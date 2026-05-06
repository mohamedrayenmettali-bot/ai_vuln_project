import time
import requests
from datetime import datetime, date
from fastapi import HTTPException
from app.config import settings

def extract_cve_ids(finding: dict) -> list[str]:
    """Return all CVE IDs found in a finding, in priority order."""
    cves: list[str] = []

    # a) vulnerability_ids list (API response)
    for item in finding.get("vulnerability_ids") or []:
        if isinstance(item, dict):
            vid = str(item.get("vulnerability_id") or "").strip().upper()
        else:
            vid = str(item).strip().upper()
        if vid.startswith("CVE-"):
            cves.append(vid)

    # b) top-level cve field (legacy / some parsers)
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

class DefectDojoService:
    def __init__(self):
        self.url = settings.DEFECTDOJO_URL.rstrip("/")
        self.token = settings.DEFECTDOJO_API_TOKEN
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

    def fetch_findings(self, limit: int = 100) -> list[dict]:
        """Fetch raw findings directly from DefectDojo via its API, respecting the limit."""
        if not self.token:
            raise ValueError(
                "DEFECTDOJO_API_TOKEN is not set. Please configure the "
                "integration in system settings or environment variables."
            )

        findings: list[dict] = []
        # DefectDojo API limit per request is usually capped (e.g., 100).
        # We fetch in pages until we hit the user-requested total limit.
        page_limit = min(limit, 100)
        next_url = f"{self.url}/api/v2/findings/?limit={page_limit}&offset=0&duplicate=false"

        while next_url and len(findings) < limit:
            try:
                resp = requests.get(next_url, headers=self.headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(status_code=502, detail=f"Failed to connect to DefectDojo: {str(e)}")
            except requests.exceptions.JSONDecodeError:
                raise HTTPException(
                    status_code=502, 
                    detail=f"DefectDojo response was not valid JSON. Status={resp.status_code}"
                )

            results = data.get("results", [])
            findings.extend(results)
            
            # If we've reached or exceeded the requested limit, stop.
            if len(findings) >= limit:
                findings = findings[:limit]
                break
                
            next_url = data.get("next")
            time.sleep(0.1)

        return findings

    def enrich_findings(self, findings: list[dict], use_epss: bool = None) -> list[dict]:
        """Enrich findings with optional EPSS and normalization tags."""
        if use_epss is None:
            use_epss = settings.USE_EPSS

        if use_epss:
            cve_ids_to_fetch: set[str] = set()
            for f in findings:
                # Re-use existing
                if f.get("epss_score") is not None and float(f.get("epss_score", 0)) > 0:
                    f["_epss_score"]      = float(f["epss_score"])
                    f["_epss_percentile"] = float(f.get("epss_percentile", 0))
                    continue

                for cve in extract_cve_ids(f):
                    cve_ids_to_fetch.add(cve)

            cve_list = list(cve_ids_to_fetch)
            epss_map: dict[str, dict] = {}
            fetch_errors: list[Exception] = []
            for i in range(0, len(cve_list), 30):
                batch = ",".join(cve_list[i : i + 30])
                try:
                    r = requests.get("https://api.first.org/data/v1/epss", params={"cve": batch}, timeout=10)
                    r.raise_for_status()
                    for entry in r.json().get("data", []):
                        epss_map[entry["cve"].upper()] = {
                            "epss":       float(entry.get("epss", 0.0)),
                            "percentile": float(entry.get("percentile", 0.0)),
                        }
                    time.sleep(0.2)
                except Exception as exc:
                    fetch_errors.append(exc)
                    break

            if fetch_errors:
                raise RuntimeError("Failed to enrich findings with EPSS data.") from fetch_errors[0]

            for f in findings:
                if "_epss_score" in f:
                    continue
                score = {"epss": 0.0, "percentile": 0.0}
                for cve in extract_cve_ids(f):
                    if cve in epss_map:
                        score = epss_map[cve]
                        break
                f["_epss_score"]      = score["epss"]
                f["_epss_percentile"] = score["percentile"]
        else:
            for f in findings:
                f["_epss_score"]      = 0.0
                f["_epss_percentile"] = 0.0

        for finding in findings:
            finding["_component_name"] = finding.get("component_name") or ""
            finding["_component_version"] = finding.get("component_version") or ""
            finding["_found_by_count"] = len(finding.get("found_by") or [])
            finding["_endpoints_count"] = len(finding.get("endpoints") or [])
            finding["_nb_occurrences"] = finding.get("nb_occurrences", 1)
            finding["_sla_days_remaining"] = compute_sla(finding)

        return findings

defectdojo_service = DefectDojoService()
