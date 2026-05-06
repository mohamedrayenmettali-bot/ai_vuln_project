from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from collections import Counter
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding, FindingStatus, SeverityLevel
from app.db.models.finding_event import FindingEvent
from app.db.models.notification import Notification
from app.db.models.project import Project, ProjectStatus
from app.db.models.project_setting import ProjectIntegrationSetting
from app.services.defectdojo import defectdojo_service, extract_cve_ids
from app.services.finding_identity import build_finding_dedupe_key, hash_external_payload, parse_external_updated_at
from app.services.predictor import PredictorService
from app.schemas.base import PredictionInput
from ai.config import SeverityLevel as AISSeverityLevel


def severity_slug(value: SeverityLevel | str | None) -> str:
    raw = str(getattr(value, "value", value) or "").strip().lower()
    return raw


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def status_slug(value: FindingStatus | str | None) -> str:
    raw = str(getattr(value, "value", value) or "").strip().lower()
    mapping = {
        "open": "open",
        "in progress": "in_progress",
        "in_progress": "in_progress",
        "accepted": "accepted",
        "mitigated": "closed",
        "closed": "closed",
    }
    return mapping.get(raw, raw.replace(" ", "_"))


def _coerce_finding_status(raw_status: str) -> FindingStatus:
    normalized = raw_status.strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "open": FindingStatus.OPEN,
        "in_progress": FindingStatus.IN_PROGRESS,
        "inprogress": FindingStatus.IN_PROGRESS,
        "accepted": FindingStatus.ACCEPTED,
        "closed": FindingStatus.MITIGATED,
        "mitigated": FindingStatus.MITIGATED,
    }
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Unsupported finding status.") from exc


def _coerce_severity(raw_value: str | SeverityLevel | None) -> SeverityLevel:
    normalized = severity_slug(raw_value)
    mapping = {
        "critical": SeverityLevel.CRITICAL,
        "high": SeverityLevel.HIGH,
        "medium": SeverityLevel.MEDIUM,
        "low": SeverityLevel.LOW,
        "info": SeverityLevel.INFO,
    }
    return mapping.get(normalized, SeverityLevel.MEDIUM)


def _ai_severity_from_db(value: SeverityLevel | str | None) -> AISSeverityLevel:
    mapping = {
        "critical": AISSeverityLevel.CRITICAL,
        "high": AISSeverityLevel.HIGH,
        "medium": AISSeverityLevel.MEDIUM,
        "low": AISSeverityLevel.LOW,
        "info": AISSeverityLevel.INFO,
    }
    return mapping.get(severity_slug(value), AISSeverityLevel.MEDIUM)


def serialize_finding(finding: Finding) -> dict[str, Any]:
    created_at = finding.created_at.isoformat() if finding.created_at else None
    updated_at = finding.updated_at.isoformat() if finding.updated_at else created_at
    return {
        "id": finding.id,
        "project_id": finding.project_id,
        "title": finding.title,
        "description": finding.description,
        "severity": severity_slug(finding.severity),
        "status": status_slug(finding.status),
        "scanner": finding.scanner or "Unknown",
        "cvss": float(getattr(finding, "cvss_score", 0.0) or 0.0),
        "ai_score": float(getattr(finding, "ai_risk_score", 0.0) or 0.0),
        "epss": float(getattr(finding, "epss_score", 0.0) or 0.0),
        "epss_percentile": float(getattr(finding, "epss_percentile", 0.0) or 0.0),
        "assigned": finding.assigned_to,
        "date": created_at,
        "updated_at": updated_at,
        "source": finding.source,
        "external_id": finding.external_id,
        "dedupe_key": finding.dedupe_key,
        "external_updated_at": finding.external_updated_at.isoformat() if finding.external_updated_at else None,
        "last_synced_at": finding.last_synced_at.isoformat() if finding.last_synced_at else None,
        "local_updated_at": finding.local_updated_at.isoformat() if finding.local_updated_at else None,
        "sync_conflict": bool(finding.sync_conflict),
        "cve_id": finding.cve_id,
    }


