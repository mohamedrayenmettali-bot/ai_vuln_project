from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from app.db.models.finding import Finding
from app.db.session import get_sessionmaker
from app.schemas.base import PredictionInput
from app.services.predictor import PredictorService
from app.services.sast_ingestion import ingest_sast_findings, resolve_sast_ingestion_target
from backend.tests.support import create_project


def test_populate_epss_skips_blank_and_whitespace_cve_ids(monkeypatch):
    called = False

    def fake_fetch(_: list[str]) -> dict[str, dict[str, float]]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr("app.services.predictor.fetch_epss_scores", fake_fetch)

    inputs = [
        PredictionInput(description="Hardcoded secret", cve_id="   ", cwe_id="CWE-259"),
        PredictionInput(description="No CVE at all", cve_id=None, cwe_id="CWE-89"),
    ]

    hydrated = PredictorService._populate_epss(inputs)

    assert called is False
    assert hydrated[0].epss_score is None
    assert hydrated[0].epss_percentile is None
    assert hydrated[1].epss_score is None
    assert hydrated[1].epss_percentile is None


def test_populate_epss_hydrates_missing_scores(monkeypatch):
    monkeypatch.setattr(
        "app.services.predictor.fetch_epss_scores",
        lambda ids: {"CVE-2024-0001": {"epss": 0.42, "percentile": 0.81}},
    )

    hydrated = PredictorService._populate_epss(
        [
            PredictionInput(description="Buffer overflow", cve_id="cve-2024-0001", cwe_id="CWE-121"),
        ]
    )

    assert hydrated[0].epss_score == pytest.approx(0.42)
    assert hydrated[0].epss_percentile == pytest.approx(0.81)


def test_sast_ingestion_rejects_combined_targets():
    with pytest.raises(ValueError):
        resolve_sast_ingestion_target("database,defectdojo")


def test_sast_database_ingestion_upserts_by_dedupe_key(app_environment):
    project = asyncio.run(create_project(name="SAST Project"))
    raw = [
        {
            "scanner": "Semgrep",
            "rule_id": "python.sql-injection",
            "title": "SQL injection",
            "description": "Untrusted SQL string concatenation",
            "severity": "High",
            "path": "app/users.py",
            "line": 42,
        }
    ]

    async def run_ingestion():
        async with get_sessionmaker()() as db:
            first = await ingest_sast_findings(db, project.id, raw, target="database")
        raw[0]["description"] = "Untrusted SQL string concatenation in login"
        async with get_sessionmaker()() as db:
            second = await ingest_sast_findings(db, project.id, raw, target="database")
        async with get_sessionmaker()() as db:
            result = await db.execute(select(Finding).where(Finding.project_id == project.id))
            findings = list(result.scalars().all())
        return first, second, findings

    first, second, findings = asyncio.run(run_ingestion())

    assert first["created"] == 1
    assert second["updated"] == 1
    assert len(findings) == 1
    assert findings[0].description == "Untrusted SQL string concatenation in login"


def test_sast_defectdojo_target_does_not_write_database(app_environment):
    project = asyncio.run(create_project(name="Dojo-only SAST Project"))
    submitted: list[dict] = []

    async def run_ingestion():
        async with get_sessionmaker()() as db:
            result = await ingest_sast_findings(
                db,
                project.id,
                [{"scanner": "Semgrep", "title": "Hardcoded secret", "path": "settings.py", "line": 7}],
                target="defectdojo",
                defectdojo_submitter=submitted.extend,
            )
        async with get_sessionmaker()() as db:
            rows = await db.execute(select(Finding).where(Finding.project_id == project.id))
            findings = list(rows.scalars().all())
        return result, findings

    result, findings = asyncio.run(run_ingestion())

    assert result["submitted"] == 1
    assert len(submitted) == 1
    assert findings == []
