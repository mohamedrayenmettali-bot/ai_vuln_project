import os
import re
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timezone

# Path configuration (Relative to project root)
BASE_DIR    = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "raw_findings.json"
OUTPUT_PATH = BASE_DIR / "data" / "features.csv"

# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

SEVERITY_SCORE = {
    "critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "informational": 0
}

SEVERITY_TO_CVSS = {
    "critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.5, "info": 0.5, "informational": 0.5
}

SCANNER_MAP = {
    "semgrep":          "SAST",
    "bandit":           "SAST",
    "sonarqube":        "SAST",
    "zap scan":         "DAST",
    "zap":              "DAST",
    "trivy scan":       "SCA",
    "trivy":            "SCA",
    "dependency check": "SCA",
    "snyk":             "SCA",
    "npm audit":        "SCA",
}

CWE_CATEGORY_MAP = {
    # Injection
    **{c: "injection" for c in [74, 77, 78, 79, 80, 89, 94, 95, 96, 134, 176, 193, 611, 918, 1321]},
    # Auth
    **{c: "auth" for c in [285, 287, 306, 307, 384, 521, 522, 640, 693, 798, 939]},
    # Crypto
    **{c: "crypto" for c in [310, 311, 312, 319, 321, 326, 327, 328, 330, 338, 347, 353, 385, 1240]},
    # Access Control
    **{c: "access_control" for c in [22, 73, 264, 269, 276, 284, 471, 601, 732, 749, 829, 862, 863, 913, 915, 1021]},
    # Data Exposure
    **{c: "data_exposure" for c in [200, 201, 209, 359, 497, 524, 538, 540, 548, 598]},
    # Memory
    **{c: "memory" for c in [119, 120, 121, 122, 125, 401, 416, 476]},
    # Config
    **{c: "config" for c in [16, 358, 547, 614, 704, 843, 1004, 1104]},
    # Resource Mgmt
    **{c: "resource_mgmt" for c in [367, 399, 400, 407, 459, 674, 770, 772, 835, 908, 1050, 1333]},
    # Input Validation
    **{c: "input_validation" for c in [20, 190, 248, 705, 754, 1035]},
}

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_scanner(test_field) -> str:
    if isinstance(test_field, str):
        m = re.search(r"\(([^)]+)\)\s*$", test_field)
        label = m.group(1).lower() if m else test_field.lower()
    elif isinstance(test_field, dict):
        tt = test_field.get("test_type") or {}
        label = (tt.get("name") or test_field.get("title") or "").lower()
    else:
        label = ""

    for key, cat in SCANNER_MAP.items():
        if key in label: return cat
    return "OTHER"

def extract_cve(f: dict) -> bool:
    vids = f.get("vulnerability_ids")
    if isinstance(vids, str) and _CVE_RE.search(vids): return True
    if isinstance(vids, list):
        for item in vids:
            vid = item.get("vulnerability_id", "") if isinstance(item, dict) else str(item)
            if _CVE_RE.search(vid): return True
    cve = f.get("cve") or ""
    if isinstance(cve, str) and cve.upper().startswith("CVE-"): return True
    if _CVE_RE.search(f.get("title") or ""): return True
    return False

def parse_age(date_val) -> int:
    if date_val is None: return -1
    if isinstance(date_val, datetime):
        dt = date_val.replace(tzinfo=timezone.utc) if date_val.tzinfo is None else date_val
        return max((datetime.now(timezone.utc) - dt).days, 0)
    if isinstance(date_val, date):
        dt = datetime(date_val.year, date_val.month, date_val.day, tzinfo=timezone.utc)
        return max((datetime.now(timezone.utc) - dt).days, 0)
    try:
        dt = datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return max((datetime.now(timezone.utc) - dt).days, 0)
    except (ValueError, TypeError):
        return -1

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def process_findings(findings: list) -> pd.DataFrame:
    """
    Core logic to transform a list of raw findings into a feature-engineered DataFrame.
    Can be called by both CLI and API.
    """
    # Filter out duplicates
    findings = [f for f in findings if not f.get("duplicate", False)]
    
    rows = []
    for f in findings:
        severity = (f.get("severity") or "info").lower().strip()
        if severity not in SEVERITY_SCORE: 
            severity = "info"

        cvss = None
        for field in ("cvssv3_score", "cvssv2_score", "cvss_score"):
            val = f.get(field)
            if val is not None:
                try:
                    cvss = float(val)
                    break
                except (ValueError, TypeError): 
                    pass
        
        if cvss is None or not (0.0 <= cvss <= 10.0):
            cvss = SEVERITY_TO_CVSS.get(severity, 0.5)

        scanner = extract_scanner(f.get("test"))
        try:
            cwe_id  = int(str(f.get("cwe", "0")).replace("CWE-", "").strip())
            cwe_cat = CWE_CATEGORY_MAP.get(cwe_id, "other")
        except (ValueError, TypeError):
            cwe_cat = "unknown"

        rows.append({
            "finding_id":      f.get("id", -1),
            "title":           f.get("title", ""),
            "description":     f.get("description", ""), 
            "severity":        severity,
            "scanner":         scanner,
            "cwe_category":    cwe_cat,
            "cvss_score":      cvss,
            "epss_score":      float(f.get("_epss_score", 0.0)),
            "epss_percentile": float(f.get("_epss_percentile", 0.0)),
            "severity_score":  SEVERITY_SCORE.get(severity, 0),
            "age_days":        parse_age(f.get("date") or f.get("created")),
            "is_verified":     int(bool(f.get("verified", False))),
            "is_active":       int(bool(f.get("active", True))),
            "has_cve":         1 if extract_cve(f) else 0,
            "nb_occurrences":  f.get("_nb_occurrences", 1),
            "endpoints_count": f.get("_endpoints_count", 0),
            "found_by_count":  f.get("_found_by_count", 1),
            "has_component":   1 if f.get("_component_name") else 0,
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Compute AI risk score (for evaluation reference)
    cvss_norm = df["cvss_score"] / 10.0
    epss_norm = df["epss_score"]
    sev_norm  = df["severity_score"] / 4.0
    freshness = df["age_days"].apply(lambda d: 0.5 if d < 0 else max(0.0, 1.0 - d / 365.0))

    df["ai_risk_score"] = (1.0 + (0.40 * cvss_norm + 0.30 * epss_norm + 0.20 * sev_norm + 0.10 * freshness) * 9.0).round(2)
    df["ai_severity"] = pd.cut(df["ai_risk_score"], bins=[0, 2, 4, 6.5, 8.5, 10], labels=["Info", "Low", "Medium", "High", "Critical"])

    # One-hot encoding for categorical features
    df = pd.get_dummies(df, columns=["scanner", "cwe_category"], prefix=["scanner", "cwe"], dtype=int)
    
    return df

def main():
    print(f"Loading {INPUT_PATH}...")
    if not INPUT_PATH.exists():
        print(f"ERROR: {INPUT_PATH} not found.")
        return

    with open(INPUT_PATH) as fh:
        raw = json.load(fh)

    findings = raw.get("findings", raw) if isinstance(raw, dict) else raw
    print(f"  {len(findings)} findings loaded.")

    df = process_findings(findings)
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved -> {OUTPUT_PATH} ({df.shape[0]} rows)")

if __name__ == "__main__":
    main()