def build_finding_history(finding: Finding, events: list[FindingEvent]) -> list[dict[str, Any]]:
    created_at = finding.created_at.isoformat() if finding.created_at else None
    updated_at = finding.updated_at.isoformat() if finding.updated_at else created_at
    history = [
        {
            "type": "created",
            "label": f"Finding detected for project {finding.project_id}",
            "time": created_at,
        }
    ]

    for event in events:
        payload = event.payload or {}
        history.append(
            {
                "type": event.event_type,
                "label": event.title,
                "time": event.created_at.isoformat() if event.created_at else updated_at,
                "message": event.message,
                "payload": payload,
            }
        )

    if finding.updated_at:
        history.append(
            {
                "type": "status",
                "label": f"Current status: {status_slug(finding.status).replace('_', ' ').title()}",
                "time": updated_at,
            }
        )

    return [item for item in history if item.get("time")]


def build_ai_analysis(finding: Finding) -> dict[str, Any]:
    ai_score = float(getattr(finding, "ai_risk_score", 0.0) or 0.0)
    cvss = float(getattr(finding, "cvss_score", 0.0) or 0.0)
    epss = float(getattr(finding, "epss_score", 0.0) or 0.0)
    severity = severity_slug(finding.severity)
    risk_band = "high" if ai_score >= 7 else "medium" if ai_score >= 4 else "low"
    status_value = status_slug(finding.status)

    return {
        "finding_id": finding.id,
        "risk_score": round(ai_score, 2),
        "severity": severity,
        "risk_band": risk_band,
        "confidence": round(min(0.98, max(0.55, 0.58 + ai_score / 20)), 2),
        "summary": (
            f"This finding is considered {risk_band} risk because its severity is {severity} "
            f"and the AI score is {ai_score:.1f}."
        ),
        "signals": [
            {"label": "CVSS Score", "value": cvss, "weight": round(min(1.0, cvss / 10), 2)},
            {"label": "EPSS Score", "value": epss, "weight": round(min(1.0, epss), 2)},
            {"label": "AI Risk Score", "value": ai_score, "weight": round(min(1.0, ai_score / 10), 2)},
            {"label": "Status", "value": status_value, "weight": 0.5 if status_value == "open" else 0.3},
        ],
        "recommendations": [
            "Validate the affected code path and confirm the fix with a regression test.",
            "Update the ticket status once remediation is deployed and verified.",
        ],
    }


def build_overview(findings: list[Finding]) -> dict[str, Any]:
    severity_totals = {key: 0 for key in ("critical", "high", "medium", "low")}
    by_scanner: Counter[str] = Counter()
    ai_score_distribution = [
        {"range": "0-2", "count": 0},
        {"range": "2-4", "count": 0},
        {"range": "4-6", "count": 0},
        {"range": "6-8", "count": 0},
        {"range": "8-10", "count": 0},
    ]
    recent_critical: list[dict[str, Any]] = []
    findings_over_time: dict[str, dict[str, int]] = {}

    for finding in findings:
        sev = severity_slug(finding.severity)
        if sev in severity_totals:
            severity_totals[sev] += 1

        scanner_name = finding.scanner or "Unknown"
        by_scanner[scanner_name] += 1

        ai_score = float(getattr(finding, "ai_risk_score", 0.0) or 0.0)
        if ai_score < 2:
            ai_score_distribution[0]["count"] += 1
        elif ai_score < 4:
            ai_score_distribution[1]["count"] += 1
        elif ai_score < 6:
            ai_score_distribution[2]["count"] += 1
        elif ai_score < 8:
            ai_score_distribution[3]["count"] += 1
        else:
            ai_score_distribution[4]["count"] += 1

        created_date = finding.created_at.date().isoformat() if finding.created_at else None
        if created_date:
            bucket = findings_over_time.setdefault(
                created_date,
                {"date": created_date, "critical": 0, "high": 0, "medium": 0, "low": 0},
            )
            if sev in bucket:
                bucket[sev] += 1

        if sev == "critical":
            recent_critical.append(
                {
                    "id": finding.id,
                    "title": finding.title,
                    "severity": "critical",
                    "scanner": scanner_name,
                    "ai_score": ai_score,
                    "date": finding.created_at.isoformat() if finding.created_at else None,
                }
            )

    total = sum(severity_totals.values())
    recent_critical = sorted(recent_critical, key=lambda item: item["date"] or "", reverse=True)[:5]
    findings_over_time_list = [findings_over_time[key] for key in sorted(findings_over_time.keys())]

    return {
        "total": total,
        **severity_totals,
        "findings_over_time": findings_over_time_list,
        "by_scanner": [{"scanner": scanner, "count": count} for scanner, count in by_scanner.most_common()],
        "ai_score_distribution": ai_score_distribution,
        "recent_critical": recent_critical,
    }


