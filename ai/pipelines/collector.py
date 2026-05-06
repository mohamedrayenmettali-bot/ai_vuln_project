import os
import json
import time
import requests
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DEFECTDOJO_URL = os.getenv("DEFECTDOJO_URL", "http://localhost:8080")
API_TOKEN      = os.getenv("DEFECTDOJO_API_TOKEN", "")
USE_EPSS       = os.getenv("USE_EPSS", "true").lower() == "true"
PAGE_SIZE      = 100

# Path configuration (Relative to project root)
BASE_DIR    = Path(__file__).resolve().parent.parent
OUTPUT_DIR  = BASE_DIR / "data"
OUTPUT_PATH = OUTPUT_DIR / "raw_findings.json"

if not API_TOKEN:
    print("WARNING: DEFECTDOJO_API_TOKEN is not set. Using only local data if available.")

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}

def extract_cve_ids(finding: dict) -> list[str]:
    """Return all CVE IDs found in a finding, in priority order."""
    cves: list[str] = []
    
    # vulnerability_ids list (API response)
    for item in finding.get("vulnerability_ids") or []:
        if isinstance(item, dict):
            vid = str(item.get("vulnerability_id") or "").strip().upper()
        else:
            vid = str(item).strip().upper()
        if vid.startswith("CVE-"):
            cves.append(vid)

    # top-level cve field (legacy / some parsers)
    cve = str(finding.get("cve") or "").strip().upper()
    if cve.startswith("CVE-") and cve not in cves:
        cves.append(cve)

    return cves

def compute_sla(finding: dict) -> int:
    """Return SLA days remaining, preferring API-provided values when available."""
    sla_days_remaining = finding.get("sla_days_remaining")
    if sla_days_remaining is not None:
        try:
            return int(float(sla_days_remaining))
        except (TypeError, ValueError):
            pass

    sla_expiration_date = finding.get("sla_expiration_date")
    if not sla_expiration_date:
        return 0

    try:
        expiration = date.fromisoformat(str(sla_expiration_date)[:10])
        return (expiration - datetime.utcnow().date()).days
    except (TypeError, ValueError):
        return 0

def collect_from_dojo():
    if not API_TOKEN:
        print("ERROR: Cannot collect without API_TOKEN.")
        return []

    print(f"Fetching findings from DefectDojo at {DEFECTDOJO_URL}...")
    findings: list[dict] = []
    url = f"{DEFECTDOJO_URL}/api/v2/findings/?limit={PAGE_SIZE}&offset=0&duplicate=false"

    while url:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        findings.extend(data.get("results", []))
        url = data.get("next")
        print(f"  Fetched {len(findings)} / {data.get('count', '?')} findings...")
        time.sleep(0.1)
    
    return findings

def enrich_epss(findings: list):
    if not USE_EPSS:
        for f in findings:
            f["_epss_score"] = 0.0
            f["_epss_percentile"] = 0.0
        return

    print("Enriching with EPSS scores...")
    cve_ids_to_fetch: set[str] = set()
    for f in findings:
        if f.get("epss_score") is not None and float(f.get("epss_score", 0)) > 0:
            f["_epss_score"]      = float(f["epss_score"])
            f["_epss_percentile"] = float(f.get("epss_percentile", 0))
            continue
        for cve in extract_cve_ids(f):
            cve_ids_to_fetch.add(cve)

    cve_list = list(cve_ids_to_fetch)
    epss_map: dict[str, dict] = {}
    for i in range(0, len(cve_list), 30):
        batch = ",".join(cve_list[i : i + 30])
        try:
            r = requests.get("https://api.first.org/data/v1/epss", params={"cve": batch}, timeout=10)
            r.raise_for_status()
            for entry in r.json().get("data", []):
                epss_map[entry["cve"].upper()] = {
                    "epss": float(entry.get("epss", 0.0)),
                    "percentile": float(entry.get("percentile", 0.0)),
                }
            time.sleep(0.2)
        except Exception as exc:
            print(f"  EPSS batch failed: {exc}")

    for f in findings:
        if "_epss_score" in f: continue
        score = {"epss": 0.0, "percentile": 0.0}
        for cve in extract_cve_ids(f):
            if cve in epss_map:
                score = epss_map[cve]
                break
        f["_epss_score"]      = score["epss"]
        f["_epss_percentile"] = score["percentile"]

def main():
    try:
        findings = collect_from_dojo()
        if not findings:
            print("No findings collected.")
            return

        enrich_epss(findings)

        for f in findings:
            f["_component_name"] = f.get("component_name") or ""
            f["_component_version"] = f.get("component_version") or ""
            f["_found_by_count"] = len(f.get("found_by") or [])
            f["_endpoints_count"] = len(f.get("endpoints") or [])
            f["_nb_occurrences"] = f.get("nb_occurrences", 1)
            f["_sla_days_remaining"] = compute_sla(f)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = {
            "collected_at":   datetime.utcnow().isoformat() + "Z",
            "source_url":     DEFECTDOJO_URL,
            "total_findings": len(findings),
            "epss_enriched":  USE_EPSS,
            "findings":       findings,
        }

        with open(OUTPUT_PATH, "w") as fh:
            json.dump(output, fh, indent=2, default=str)

        print(f"\nDone. Saved {len(findings)} findings -> {OUTPUT_PATH}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    main()
