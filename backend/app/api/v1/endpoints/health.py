from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_predictor
from app.services.predictor import PredictorService
from app.schemas.base import HealthResponse
from app.config import settings

router = APIRouter(prefix="/health", tags=["Health"])
HEALTH_STATUS_OK = "ok"
HEALTH_STATUS_READY = "ready"


@router.get("", response_model=HealthResponse, summary="Liveness probe")
def liveness(service: PredictorService = Depends(get_predictor)) -> HealthResponse:
    return HealthResponse(
        status=HEALTH_STATUS_OK,
        model_loaded=service.model_loaded,
        nlp_encoder_ready=service.nlp_encoder_ready,
        uptime_seconds=round(service.uptime_seconds, 2),
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
def readiness(service: PredictorService = Depends(get_predictor)) -> HealthResponse:
    if not service.model_loaded or not service.nlp_encoder_ready:
        raise HTTPException(status_code=503, detail=settings.SERVICE_NOT_READY_MESSAGE)
    return HealthResponse(
        status=HEALTH_STATUS_READY,
        model_loaded=service.model_loaded,
        nlp_encoder_ready=service.nlp_encoder_ready,
        uptime_seconds=round(service.uptime_seconds, 2),
    )
