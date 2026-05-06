from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models.notification import Notification
from app.db.session import get_db_session
from app.schemas.auth import AuthUser

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize_notification(notification: Notification) -> dict[str, object]:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "time": notification.created_at.isoformat() if notification.created_at else None,
        "read": notification.read_at is not None,
        "project_id": notification.project_id,
        "finding_id": notification.finding_id,
    }


@router.get("", summary="List notifications")
async def list_notifications(
    unread_only: bool = Query(False, description="Return unread notifications only"),
    notification_type: str | None = Query(default=None, description="Filter by notification type"),
    limit: int | None = Query(default=None, ge=1, le=500, description="Maximum number of notifications"),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    if notification_type:
        query = query.where(Notification.type == notification_type.lower())

    query = query.order_by(Notification.created_at.desc()).offset(skip)
    if limit is not None:
        query = query.limit(limit)

    result = await db.execute(query)
    return [_serialize_notification(notification) for notification in result.scalars().all()]


@router.get("/unread-count", summary="Unread notification count")
async def unread_count(
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, int]:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    return {"count": int(result.scalar_one() or 0)}


@router.patch("/{notification_id}/read", summary="Mark a notification as read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalars().first()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)
    return _serialize_notification(notification)


@router.post("/mark-all-read", summary="Mark all notifications as read")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, int]:
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    notifications = result.scalars().all()
    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.read_at = now
    await db.commit()
    return {"updated": len(notifications)}


@router.get("/{notification_id}", summary="Get a notification")
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalars().first()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return _serialize_notification(notification)
