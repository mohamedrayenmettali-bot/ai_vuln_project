from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models.finding import Finding
from app.db.models.project import Project, ProjectStatus
from app.db.models.user_project_assignment import UserProjectAssignment
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.dashboard import (
    build_jira_tickets,
    build_overview,
    build_pipeline_snapshot,
    create_notification,
    get_project_or_404,
    save_project_settings,
    serialize_finding,
    serialize_project,
    sync_project_from_defectdojo,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


async def _get_accessible_project_ids(db: AsyncSession, current_user: AuthUser) -> list[str] | None:
    """Return the list of project IDs the user may access.

    Returns ``None`` for admin users (meaning: all projects are accessible).
    """
    if current_user.role == "admin":
        return None
    result = await db.execute(
        select(UserProjectAssignment.project_id).where(
            UserProjectAssignment.user_id == current_user.id
        )
    )
    return [row[0] for row in result.all()]


async def _assert_project_access(
    db: AsyncSession,
    project_id: str,
    current_user: AuthUser,
) -> None:
    """Raise 403 if the current user does not have access to *project_id*."""
    if current_user.role == "admin":
        return
    result = await db.execute(
        select(UserProjectAssignment).where(
            UserProjectAssignment.user_id == current_user.id,
            UserProjectAssignment.project_id == project_id,
        )
    )
    if result.scalars().first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project.",
        )


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 12 Tf", "72 740 Td"]
    for index, line in enumerate(lines):
        if index:
            content_lines.append("0 -16 Td")
        content_lines.append(f"({_escape_pdf_text(line)}) Tj")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length "
        + str(len(content_stream)).encode("ascii")
        + b" >> stream\n"
        + content_stream
        + b"\nendstream endobj\n",
    ]

    parts = [b"%PDF-1.4\n"]
    offsets = [0]
    current = len(parts[0])
    for obj in objects:
        offsets.append(current)
        parts.append(obj)
        current += len(obj)

    xref_offset = current
    xref_lines = ["xref\n0 6\n", "0000000000 65535 f \n"]
    xref_lines.extend(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    trailer = f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    return b"".join(parts) + "".join(xref_lines).encode("ascii") + trailer.encode("ascii")


async def _load_findings(db: AsyncSession, project_id: str) -> list[Finding]:
    result = await db.execute(
        select(Finding)
        .where(Finding.project_id == project_id)
        .order_by(Finding.created_at.asc(), Finding.id.asc())
    )
    return list(result.scalars().all())


async def _snapshot_project(db: AsyncSession, project: Project) -> dict[str, Any]:
    findings = await _load_findings(db, project.id)
    return serialize_project(project, findings)


@router.get("/", response_model=list[ProjectOut])
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    accessible_ids = await _get_accessible_project_ids(db, current_user)
    query = select(Project).order_by(Project.created_at.asc(), Project.id.asc())
    if accessible_ids is not None:
        query = query.where(Project.id.in_(accessible_ids))
    result = await db.execute(query.offset(skip).limit(limit))
    projects = result.scalars().all()
    return [await _snapshot_project(db, project) for project in projects]


@router.get("/{project_id}/overview", summary="Project overview for dashboard charts")
async def project_overview(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user)
    findings = await _load_findings(db, project_id)
    return build_overview(findings)


@router.get("/{project_id}/findings", summary="List findings for a project")
async def read_project_findings(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    await _assert_project_access(db, project_id, current_user)
    result = await db.execute(
        select(Finding)
        .where(Finding.project_id == project_id)
        .order_by(Finding.created_at.asc(), Finding.id.asc())
        .offset(skip)
        .limit(limit)
    )
    findings = result.scalars().all()
    return [serialize_finding(finding) for finding in findings]


@router.get("/{project_id}/findings/export/csv", summary="Export project findings as CSV")
async def export_project_findings_csv(
    project_id: str,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> Response:
    findings = await read_project_findings(project_id=project_id, skip=skip, limit=limit, db=db, current_user=current_user)

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "id",
            "title",
            "severity",
            "scanner",
            "cvss",
            "ai_score",
            "epss",
            "status",
            "assigned",
            "date",
            "cve_id",
        ],
    )
    writer.writeheader()
    for finding in findings:
        writer.writerow({key: finding.get(key) for key in writer.fieldnames})

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="project-{project_id}-findings.csv"'},
    )


