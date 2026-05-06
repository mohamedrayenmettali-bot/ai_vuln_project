from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: str = Field(min_length=1)
    content: str = Field(min_length=1)

    model_config = ConfigDict(extra="ignore")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class ChatResponse(BaseModel):
    reply: str
