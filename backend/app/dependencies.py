from __future__ import annotations

import uuid

from fastapi import Request

from app.services.predictor import PredictorService
from app.config import settings


def get_predictor() -> PredictorService:
    return PredictorService.get()


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", request.headers.get(settings.REQUEST_ID_HEADER, str(uuid.uuid4())))