@router.get("/{project_id}/pipeline", summary="Project pipeline snapshot")
async def project_pipeline(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)
    findings = await _load_findings(db, project_id)
    return build_pipeline_snapshot(findings, project)


@router.post("/{project_id}/scan", summary="Trigger a new project scan")
async def project_scan(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, str]:
    project = await get_project_or_404(db, project_id)
    project.status = ProjectStatus.SCANNING
    await create_notification(
        db,
        current_user.id,
        notification_type="pipeline",
        title="Security scan queued",
        message=f"A new scan was queued for {project.name}.",
        project_id=project_id,
    )
    await db.commit()
    return {
        "project_id": project_id,
        "status": "queued",
        "detail": "Security scan initiated.",
    }


@router.post("/{project_id}/sync", summary="Sync project findings")
async def project_sync(
    project_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum findings to import"),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return await sync_project_from_defectdojo(
            db,
            project_id,
            actor_user_id=current_user.id,
            limit=limit,
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


@router.get("/{project_id}/settings", summary="Project integration settings")
async def get_project_settings(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)
    from app.services.dashboard import load_project_settings

    settings_row = await load_project_settings(db, project_id)
    return {
        "project_id": project.id,
        "jira_url": settings_row.jira_url if settings_row else "",
        "project_key": settings_row.project_key if settings_row else project.name[:3].upper(),
        "api_token": "",
        "user_email": settings_row.user_email if settings_row else "",
        "default_issue_type": settings_row.default_issue_type if settings_row else "Bug",
        "auto_critical": settings_row.auto_critical if settings_row else True,
        "auto_high_ai": settings_row.auto_high_ai if settings_row else True,
        "configured": settings_row is not None,
    }


@router.put("/{project_id}/settings", summary="Update project integration settings")
async def update_project_settings(
    project_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    project = await get_project_or_404(db, project_id)
    settings_row = await save_project_settings(db, project_id, payload)
    await create_notification(
        db,
        current_user.id,
        notification_type="system",
        title="Project settings updated",
        message=f"Integration settings were updated for {project.name}.",
        project_id=project_id,
    )
    await db.commit()
    return {
        "project_id": project_id,
        "jira_url": settings_row.jira_url,
        "project_key": settings_row.project_key,
        "api_token": "",
        "user_email": settings_row.user_email,
        "default_issue_type": settings_row.default_issue_type,
        "auto_critical": settings_row.auto_critical,
        "auto_high_ai": settings_row.auto_high_ai,
        "configured": True,
    }


@router.get("/{project_id}/jira-tickets", summary="List Jira tickets for a project")
async def get_project_jira_tickets(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)
    findings = await _load_findings(db, project_id)
    from app.services.dashboard import load_project_settings

    settings_row = await load_project_settings(db, project_id)
    project_key = settings_row.project_key if settings_row and settings_row.project_key else project.name[:3].upper()
    return build_jira_tickets(findings, project_key=project_key)


@router.get("/{project_id}/export/pdf", summary="Export project report as PDF")
async def export_project_pdf(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> Response:
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)
    findings = await _load_findings(db, project_id)
    overview = build_overview(findings)
    pdf_bytes = _build_pdf(
        [
            f"Project: {project.name}",
            f"Total findings: {overview['total']}",
            f"Critical: {overview['critical']}",
            f"High: {overview['high']}",
            f"Medium: {overview['medium']}",
            f"Low: {overview['low']}",
        ]
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="project-{project_id}.pdf"'},
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def read_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)
    findings = await _load_findings(db, project_id)
    return serialize_project(project, findings)


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.flush()
    # Non-admin creators are automatically assigned to the project they create.
    if current_user.role != "admin":
        assignment = UserProjectAssignment(user_id=current_user.id, project_id=db_project.id)
        db.add(assignment)
    await db.commit()
    await db.refresh(db_project)
    return serialize_project(db_project, [])


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)

    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    findings = await _load_findings(db, project_id)
    return serialize_project(project, findings)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user)
    project = await get_project_or_404(db, project_id)

    await db.delete(project)
    await db.commit()
    return None