def serialize_project(project: Project, findings: list[Finding]) -> dict[str, Any]:
    overview = build_overview(findings)
    last_scan = max((finding.created_at for finding in findings if finding.created_at), default=None)
    pipeline_status = "running" if project.status == ProjectStatus.SCANNING else ("failed" if overview["critical"] or overview["high"] else "passed")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value if getattr(project.status, "value", None) else str(project.status),
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "last_scan": last_scan,
        "pipeline_status": pipeline_status,
        "tech_stack": [],
        "findings_summary": {
            "critical": overview["critical"],
            "high": overview["high"],
            "medium": overview["medium"],
            "low": overview["low"],
        },
    }


def build_pipeline_snapshot(findings: list[Finding], project: Project) -> dict[str, Any]:
    summary = build_overview(findings)
    scanner_counts = summary["by_scanner"]
    total_findings = summary["total"]
    failed = summary["critical"] + summary["high"] > 0
    if project.status == ProjectStatus.SCANNING:
        status_value = "running"
    else:
        status_value = "failed" if failed else "passed"

    scanners = [
        {"name": "SonarQube", "status": status_value, "findings": summary["critical"] + summary["high"], "duration": "0m 0s"},
        {"name": "OWASP ZAP", "status": status_value, "findings": summary["high"], "duration": "0m 0s"},
        {"name": "Trivy", "status": "passed" if summary["critical"] == 0 else "failed", "findings": summary["medium"], "duration": "0m 0s"},
        {"name": "Semgrep", "status": "passed", "findings": summary["low"], "duration": "0m 0s"},
    ]

    latest_created = max((finding.created_at for finding in findings if finding.created_at), default=None)
    return {
        "summary": {
            "sast": {"status": status_value, "new_findings": summary["critical"] + summary["high"], "total": total_findings},
            "dast": {"status": status_value, "new_findings": summary["high"], "total": total_findings},
            "sca": {"status": "passed" if summary["critical"] == 0 else "failed", "new_findings": summary["medium"], "total": total_findings},
            "secrets": {"status": "passed", "new_findings": 0, "total": total_findings},
        },
        "runs": [
            {
                "id": "latest",
                "run_number": 1,
                "triggered_by": "System",
                "branch": "main",
                "status": status_value,
                "duration": "0m 0s",
                "date": latest_created.isoformat() if latest_created else None,
                "scanners": scanners,
            }
        ],
        "scanner_counts": scanner_counts,
        "project_status": project.status.value if getattr(project.status, "value", None) else str(project.status),
    }


def build_jira_tickets(findings: list[Finding], project_key: str = "SEC") -> list[dict[str, Any]]:
    priority_map = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    tickets: list[dict[str, Any]] = []
    for index, finding in enumerate(findings, start=1):
        severity = severity_slug(finding.severity)
        created_at = finding.created_at.isoformat() if finding.created_at else None
        updated_at = finding.updated_at.isoformat() if finding.updated_at else created_at
        tickets.append(
            {
                "id": f"{project_key.upper()}-{index:03d}",
                "summary": finding.title,
                "finding": finding.id,
                "priority": priority_map.get(severity, "Medium"),
                "status": "Open" if status_slug(finding.status) == "open" else "In Progress",
                "assignee": finding.assigned_to or "Unassigned",
                "created": created_at,
                "last_sync": updated_at,
            }
        )
    return tickets


async def create_notification(
    db: AsyncSession,
    user_id: str,
    *,
    notification_type: str,
    title: str,
    message: str,
    project_id: str | None = None,
    finding_id: str | None = None,
) -> Notification:
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        project_id=project_id,
        finding_id=finding_id,
        created_at=_utc_now(),
    )
    db.add(notification)
    return notification


async def record_finding_event(
    db: AsyncSession,
    finding_id: str,
    *,
    event_type: str,
    title: str,
    message: str,
    payload: dict[str, Any] | None = None,
    actor_user_id: str | None = None,
) -> FindingEvent:
    event = FindingEvent(
        id=str(uuid.uuid4()),
        finding_id=finding_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        message=message,
        payload=payload or {},
        created_at=_utc_now(),
    )
    db.add(event)
    return event


async def load_project_settings(db: AsyncSession, project_id: str) -> ProjectIntegrationSetting | None:
    result = await db.execute(select(ProjectIntegrationSetting).where(ProjectIntegrationSetting.project_id == project_id))
    return result.scalars().first()


async def save_project_settings(
    db: AsyncSession,
    project_id: str,
    payload: dict[str, Any],
) -> ProjectIntegrationSetting:
    settings_row = await load_project_settings(db, project_id)
    if settings_row is None:
        settings_row = ProjectIntegrationSetting(project_id=project_id)
        db.add(settings_row)

    for field in ("jira_url", "project_key", "api_token", "user_email", "default_issue_type", "auto_critical", "auto_high_ai"):
        if field in payload:
            setattr(settings_row, field, payload[field])
    await db.flush()
    return settings_row


async def get_project_or_404(db: AsyncSession, project_id: str) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _score_finding(
    predictor: PredictorService,
    title: str,
    description: str | None,
    cve_id: str | None,
    severity: SeverityLevel,
) -> tuple[float, float, float]:
    input_payload = PredictionInput(
        description=description or title,
        cve_id=cve_id,
        severity=_ai_severity_from_db(severity),
    )
    result = predictor.predict_single(input_payload)
    return result.risk_score, float(result.epss_score or 0.0), float(result.epss_percentile or 0.0)


