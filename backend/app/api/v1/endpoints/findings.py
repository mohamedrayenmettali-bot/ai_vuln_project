from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models.finding import Finding
from app.db.models.finding_event import FindingEvent
from app.db.models.user_project_assignment import UserProjectAssignment
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.finding import FindingCreate, FindingUpdate, FindingOut
from app.services.dashboard import (
    build_ai_analysis,
    build_finding_history,
    create_notification,
    record_finding_event,
    serialize_finding,
    severity_slug,
    status_slug,
)
from app.services.finding_identity import build_finding_dedupe_key
from app.db.models.finding import FindingStatus, SeverityLevel

router = APIRouter(prefix="/findings", tags=["Findings"])


class FindingStatusPatch(BaseModel):
    status: str = Field(min_length=1)


class FindingAssignPatch(BaseModel):
    user_id: str = Field(min_length=1)


class FindingFeedbackPayload(BaseModel):
    vote: str | None = None
    comment: str | None = None


def _coerce_status(raw_status: str) -> FindingStatus:
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


def _coerce_severity(raw_severity: SeverityLevel | str) -> SeverityLevel:
    if isinstance(raw_severity, SeverityLevel):
        return raw_severity

    normalized = str(raw_severity).strip().lower()
    mapping = {
        "critical": SeverityLevel.CRITICAL,
        "high": SeverityLevel.HIGH,
        "medium": SeverityLevel.MEDIUM,
        "low": SeverityLevel.LOW,
        "info": SeverityLevel.INFO,
    }
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Unsupported severity value.") from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_automated_source(source: str | None) -> bool:
    normalized = str(source or "").strip().lower()
    return normalized == "defectdojo" or normalized == "sast" or normalized.startswith("sast:")


def _ensure_dedupe_key(data: dict[str, Any]) -> None:
    if data.get("dedupe_key"):
        return
    source = data.get("source")
    if not _is_automated_source(source):
        return
    title = data.get("title")
    if not title:
        return
    data["dedupe_key"] = build_finding_dedupe_key(
        title=str(title),
        cve_id=data.get("cve_id"),
    )


def _mark_local_update(finding: Finding, timestamp: datetime) -> None:
    finding.updated_at = timestamp
    finding.local_updated_at = timestamp


async def _load_finding(db: AsyncSession, finding_id: str) -> Finding:
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalars().first()
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


async def _load_finding_events(db: AsyncSession, finding_id: str) -> list[FindingEvent]:
    result = await db.execute(
        select(FindingEvent).where(FindingEvent.finding_id == finding_id).order_by(FindingEvent.created_at.asc())
    )
    return list(result.scalars().all())


@router.get("/")
async def read_findings(
    project_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    query = select(Finding)
    if project_id:
        # Enforce single-project access.
        if current_user.role != "admin":
            access = await db.execute(
                select(UserProjectAssignment).where(
                    UserProjectAssignment.user_id == current_user.id,
                    UserProjectAssignment.project_id == project_id,
                )
            )
            if access.scalars().first() is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this project.",
                )
        query = query.where(Finding.project_id == project_id)
    elif current_user.role != "admin":
        # Limit to only findings in the user's assigned projects.
        assigned = await db.execute(
            select(UserProjectAssignment.project_id).where(
                UserProjectAssignment.user_id == current_user.id
            )
        )
        accessible_ids = [row[0] for row in assigned.all()]
        query = query.where(Finding.project_id.in_(accessible_ids))

    query = query.order_by(Finding.created_at.asc(), Finding.id.asc()).offset(skip).limit(limit)

    result = await db.execute(query)
    findings = result.scalars().all()
    return [serialize_finding(finding) for finding in findings]


@router.get("/{finding_id}")
async def read_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    finding = await _load_finding(db, finding_id)
    if current_user.role != "admin":
        access = await db.execute(
            select(UserProjectAssignment).where(
                UserProjectAssignment.user_id == current_user.id,
                UserProjectAssignment.project_id == finding.project_id,
            )
        )
        if access.scalars().first() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project.",
            )
    return serialize_finding(finding)


