from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)

    model_config = ConfigDict(extra="ignore")


class AuthRegisterRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    role: str = Field(min_length=1)

    model_config = ConfigDict(extra="ignore")


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3)

    model_config = ConfigDict(extra="ignore")


class AuthUser(BaseModel):
    id: str
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser
