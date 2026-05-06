import re
import numpy as np
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
from ai.config import CWE_GROUPS, CWE_COLS, SCORE_THRESHOLDS, SeverityLevel

def extract_cwe_number(cwe_str: str):
    """'CWE-79' → 79  |  'NVD-CWE-noinfo' → None"""
    if not cwe_str or not isinstance(cwe_str, str):
        return None
    m = re.search(r"(\d+)", cwe_str)
    return int(m.group(1)) if m else None

def cwe_to_flags(cwe_num) -> dict:
    """Return one-hot dict of CWE category flags."""
    flags = {col: 0 for col in CWE_COLS}
    if cwe_num is None:
        flags["cwe_other"] = 1
        return flags
    matched = False
    for group, ids in CWE_GROUPS.items():
        if cwe_num in ids:
            flags[group] = 1
            matched = True
    if not matched:
        flags["cwe_other"] = 1
    return flags

def score_to_severity(score: float) -> SeverityLevel:
    """Convert numerical CVSS/Risk score to severity label."""
    for threshold, label in SCORE_THRESHOLDS:
        if score >= threshold:
            return label
    return SeverityLevel.LOW

def compute_age_days(published_date: str, reference_date: datetime | None = None) -> int:
    """Calculate age in days based on a publication date versus a reference date."""
    if not published_date:
        return 365
    try:
        pub = datetime.strptime(str(published_date)[:10], "%Y-%m-%d")
        ref = reference_date or datetime.utcnow()
        return max(0, min((ref - pub).days, 3650))
    except Exception:
        return 365

def weighted_mae(y_true, y_pred, sample_weight) -> float:
    """Calculate weighted mean absolute error."""
    return float(np.average(np.abs(np.asarray(y_true) - np.asarray(y_pred)),
                             weights=np.asarray(sample_weight)))

def encode_chunked(encoder: "SentenceTransformer",
                   texts: list[str],
                   chunk_chars: int = 2000) -> np.ndarray:
    """Encode large texts by chunking and averaging embeddings."""
    results = []
    for text in texts:
        chunks = [text[i: i + chunk_chars]
                  for i in range(0, max(len(text), 1), chunk_chars)] or [""]
        vecs = encoder.encode(chunks, show_progress_bar=False)
        results.append(vecs.mean(axis=0))
    return np.array(results)