@router.patch("/{finding_id}/status", summary="Update a finding status")
async def update_finding_status(
    finding_id: str,
    payload: FindingStatusPatch,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    finding = await _load_finding(db, finding_id)
    previous_status = status_slug(finding.status)
    finding.status = _coerce_status(payload.status)
    _mark_local_update(finding, _now())
    await record_finding_event(
        db,
        finding.id,
        event_type="status",
        title=f"Status changed to {status_slug(finding.status).replace('_', ' ').title()}",
        message=f"Status changed from {previous_status} to {status_slug(finding.status)}.",
        payload={"from": previous_status, "to": status_slug(finding.status)},
        actor_user_id=current_user.id,
    )
    await create_notification(
        db,
        current_user.id,
        notification_type="finding",
        title="Finding status updated",
        message=f"{finding.title} moved from {previous_status} to {status_slug(finding.status)}.",
        project_id=finding.project_id,
        finding_id=finding.id,
    )
    await db.commit()
    await db.refresh(finding)
    return serialize_finding(finding)


@router.patch("/{finding_id}/assign", summary="Assign a finding")
async def assign_finding(
    finding_id: str,
    payload: FindingAssignPatch,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    finding = await _load_finding(db, finding_id)
    previous_assignee = finding.assigned_to
    finding.assigned_to = payload.user_id.strip()
    _mark_local_update(finding, _now())
    await record_finding_event(
        db,
        finding.id,
        event_type="assignment",
        title=f"Assigned to {finding.assigned_to}",
        message=f"Assigned from {previous_assignee or 'Unassigned'} to {finding.assigned_to}.",
        payload={"from": previous_assignee, "to": finding.assigned_to},
        actor_user_id=current_user.id,
    )
    await create_notification(
        db,
        current_user.id,
        notification_type="finding",
        title="Finding assigned",
        message=f"{finding.title} assigned to {finding.assigned_to}.",
        project_id=finding.project_id,
        finding_id=finding.id,
    )
    await db.commit()
    await db.refresh(finding)
    return serialize_finding(finding)


@router.post("/{finding_id}/feedback", summary="Store AI prioritization feedback")
async def submit_finding_feedback(
    finding_id: str,
    payload: FindingFeedbackPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    finding = await _load_finding(db, finding_id)
    feedback_entry = {
        "vote": payload.vote,
        "comment": payload.comment,
        "time": datetime.now(timezone.utc).isoformat(),
        "actor_user_id": current_user.id,
    }
    await record_finding_event(
        db,
        finding.id,
        event_type="feedback",
        title="AI prioritization feedback submitted",
        message=payload.comment or "Feedback recorded.",
        payload=feedback_entry,
        actor_user_id=current_user.id,
    )
    await db.commit()
    return {
        "detail": "Feedback recorded",
        "finding_id": finding_id,
        "finding": serialize_finding(finding),
        "feedback": feedback_entry,
    }


@router.get("/{finding_id}/history", summary="Return a finding history timeline")
async def get_finding_history(
    finding_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
    finding = await _load_finding(db, finding_id)
    events = await _load_finding_events(db, finding_id)
    return build_finding_history(finding, events)


@router.get("/{finding_id}/ai-analysis", summary="Return AI analysis for a finding")
async def get_finding_ai_analysis(
    finding_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    finding = await _load_finding(db, finding_id)
    return build_ai_analysis(finding)


@router.post("/", response_model=FindingOut, status_code=status.HTTP_201_CREATED)
async def create_finding(
    finding: FindingCreate,
    db: AsyncSession = Depends(get_db_session),
):
    data = finding.model_dump()
    _ensure_dedupe_key(data)

    db_finding = None
    if _is_automated_source(data.get("source")) and data.get("dedupe_key"):
        result = await db.execute(
            select(Finding).where(
                Finding.project_id == data["project_id"],
                Finding.dedupe_key == data["dedupe_key"],
            )
        )
        db_finding = result.scalars().first()

    timestamp = _now()
    if db_finding is None:
        if not _is_automated_source(data.get("source")):
            data["local_updated_at"] = timestamp
        db_finding = Finding(**data)
    else:
        for key, value in data.items():
            setattr(db_finding, key, value)
        db_finding.updated_at = timestamp

    db.add(db_finding)
    await db.commit()
    await db.refresh(db_finding)
    return db_finding


@router.put("/{finding_id}", response_model=FindingOut)
async def update_finding(
    finding_id: str,
    finding_update: FindingUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_finding = await _load_finding(db, finding_id)

    update_data = finding_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status" and isinstance(value, str):
            setattr(db_finding, key, _coerce_status(value))
        elif key == "severity":
            setattr(db_finding, key, _coerce_severity(value))
        else:
            setattr(db_finding, key, value)

    if _is_automated_source(db_finding.source) and (
        not db_finding.dedupe_key or "title" in update_data or "cve_id" in update_data
    ):
        db_finding.dedupe_key = build_finding_dedupe_key(
            title=db_finding.title,
            cve_id=db_finding.cve_id,
        )
    _mark_local_update(db_finding, _now())
    await db.commit()
    await db.refresh(db_finding)
    return db_finding


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(finding_id: str, db: AsyncSession = Depends(get_db_session)):
    db_finding = await _load_finding(db, finding_id)

    await db.delete(db_finding)
    await db.commit()
    return None
