"""
data_loader.py — Load and transform CVEfixes DB into DefectDojo-compatible features.

Two sources:
  1. CVEfixes SQLite DB  → training data
  2. DefectDojo CSV      → validation / real-world data
"""

import os
import re
import json
import time
import sqlite3
import warnings
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd

from ai.config import (
    CVEFIXES_CUTOFF, CWE_GROUPS, CWE_COLS, CWE_DANGER_WEIGHTS,
    SEVERITY_MAP, FEATURE_COLS, TARGET_COL, DATA_DIR,
    EPSS_DEFAULT_SCORE, EPSS_DEFAULT_PERCENTILE
)
from ai.utils.ml_utils import extract_cwe_number, cwe_to_flags, compute_age_days

warnings.filterwarnings("ignore")


CVEFIXES_SQL = """
SELECT
    cv.cve_id,
    COALESCE(cv.cvss3_base_score, cv.cvss2_base_score) AS cvss_score,
    LOWER(cv.severity)                                  AS severity,
    cv.published_date,
    cv.description,
    cc.cwe_id
FROM cve cv
JOIN fixes              fx ON cv.cve_id = fx.cve_id
JOIN cwe_classification cc ON cv.cve_id = cc.cve_id
WHERE COALESCE(cv.cvss3_base_score, cv.cvss2_base_score) IS NOT NULL
"""



def compute_risk_score(row: dict) -> float:
    return round(float(row.get("cvss_score", 0)), 1)



def fetch_epss_scores(cves: list) -> dict:
    """Fetch EPSS scores using the FIRST API, with local caching."""
    cache_path = os.path.join(DATA_DIR, "epss_cache.json")
    epss_data = {}
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                epss_data = json.load(f)
            print(f"[EPSS] Loaded {len(epss_data)} scores from local cache.")
        except Exception as e:
            print(f"[EPSS] Failed to load cache: {e}")
    
    # Identify which CVEs still need to be fetched
    missing_cves = [c for c in cves if c not in epss_data]
    if not missing_cves:
        return epss_data

    batch_size = 100
    print(f"[EPSS] Fetching scores for {len(missing_cves)} missing CVEs in batches of {batch_size}...")
    
    for i in range(0, len(missing_cves), batch_size):
        batch = missing_cves[i:i+batch_size]
        cve_str = ",".join(batch)
        url = f"https://api.first.org/data/v1/epss?cve={cve_str}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    for item in data.get("data", []):
                        epss_data[item["cve"]] = {
                            "epss": float(item["epss"]),
                            "percentile": float(item["percentile"])
                        }
            time.sleep(0.1) # Be nice to the API
        except Exception as e:
            print(f"[EPSS] Error fetching batch {i//batch_size + 1}: {e}")
            time.sleep(1.0)
            
    # Cache the updated data
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(epss_data, f, indent=4)
        print(f"[EPSS] Updated local cache with {len(epss_data)} total entries.")
    except Exception as e:
        print(f"[EPSS] Failed to save cache: {e}")
        
    return epss_data



