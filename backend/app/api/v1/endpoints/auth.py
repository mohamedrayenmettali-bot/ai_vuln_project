from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, login_user, logout_user, register_user, reset_password, security
from app.db.session import get_db_session
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse, AuthUser, PasswordResetRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthResponse, summary="Authenticate a user")
async def login(body: AuthLoginRequest, db: AsyncSession = Depends(get_db_session)) -> AuthResponse:
    return await login_user(db, body)


@router.post("/register", response_model=AuthUser, summary="Register a new user")
async def register(body: AuthRegisterRequest, db: AsyncSession = Depends(get_db_session)) -> AuthUser:
    return await register_user(db, body)


@router.post("/forgot-password", summary="Request a password reset")
async def forgot_password(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    return await reset_password(db, body)


@router.get("/me", response_model=AuthUser, summary="Return the current user")
async def me(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return current_user


@router.post("/logout", summary="Invalidate the current session")
async def logout(
    db: AsyncSession = Depends(get_db_session),
    auth: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, str]:
    return await logout_user(db, auth)
