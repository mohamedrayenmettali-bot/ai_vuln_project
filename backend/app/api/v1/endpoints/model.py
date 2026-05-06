from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_predictor
from app.services.predictor import PredictorService
from app.schemas.base import ModelInfoResponse
from app.config import settings
from ai.config import MODEL_PATH

router = APIRouter(prefix="/model", tags=["Model"])
log = logging.getLogger("vuln_api.model")


@router.get("/info", response_model=ModelInfoResponse, summary="Loaded model metadata")
def model_info(service: PredictorService = Depends(get_predictor)) -> ModelInfoResponse:
    if not service.model_loaded:
        raise HTTPException(status_code=503, detail=settings.MODEL_NOT_LOADED_MESSAGE)

    return ModelInfoResponse(
        nlp_model=service.nlp_model_name,
        feature_cols=service.feature_cols,
        base_models=[name for name in service.models if name != "meta"],
        meta_learner=type(service.models.get("meta")).__name__,
        model_path=str(MODEL_PATH),
        n_features=len(service.feature_cols),
    )


@router.get("/features", summary="List selected feature names")
def model_features(service: PredictorService = Depends(get_predictor)) -> dict:
    if not service.model_loaded:
        raise HTTPException(status_code=503, detail=settings.MODEL_NOT_LOADED_MESSAGE)

    structured = [feature for feature in service.feature_cols if not feature.startswith("pca_emb_")]
    embeddings = [feature for feature in service.feature_cols if feature.startswith("pca_emb_")]
    return {
        "total": len(service.feature_cols),
        "structured": structured,
        "nlp_pca_embeddings": {
            "count": len(embeddings),
            "prefix": "pca_emb_",
        },
    }


@router.post("/reload", summary="Hot-reload model artifacts")
def reload_model(service: PredictorService = Depends(get_predictor)) -> dict:
    try:
        service.load()
        service.warm_encoder()
        return {"status": "reloaded", "features": len(service.feature_cols)}
    except Exception as exc:
        log.exception("Model reload failed.")
        raise HTTPException(status_code=500, detail=settings.MODEL_RELOAD_FAILED_MESSAGE) from exc