def load_cvefixes(db_path: str) -> pd.DataFrame:
    print(f"[DataLoader] Connecting to CVEfixes DB: {db_path}")
    conn = sqlite3.connect(db_path)
    df_raw = pd.read_sql_query(CVEFIXES_SQL, conn)
    conn.close()
    print(f"[DataLoader] Raw rows: {len(df_raw):,}")

    unique_cves = df_raw["cve_id"].dropna().unique().tolist()
    cve_epss_map = fetch_epss_scores(unique_cves)

    rows = []
    for _, row in df_raw.iterrows():
        sev_str   = (row["severity"] or "low").lower().strip()
        sev_score = SEVERITY_MAP.get(sev_str, 1)
        cwe_num   = extract_cwe_number(str(row.get("cwe_id", "")))
        cwe_flags = cwe_to_flags(cwe_num)
        age       = compute_age_days(str(row.get("published_date", "")), CVEFIXES_CUTOFF)

        # Compute a weighted CWE risk score
        cwe_risk = sum(cwe_flags[g] * CWE_DANGER_WEIGHTS.get(g, 0.35) for g in CWE_COLS)

        epss_info = cve_epss_map.get(row["cve_id"], {"epss": EPSS_DEFAULT_SCORE, "percentile": EPSS_DEFAULT_PERCENTILE})

        record = {
            "cve_id":         row["cve_id"],
            "cvss_score":     round(float(row["cvss_score"]), 1),
            "description":    str(row.get("description", "")),
            "severity":       sev_str,
            "severity_score": sev_score,
            "epss_score":     epss_info["epss"],
            "epss_percentile":epss_info["percentile"],
            "age_days":       age,
            "is_verified":    1,     # NVD-validated → always 1
            "is_active":      1,
            "has_cve":        1,
            "cwe_total_risk": cwe_risk,
            **cwe_flags,
        }
        # In this ML formulation, target is explicitly cvss_score
        record[TARGET_COL] = record["cvss_score"]
        rows.append(record)

    df = pd.DataFrame(rows)
    df = df.dropna(subset=[TARGET_COL])

    # Compute sample weights to handle class imbalance (inverse frequency)
    counts = df["severity"].value_counts(normalize=True)
    df["sample_weight"] = df["severity"].map(lambda s: 1.0 / counts.get(s, 1.0))
    df["sample_weight"] = df["sample_weight"] / df["sample_weight"].mean()

    print(f"[DataLoader] Processed rows : {len(df):,}")
    print(f"[DataLoader] Risk score     : "
          f"mean={df[TARGET_COL].mean():.2f}  "
          f"std={df[TARGET_COL].std():.2f}  "
          f"min={df[TARGET_COL].min():.2f}  "
          f"max={df[TARGET_COL].max():.2f}")
    return df


def load_defectdojo(csv_path: str) -> pd.DataFrame:
    """
    Load DefectDojo features.csv export.
    Drops non-feature columns and adds risk_score target.
    """
    print(f"[DataLoader] Loading DefectDojo CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[DataLoader] Rows: {len(df):,} | Cols: {df.shape[1]}")

    # Drop non-feature cols
    drop_cols = ["finding_id", "title", "scanner_OTHER", "ai_risk_score", "ai_severity"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Encode severity
    df["severity_score"] = df["severity"].str.lower().map(SEVERITY_MAP).fillna(1).astype(int)

    # Compute a weighted CWE risk score (vectorized)
    df["cwe_total_risk"] = 0.0
    for col in CWE_COLS:
        if col in df.columns:
            df["cwe_total_risk"] += df[col] * CWE_DANGER_WEIGHTS.get(col, 0.35)

    # Compute ground truth target
    df[TARGET_COL] = df.apply(lambda r: compute_risk_score(r.to_dict()), axis=1)

    # Compute sample weights
    counts = df["severity"].str.lower().value_counts(normalize=True)
    df["sample_weight"] = df["severity"].str.lower().map(lambda s: 1.0 / counts.get(s, 1.0))
    df["sample_weight"] = df["sample_weight"] / df["sample_weight"].mean()

    print(f"[DataLoader] Risk score: "
          f"mean={df[TARGET_COL].mean():.2f}  "
          f"std={df[TARGET_COL].std():.2f}")
    return df


def summarize(df: pd.DataFrame, name: str = "Dataset") -> None:
    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    print(f"  Shape       : {df.shape}")
    print(f"  Missing vals: {df.isnull().sum().sum()}")
    if "severity" in df.columns:
        print(f"  Severity dist:\n{df['severity'].value_counts().to_string()}")
    if TARGET_COL in df.columns:
        s = df[TARGET_COL]
        print(f"  Risk score  : mean={s.mean():.2f}  std={s.std():.2f}  "
              f"min={s.min():.2f}  max={s.max():.2f}")
    print(f"{'='*55}\n")
