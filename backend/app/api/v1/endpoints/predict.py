from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_predictor
from app.services.predictor import PredictorService
from app.schemas.base import (
    BatchPredictionInput,
    BatchPredictionResult,
    PredictionInput,
    PredictionResult,
)
from app.config import settings

router = APIRouter(prefix="/predict", tags=["Predictions"])
log = logging.getLogger("vuln_api.predict")


def _ensure_ready(service: PredictorService) -> None:
    if not service.model_loaded:
        raise HTTPException(status_code=503, detail=settings.MODEL_LOADING_MESSAGE)


@router.post("", response_model=PredictionResult, summary="Score a single vulnerability finding")
def predict_single(
    body: PredictionInput,
    service: PredictorService = Depends(get_predictor),
) -> PredictionResult:
    _ensure_ready(service)
    try:
        return service.predict_single(body)
    except Exception as exc:
        log.exception("Single prediction failed.")
        raise HTTPException(status_code=500, detail=settings.PREDICTION_FAILED_MESSAGE) from exc


@router.post("/batch", response_model=BatchPredictionResult, summary="Score multiple findings")
def predict_batch(
    body: BatchPredictionInput,
    service: PredictorService = Depends(get_predictor),
) -> BatchPredictionResult:
    _ensure_ready(service)
    started = time.perf_counter()
    try:
        results = service.predict_batch(body.findings)
    except Exception as exc:
        log.exception("Batch prediction failed.")
        raise HTTPException(status_code=500, detail=settings.BATCH_PREDICTION_FAILED_MESSAGE) from exc

    return BatchPredictionResult(
        results=results,
        count=len(results),
        elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
    )
