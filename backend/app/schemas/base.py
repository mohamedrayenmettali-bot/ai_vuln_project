from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, RootModel

from app.config import settings
from ai.config import SCHEMA_EXAMPLES, SeverityLevel


class PredictionInput(BaseModel):
    description: str = Field(default="", examples=[SCHEMA_EXAMPLES["finding_description"]])
    cve_id: Optional[str] = Field(default=None, examples=[SCHEMA_EXAMPLES["cve_id"]])
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, examples=[SCHEMA_EXAMPLES["severity"]])
    cwe_id: Optional[str] = Field(default=None, examples=[SCHEMA_EXAMPLES["cwe_id"]])
    published_date: Optional[str] = Field(default=None, examples=[SCHEMA_EXAMPLES["published_date"]])
    epss_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description=SCHEMA_EXAMPLES["epss_description"])
    epss_percentile: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=SCHEMA_EXAMPLES["epss_percentile_desc"],
    )


class BatchPredictionInput(BaseModel):
    findings: list[PredictionInput] = Field(..., min_length=1, max_length=settings.PREDICT_BATCH_MAX_FINDINGS)


class BaseModelPredictions(RootModel):
    root: dict[str, float]


class PredictionResult(BaseModel):
    risk_score: float = Field(ge=0.0, le=10.0)
    severity_label: str
    base_predictions: BaseModelPredictions
    epss_score: Optional[float] = Field(default=None)
    epss_percentile: Optional[float] = Field(default=None)
    cve_id: Optional[str] = Field(default=None)


class BatchPredictionResult(BaseModel):
    results: list[PredictionResult]
    count: int
    elapsed_ms: float


class ModelInfoResponse(BaseModel):
    nlp_model: str
    feature_cols: list[str]
    base_models: list[str]
    meta_learner: str
    model_path: str
    n_features: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    nlp_encoder_ready: bool
    uptime_seconds: float


class EpssItem(BaseModel):
    cve_id: str
    epss_score: float
    epss_percentile: float
    source: str = Field(default=settings.EPSS_SOURCE_NAME)


class EpssBatchInput(BaseModel):
    cve_ids: list[str] = Field(..., min_length=1, max_length=settings.EPSS_BATCH_MAX_CVES)


class EpssBatchResponse(BaseModel):
    results: list[EpssItem]
    not_found: list[str] = Field(default_factory=list)
