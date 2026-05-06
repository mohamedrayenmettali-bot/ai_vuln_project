
"""
config.py — Central configuration for the AI Vulnerability Risk Model.
All paths, constants, and hyperparameters live here.
"""

from enum import Enum
from pathlib import Path
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
if '__file__' in globals():
    BASE_DIR = Path(__file__).parent
else:
    BASE_DIR = Path.cwd()

DATA_DIR      = BASE_DIR / "data"
MODELS_DIR    = BASE_DIR / "models"
REPORTS_DIR   = BASE_DIR / "reports"

CVEFIXES_DB   = DATA_DIR / "CVEfixes.db"          # your SQLite dump
DEFECTDOJO_CSV = DATA_DIR / "features.csv"        # DefectDojo export
MODEL_PATH    = MODELS_DIR / "ai_risk_model.pkl"
FEATURES_PATH = MODELS_DIR / "model_features.pkl"
SCALER_PATH   = MODELS_DIR / "scaler.pkl"

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── CVEfixes ─────────────────────────────────────────────────────────────────
CVEFIXES_CUTOFF = datetime(2022, 8, 27)   # v1.0.7 collection cutoff

# ── EPSS Defaults ────────────────────────────────────────────────────────────
EPSS_DEFAULT_SCORE      = 0.0
EPSS_DEFAULT_PERCENTILE = 0.0

# ── Severity ─────────────────────────────────────────────────────────────────
class SeverityLevel(str, Enum):
    INFO     = "info"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

SEVERITY_MAP = {
    SeverityLevel.INFO:     0,
    SeverityLevel.LOW:      1,
    SeverityLevel.MEDIUM:   2,
    SeverityLevel.HIGH:     3,
    SeverityLevel.CRITICAL: 4,
}

SEVERITY_LABEL = {
    0: "Info",
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
}

# Score thresholds → severity bucket
SCORE_THRESHOLDS = [
    (8.0, SeverityLevel.CRITICAL),
    (6.0, SeverityLevel.HIGH),
    (3.5, SeverityLevel.MEDIUM),
    (0.0, SeverityLevel.LOW),
]

# ── Schema Metadata & Examples ───────────────────────────────────────────────
SCHEMA_EXAMPLES = {
    "finding_description": "A buffer overflow in libpng allows remote code execution.",
    "cve_id":              "CVE-2021-44228",
    "cwe_id":              "CWE-79",
    "published_date":      "2021-12-10",
    "severity":            SeverityLevel.MEDIUM,
    "epss_description":    "EPSS probability score [0-1]. Fetched automatically if omitted.",
    "epss_percentile_desc":"EPSS percentile [0-1]. Fetched automatically if omitted.",
}
CWE_COLS = [
    "cwe_injection", "cwe_memory", "cwe_input_validation",
    "cwe_access_control", "cwe_crypto", "cwe_auth",
    "cwe_data_exposure", "cwe_resource_mgmt", "cwe_config", "cwe_other",
]

FEATURE_COLS = [
    "epss_score", "epss_percentile",
    "age_days",
    "cwe_total_risk",
] + CWE_COLS

TARGET_COL = "cvss_score"


# ── CWE grouping (CWE-ID → DefectDojo category) ──────────────────────────────
CWE_GROUPS = {
    "cwe_injection":        [77,78,79,80,88,89,90,91,93,94,95,96,97,98,99,116,134,643,917,1336],
    "cwe_memory":           [119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,787,788,824,908],
    "cwe_input_validation": [20,74,75,76,113,138,184,228,229,230,231,232,233,234,235,236,237,238,239,240],
    "cwe_access_control":   [22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,264,269,270,271,
                             272,273,274,275,276,277,278,279,280,281,282,283,284,285,639,640],
    "cwe_crypto":           [310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,
                             326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,347],
    "cwe_auth":             [255,256,257,258,259,260,261,262,263,287,288,289,290,291,292,293,
                             294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309],
    "cwe_data_exposure":    [200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,
                             359,497,538,540,548,550,598,615],
    "cwe_resource_mgmt":    [400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,
                             416,417,476,772,789],
    "cwe_config":           [2,5,6,7,8,9,10,11,12,13,14,15,16,732,1004,1021,1022,1023,1024,1025],
}

# Danger weight per CWE group (used for target computation)
CWE_DANGER_WEIGHTS = {
    "cwe_memory":           0.95,
    "cwe_injection":        0.90,
    "cwe_auth":             0.80,
    "cwe_access_control":   0.75,
    "cwe_crypto":           0.65,
    "cwe_resource_mgmt":    0.60,
    "cwe_data_exposure":    0.55,
    "cwe_input_validation": 0.50,
    "cwe_config":           0.40,
    "cwe_other":            0.35,
}

# ── Model hyperparameters ────────────────────────────────────────────────────
XGBOOST_PARAMS = {
    "n_estimators":    300,
    "max_depth":       5,
    "learning_rate":   0.04,
    "subsample":       0.85,
    "colsample_bytree":0.85,
    "min_child_weight":3,
    "gamma":           0.1,
    "random_state":    42,
    "eval_metric":     "mae",
    "verbosity":       0,
}

TEST_SIZE      = 0.2
RANDOM_STATE   = 42
CV_FOLDS       = 5