async def sync_project_from_defectdojo(
    db: AsyncSession,
    project_id: str,
    *,
    actor_user_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    project = await get_project_or_404(db, project_id)
    raw_findings = await asyncio.to_thread(defectdojo_service.fetch_findings, limit)
    enriched_findings = await asyncio.to_thread(defectdojo_service.enrich_findings, raw_findings, True)
    predictor = PredictorService.get()
    sync_started_at = _utc_now()

    created = 0
    updated = 0
    deduplicated = 0
    conflicts = 0
    imported_critical = 0

    for raw in enriched_findings:
        external_id = str(raw.get("id") or raw.get("unique_id_from_tool") or raw.get("title") or uuid.uuid4())
        title = str(raw.get("title") or raw.get("vulnerability_id") or external_id)
        description = str(raw.get("description") or raw.get("severity") or title)
        cve_ids = extract_cve_ids(raw)
        cve_id = cve_ids[0] if cve_ids else None
        severity = _coerce_severity(str(raw.get("severity") or raw.get("criticality") or "medium"))
        scanner = str(
            raw.get("scanner")
            or raw.get("test_type")
            or raw.get("test")
            or raw.get("engagement")
            or "DefectDojo"
        )
        cvss_score = raw.get("cvss_score") or raw.get("cvssv3_score") or raw.get("cvssv2_score") or raw.get("cvss")
        epss_score = float(raw.get("_epss_score") or raw.get("epss_score") or 0.0)
        epss_percentile = float(raw.get("_epss_percentile") or raw.get("epss_percentile") or 0.0)
        status_value = FindingStatus.OPEN if raw.get("active", True) else FindingStatus.MITIGATED
        dedupe_key = build_finding_dedupe_key(
            title=title,
            cve_id=cve_id,
            file_path=raw.get("file_path") or raw.get("file") or raw.get("path"),
            line=raw.get("line") or raw.get("line_number"),
            component=raw.get("_component_name") or raw.get("component_name"),
        )
        external_updated_at = parse_external_updated_at(raw)

        result = await db.execute(
            select(Finding).where(
                Finding.project_id == project_id,
                Finding.source == "defectdojo",
                Finding.external_id == external_id,
            )
        )
        finding = result.scalars().first()
        if finding is None:
            result = await db.execute(
                select(Finding).where(
                    Finding.project_id == project_id,
                    Finding.dedupe_key == dedupe_key,
                )
            )
            finding = result.scalars().first()
            if finding is not None:
                deduplicated += 1

        ai_score, scored_epss, scored_percentile = _score_finding(
            predictor,
            title,
            description,
            cve_id,
            severity,
        )
        epss_score = epss_score or scored_epss
        epss_percentile = epss_percentile or scored_percentile
        external_payload = {
            "title": title,
            "description": description,
            "severity": severity.value,
            "status": status_value.value,
            "cvss_score": float(cvss_score or 0.0),
            "cve_id": cve_id,
            "ai_risk_score": ai_score,
            "epss_score": epss_score,
            "epss_percentile": epss_percentile,
            "scanner": scanner,
        }
        external_payload_hash = hash_external_payload(external_payload)

        if finding is None:
            finding = Finding(
                id=str(uuid.uuid4()),
                project_id=project_id,
                title=title,
                description=description,
                severity=severity,
                status=status_value,
                cvss_score=float(cvss_score or 0.0),
                cve_id=cve_id,
                ai_risk_score=ai_score,
                epss_score=epss_score,
                epss_percentile=epss_percentile,
                scanner=scanner,
                source="defectdojo",
                external_id=external_id,
                dedupe_key=dedupe_key,
                external_updated_at=external_updated_at,
                external_payload_hash=external_payload_hash,
                last_synced_at=sync_started_at,
                sync_conflict=False,
                updated_at=sync_started_at,
            )
            db.add(finding)
            created += 1
        else:
            local_updated_at = _as_utc(finding.local_updated_at)
            last_synced_at = _as_utc(finding.last_synced_at)
            local_changed = bool(local_updated_at and (last_synced_at is None or local_updated_at > last_synced_at))
            external_changed = finding.external_payload_hash != external_payload_hash
            had_conflict = local_changed and external_changed
            previous_status = finding.status

            finding.title = title
            finding.description = description
            finding.severity = severity
            if not had_conflict or status_slug(previous_status) == status_slug(status_value):
                finding.status = status_value
            finding.cvss_score = float(cvss_score or 0.0)
            finding.cve_id = cve_id
            finding.ai_risk_score = ai_score
            finding.epss_score = epss_score
            finding.epss_percentile = epss_percentile
            finding.scanner = scanner
            finding.source = "defectdojo"
            finding.external_id = external_id
            finding.dedupe_key = dedupe_key
            finding.external_updated_at = external_updated_at
            finding.external_payload_hash = external_payload_hash
            finding.last_synced_at = sync_started_at
            finding.updated_at = sync_started_at
            finding.sync_conflict = had_conflict
            if not had_conflict:
                finding.local_updated_at = None
            updated += 1

            if had_conflict:
                conflicts += 1
                await record_finding_event(
                    db,
                    finding.id,
                    event_type="sync_conflict",
                    title="DefectDojo sync conflict resolved",
                    message=(
                        "DefectDojo metadata was refreshed while local workflow edits were preserved. "
                        "Review this finding if the local status should follow DefectDojo."
                    ),
                    payload={
                        "strategy": "defectdojo_metadata_wins_dashboard_workflow_wins",
                        "local_status": status_slug(previous_status),
                        "defectdojo_status": status_slug(status_value),
                        "external_updated_at": external_updated_at.isoformat() if external_updated_at else None,
                    },
                    actor_user_id=actor_user_id,
                )

        if severity == SeverityLevel.CRITICAL:
            imported_critical += 1

    project.status = ProjectStatus.ACTIVE
    await db.flush()
    await db.commit()

    if actor_user_id:
        await create_notification(
            db,
            actor_user_id,
            notification_type="pipeline",
            title="Finding sync completed",
            message=(
                f"Imported {created} findings, updated {updated}, merged {deduplicated} duplicates, "
                f"and resolved {conflicts} sync conflicts for project {project.name}."
            ),
            project_id=project_id,
        )
        await db.commit()

    return {
        "project_id": project_id,
        "project_name": project.name,
        "created": created,
        "updated": updated,
        "deduplicated": deduplicated,
        "conflicts": conflicts,
        "imported_critical": imported_critical,
        "total_imported": created + updated,
    }
