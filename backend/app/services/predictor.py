from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.base import BaseModelPredictions, PredictionInput, PredictionResult  # noqa: E402
from app.config import settings
from ai.config import (  # noqa: E402
    CWE_COLS,
    CWE_DANGER_WEIGHTS,
    EPSS_DEFAULT_PERCENTILE,
    EPSS_DEFAULT_SCORE,
    FEATURE_COLS as ALL_STRUCTURED_FEATURE_COLS,
    FEATURES_PATH,
    MODEL_PATH,
)
from ai.pipelines.data_loader import fetch_epss_scores  # noqa: E402
from ai.utils.ml_utils import compute_age_days, cwe_to_flags, encode_chunked, extract_cwe_number, score_to_severity  # noqa: E402

MODELS_DIR = ROOT / "ai" / "models"
SELECTOR_PATH = MODELS_DIR / "feature_selector.pkl"
PCA_PATH = MODELS_DIR / "pca_reducer.pkl"
SCALER_PATH = MODELS_DIR / "feature_scaler.pkl"

log = logging.getLogger("vuln_api.predictor")


class PredictorService:
    _instance: Optional["PredictorService"] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "PredictorService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._model_lock = threading.Lock()
        self._encoder_lock = threading.Lock()
        self.models: dict = {}
        self.feature_cols: list[str] = []
        self.selector = None
        self.pca = None
        self.scaler = None
        self.nlp_model_name = settings.DEFAULT_NLP_MODEL_NAME
        self.encoder: Optional[SentenceTransformer] = None
        self.model_loaded = False
        self.nlp_encoder_ready = False
        self._startup_time = time.time()

    def load(self) -> None:
        bundle = joblib.load(MODEL_PATH)
        models = bundle["models"]
        nlp_model_name = bundle.get("nlp_model", settings.DEFAULT_NLP_MODEL_NAME)
        feature_cols = joblib.load(FEATURES_PATH)
        selector = joblib.load(SELECTOR_PATH)
        scaler = joblib.load(SCALER_PATH)
        pca = joblib.load(PCA_PATH) if PCA_PATH.exists() else None

        with self._model_lock:
            model_name_changed = self.nlp_model_name != nlp_model_name
            self.models = models
            self.nlp_model_name = nlp_model_name
            self.feature_cols = feature_cols
            self.selector = selector
            self.scaler = scaler
            self.pca = pca
            self.model_loaded = True

        if model_name_changed:
            with self._encoder_lock:
                self.encoder = None
                self.nlp_encoder_ready = False

    def warm_encoder(self) -> None:
        self._ensure_encoder()

    def _ensure_encoder(self) -> SentenceTransformer:
        with self._encoder_lock:
            if not self.nlp_encoder_ready or self.encoder is None:
                self.encoder = SentenceTransformer(self.nlp_model_name)
                self.encoder.encode([settings.ENCODER_WARMUP_TEXT], show_progress_bar=False)
                self.nlp_encoder_ready = True
            return self.encoder

    @staticmethod
    def _populate_epss(inputs: list[PredictionInput]) -> list[PredictionInput]:
        missing_ids = sorted(
            {
                normalized
                for item in inputs
                if item.cve_id and (item.epss_score is None or item.epss_percentile is None)
                if (normalized := item.cve_id.upper().strip())
            }
        )
        if not missing_ids:
            return inputs

        try:
            epss_map = fetch_epss_scores(missing_ids)
        except Exception:
            log.exception("EPSS auto-fetch failed.")
            return inputs

        hydrated: list[PredictionInput] = []
        for item in inputs:
            if not item.cve_id:
                hydrated.append(item)
                continue

            key = item.cve_id.upper().strip()
            entry = epss_map.get(key)
            if not entry:
                hydrated.append(item)
                continue

            hydrated.append(
                item.model_copy(
                    update={
                        "epss_score": item.epss_score if item.epss_score is not None else float(entry["epss"]),
                        "epss_percentile": (
                            item.epss_percentile
                            if item.epss_percentile is not None
                            else float(entry["percentile"])
                        ),
                    }
                )
            )
        return hydrated

    @staticmethod
    def _build_structured(item: PredictionInput) -> pd.DataFrame:
        cwe_num = extract_cwe_number(item.cwe_id or "")
        cwe_flags = cwe_to_flags(cwe_num)
        cwe_risk = sum(cwe_flags[group] * CWE_DANGER_WEIGHTS.get(group, 0.35) for group in CWE_COLS)

        has_cve = bool(item.cve_id and item.cve_id.strip())

        if item.epss_score is not None:
            epss_score = item.epss_score
        elif not has_cve:
            epss_score = min(0.20, max(0.01, cwe_risk * 0.02))
        else:
            epss_score = EPSS_DEFAULT_SCORE

        if item.epss_percentile is not None:
            epss_percentile = item.epss_percentile
        elif not has_cve:
            epss_percentile = min(0.60, max(0.05, cwe_risk * 0.20))
        else:
            epss_percentile = EPSS_DEFAULT_PERCENTILE

        return pd.DataFrame(
            [
                {
                    "epss_score": epss_score,
                    "epss_percentile": epss_percentile,
                    "age_days": compute_age_days(item.published_date or ""),
                    "cwe_total_risk": cwe_risk,
                    **cwe_flags,
                }
            ]
        )

    def _run_pipeline(
        self,
        structured_rows: list[pd.DataFrame],
        descriptions: list[str],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        with self._model_lock:
            if not self.model_loaded:
                raise RuntimeError("Model artifacts are not loaded.")
            feature_cols = list(self.feature_cols)
            selector = self.selector
            pca = self.pca
            scaler = self.scaler
            models = dict(self.models)

        numeric_df = pd.concat(structured_rows, ignore_index=True)
        aligned_numeric = pd.DataFrame(index=numeric_df.index)
        for col in ALL_STRUCTURED_FEATURE_COLS:
            aligned_numeric[col] = numeric_df[col].values if col in numeric_df.columns else 0.0

        selected_numeric_cols = [col for col in feature_cols if not col.startswith("pca_emb_")]
        selected = pd.DataFrame(selector.transform(aligned_numeric), columns=selected_numeric_cols)

        if pca is not None:
            embeddings = encode_chunked(self._ensure_encoder(), descriptions)
            reduced_embeddings = pca.transform(embeddings)
            embedding_cols = [f"pca_emb_{index}" for index in range(reduced_embeddings.shape[1])]
            selected = pd.concat([selected, pd.DataFrame(reduced_embeddings, columns=embedding_cols)], axis=1)

        selected = selected[feature_cols]
        scaled = pd.DataFrame(scaler.transform(selected), index=selected.index, columns=selected.columns)

        xgb_pred = models["xgb"].predict(selected)
        lgbm_pred = models["lgbm"].predict(selected)
        cat_pred = models["cat"].predict(selected)
        mlp_pred = models["mlp"].predict(scaled)
        knn_pred = models["knn"].predict(scaled)

        stacked = pd.DataFrame(
            {
                "xgb": xgb_pred,
                "lgbm": lgbm_pred,
                "cat": cat_pred,
                "mlp": mlp_pred,
                "knn": knn_pred,
            }
        )
        final_pred = np.clip(models["meta"].predict(stacked), 0.0, 10.0)
        return final_pred, xgb_pred, lgbm_pred, cat_pred, mlp_pred, knn_pred

    def predict_single(self, item: PredictionInput) -> PredictionResult:
        item = self._populate_epss([item])[0]
        final, xgb_pred, lgbm_pred, cat_pred, mlp_pred, knn_pred = self._run_pipeline(
            [self._build_structured(item)],
            [item.description or ""],
        )
        score = float(final[0])
        return PredictionResult(
            risk_score=round(score, 3),
            severity_label=score_to_severity(score),
            base_predictions=BaseModelPredictions(
                {
                    "xgb": round(float(xgb_pred[0]), 3),
                    "lgbm": round(float(lgbm_pred[0]), 3),
                    "cat": round(float(cat_pred[0]), 3),
                    "mlp": round(float(mlp_pred[0]), 3),
                    "knn": round(float(knn_pred[0]), 3),
                }
            ),
            epss_score=item.epss_score,
            epss_percentile=item.epss_percentile,
            cve_id=item.cve_id,
        )

    def predict_batch(self, items: list[PredictionInput]) -> list[PredictionResult]:
        items = self._populate_epss(items)
        final, xgb_pred, lgbm_pred, cat_pred, mlp_pred, knn_pred = self._run_pipeline(
            [self._build_structured(item) for item in items],
            [item.description or "" for item in items],
        )

        results: list[PredictionResult] = []
        for index, item in enumerate(items):
            score = float(final[index])
            results.append(
                PredictionResult(
                    risk_score=round(score, 3),
                    severity_label=score_to_severity(score),
                    base_predictions=BaseModelPredictions(
                        {
                            "xgb": round(float(xgb_pred[index]), 3),
                            "lgbm": round(float(lgbm_pred[index]), 3),
                            "cat": round(float(cat_pred[index]), 3),
                            "mlp": round(float(mlp_pred[index]), 3),
                            "knn": round(float(knn_pred[index]), 3),
                        }
                    ),
                    epss_score=item.epss_score,
                    epss_percentile=item.epss_percentile,
                    cve_id=item.cve_id,
                )
            )
        return results

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._startup_time
