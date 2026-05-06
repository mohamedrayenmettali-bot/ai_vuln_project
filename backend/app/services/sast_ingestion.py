from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.finding import Finding, FindingStatus, SeverityLevel
from app.services.finding_identity import build_finding_dedupe_key


class SastIngestionTarget(str, Enum):
    DATABASE = "database"
    DEFECTDOJO = "defectdojo"
    DISABLED = "disabled"


def resolve_sast_ingestion_target(raw_target: str | None = None) -> SastIngestionTarget:
    raw = (raw_target or settings.SAST_INGESTION_TARGET or "").strip().lower()
    aliases = {
        "db": SastIngestionTarget.DATABASE,
        "database": SastIngestionTarget.DATABASE,
        "local": SastIngestionTarget.DATABASE,
        "defectdojo": SastIngestionTarget.DEFECTDOJO,
        "dojo": SastIngestionTarget.DEFECTDOJO,
        "none": SastIngestionTarget.DISABLED,
        "disabled": SastIngestionTarget.DISABLED,
    }
    if "," in raw or "+" in raw or raw in {"both", "all"}:
        raise ValueError("SAST ingestion target must be one of database, defectdojo, or disabled.")
    try:
        return aliases[raw]
    except KeyError as exc:
        raise ValueError("Unsupported SAST ingestion target.") from exc


async def ingest_sast_findings(
    db: AsyncSession,
    project_id: str,
    raw_findings: list[dict[str, Any]],
    *,
    target: str | SastIngestionTarget | None = None,
    defectdojo_submitter: Callable[[list[dict[str, Any]]], None] | None = None,
) -> dict[str, Any]:
    resolved_target = target if isinstance(target, SastIngestionTarget) else resolve_sast_ingestion_target(target)
    normalized = [_normalize_sast_finding(project_id, raw) for raw in raw_findings]

    if resolved_target == SastIngestionTarget.DISABLED:
        return {"target": resolved_target.value, "created": 0, "updated": 0, "submitted": 0}

    if resolved_target == SastIngestionTarget.DEFECTDOJO:
        if defectdojo_submitter is None:
            raise ValueError("DefectDojo SAST ingestion requires an explicit submitter.")
        defectdojo_submitter(normalized)
        return {"target": resolved_target.value, "created": 0, "updated": 0, "submitted": len(normalized)}

    created = 0
    updated = 0
    for item in normalized:
        result = await db.execute(
            select(Finding).where(
                Finding.project_id == project_id,
                Finding.dedupe_key == item["dedupe_key"],
            )
        )
        finding = result.scalars().first()
        if finding is None:
            finding = Finding(**item)
            db.add(finding)
            created += 1
        else:
            for key, value in item.items():
                setattr(finding, key, value)
            updated += 1

    await db.commit()
    return {"target": resolved_target.value, "created": created, "updated": updated, "submitted": 0}


def _normalize_sast_finding(project_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    title = str(raw.get("title") or raw.get("message") or raw.get("rule_id") or "SAST finding")
    cve_id = raw.get("cve_id") or raw.get("cve")
    scanner = str(raw.get("scanner") or raw.get("tool") or "sast")
    severity = _coerce_severity(raw.get("severity"))
    status_value = _coerce_status(raw.get("status"))
    file_path = raw.get("file_path") or raw.get("path") or raw.get("filename")
    line = raw.get("line") or raw.get("line_number") or raw.get("start_line")
    dedupe_key = str(raw.get("dedupe_key") or build_finding_dedupe_key(
        title=title,
        cve_id=str(cve_id) if cve_id else None,
        file_path=str(file_path) if file_path else None,
        line=line,
    ))
    external_id = str(raw.get("external_id") or raw.get("fingerprint") or dedupe_key[:24])

    return {
        "project_id": project_id,
        "title": title,
        "description": raw.get("description") or raw.get("message") or title,
        "severity": severity,
        "status": status_value,
        "cvss_score": _to_float(raw.get("cvss_score") or raw.get("cvss")),
        "cve_id": str(cve_id) if cve_id else None,
        "ai_risk_score": _to_float(raw.get("ai_risk_score")),
        "epss_score": _to_float(raw.get("epss_score")),
        "epss_percentile": _to_float(raw.get("epss_percentile")),
        "scanner": scanner,
        "source": f"sast:{scanner.lower()}",
        "external_id": external_id,
        "dedupe_key": dedupe_key,
        "sync_conflict": False,
    }


def _coerce_severity(raw_value: object) -> SeverityLevel:
    normalized = str(raw_value or "").strip().lower()
    mapping = {
        "critical": SeverityLevel.CRITICAL,
        "high": SeverityLevel.HIGH,
        "medium": SeverityLevel.MEDIUM,
        "low": SeverityLevel.LOW,
        "info": SeverityLevel.INFO,
    }
    return mapping.get(normalized, SeverityLevel.MEDIUM)


def _coerce_status(raw_value: object) -> FindingStatus:
    normalized = str(raw_value or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "open": FindingStatus.OPEN,
        "in_progress": FindingStatus.IN_PROGRESS,
        "accepted": FindingStatus.ACCEPTED,
        "closed": FindingStatus.MITIGATED,
        "mitigated": FindingStatus.MITIGATED,
    }
    return mapping.get(normalized, FindingStatus.OPEN)


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
