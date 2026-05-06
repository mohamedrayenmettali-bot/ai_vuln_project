from __future__ import annotations

import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db_session, get_sessionmaker
from app.db.models.auth_session import AuthSession
from app.db.models.notification import Notification
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.user import User
from app.core.security import get_password_hash, verify_password
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse, AuthUser, PasswordResetRequest
from app.services.email import (
    EmailConfigurationError,
    EmailDeliveryError,
    build_password_reset_url,
    is_password_reset_email_configured,
    send_password_reset_email,
)

logger = structlog.get_logger(__name__)
security = HTTPBearer()

ALLOWED_ROLES = {
    "admin",
    "security_analyst",
    "devops_engineer",
    "scrum_master",
    "developer",
}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_role(role: str) -> str:
    return role.strip().lower()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_public_user(user: User) -> AuthUser:
    return AuthUser(id=user.id, name=user.name, email=user.email, role=user.role)


async def _create_notification(
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


async def _background_sync_for_user(user_id: str, user_role: str) -> None:
    """Run DefectDojo sync in the background after login.

    Creates a fresh DB session so it is fully independent of the request
    session that has already been committed and returned to the caller.
    """
    # Deferred imports to avoid circular dependencies.
    from app.db.models.project import Project
    from app.db.models.user_project_assignment import UserProjectAssignment
    from app.services.dashboard import create_notification, sync_project_from_defectdojo

    try:
        async with get_sessionmaker()() as db:
            # Notify user that sync has started.
            await create_notification(
                db,
                user_id,
                notification_type="sync",
                title="DefectDojo sync started",
                message="Synchronising projects from DefectDojo in the background.",
            )
            await db.commit()

            # Determine which projects this user can access.
            if user_role == "admin":
                result = await db.execute(select(Project))
            else:
                result = await db.execute(
                    select(Project)
                    .join(UserProjectAssignment, UserProjectAssignment.project_id == Project.id)
                    .where(UserProjectAssignment.user_id == user_id)
                )
            projects = result.scalars().all()

            synced = 0
            for project in projects:
                try:
                    await sync_project_from_defectdojo(db, project.id, actor_user_id=user_id)
                    synced += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning("background_sync_project_failed", project_id=project.id, error=str(exc))

            project_word = "project" if synced == 1 else "projects"
            await create_notification(
                db,
                user_id,
                notification_type="sync",
                title="DefectDojo sync completed",
                message=f"Synchronisation complete. {synced} {project_word} updated.",
            )
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("background_sync_failed", user_id=user_id, error=str(exc))


async def register_user(db: AsyncSession, payload: AuthRegisterRequest) -> AuthUser:
    email = _normalize_email(payload.email)
    role = _normalize_role(payload.role)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported role.")

    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        email=email,
        role=role,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()
    await _create_notification(
        db,
        user.id,
        notification_type="system",
        title="Welcome to SecureOps",
        message="Your account has been created and is ready to use.",
    )
    await db.commit()
    await db.refresh(user)
    return _to_public_user(user)


async def login_user(db: AsyncSession, payload: AuthLoginRequest) -> AuthResponse:
    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token = secrets.token_urlsafe(32)
    issued_at = _utc_now()
    session = AuthSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=issued_at + timedelta(seconds=settings.AUTH_SESSION_TTL_SECONDS),
        last_used_at=issued_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(user)

    # Fire background sync without blocking login response.
    asyncio.create_task(_background_sync_for_user(user.id, user.role))

    return AuthResponse(access_token=token, user=_to_public_user(user))


async def logout_user(
    db: AsyncSession,
    auth: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, str]:
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    token = auth.credentials
    token_hash = _hash_token(token.strip())
    result = await db.execute(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.revoked_at.is_(None),
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")

    session.revoked_at = _utc_now()
    await db.commit()
    return {"detail": "Logged out successfully."}


async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    token = auth.credentials
    token_hash = _hash_token(token.strip())
    result = await db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == token_hash, AuthSession.revoked_at.is_(None))
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")

    session, user = row
    now = _utc_now()
    expires_at = _as_utc(session.expires_at)
    if expires_at is None or expires_at <= now:
        session.revoked_at = now
        session.expires_at = now
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")

    session.last_used_at = now
    await db.commit()
    return _to_public_user(user)


async def reset_password(db: AsyncSession, payload: PasswordResetRequest) -> dict[str, str]:
    # Deliberately non-enumerable: account lookup never changes the success response.
    if not is_password_reset_email_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email delivery is not configured.",
        )

    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        return {"detail": "If an account exists for that email, reset instructions have been queued."}

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=_utc_now() + timedelta(seconds=settings.PASSWORD_RESET_TOKEN_TTL_SECONDS),
    )
    db.add(reset_token)

    reset_url = build_password_reset_url(token)
    try:
        await asyncio.to_thread(
            send_password_reset_email,
            user.email,
            reset_url,
            settings.PASSWORD_RESET_TOKEN_TTL_SECONDS,
        )
    except (EmailConfigurationError, EmailDeliveryError) as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email could not be delivered.",
        ) from exc

    await db.commit()
    return {"detail": "If an account exists for that email, reset instructions have been queued."}

