from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models.project import Project
from app.db.models.user import User
from app.db.models.user_project_assignment import UserProjectAssignment
from app.db.session import get_db_session
from app.schemas.auth import AuthUser

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(current_user: AuthUser) -> AuthUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


@router.post(
    "/users/{user_id}/projects/{project_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign a user to a project (admin only)",
)
async def assign_user_to_project(
    user_id: str,
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)

    user_result = await db.execute(select(User).where(User.id == user_id))
    if user_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if project_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    existing = await db.execute(
        select(UserProjectAssignment).where(
            UserProjectAssignment.user_id == user_id,
            UserProjectAssignment.project_id == project_id,
        )
    )
    if existing.scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already assigned to this project.")

    assignment = UserProjectAssignment(user_id=user_id, project_id=project_id)
    db.add(assignment)
    await db.commit()
    return {"user_id": user_id, "project_id": project_id, "detail": "User assigned to project."}


@router.delete(
    "/users/{user_id}/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a user from a project (admin only)",
)
async def remove_user_from_project(
    user_id: str,
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> None:
    _require_admin(current_user)

    result = await db.execute(
        select(UserProjectAssignment).where(
            UserProjectAssignment.user_id == user_id,
            UserProjectAssignment.project_id == project_id,
        )
    )
    assignment = result.scalars().first()
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    await db.delete(assignment)
    await db.commit()


@router.get(
    "/users/{user_id}/projects",
    summary="List projects assigned to a user (admin only)",
)
async def list_projects_for_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    _require_admin(current_user)

    result = await db.execute(
        select(Project)
        .join(UserProjectAssignment, UserProjectAssignment.project_id == Project.id)
        .where(UserProjectAssignment.user_id == user_id)
        .order_by(Project.name.asc())
    )
    projects = result.scalars().all()
    return [{"id": p.id, "name": p.name} for p in projects]


@router.get(
    "/projects/{project_id}/users",
    summary="List users assigned to a project (admin only)",
)
async def list_users_for_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    _require_admin(current_user)

    result = await db.execute(
        select(User)
        .join(UserProjectAssignment, UserProjectAssignment.user_id == User.id)
        .where(UserProjectAssignment.project_id == project_id)
        .order_by(User.email.asc())
    )
    users = result.scalars().all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
