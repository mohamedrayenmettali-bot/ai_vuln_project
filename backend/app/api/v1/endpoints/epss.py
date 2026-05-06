from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Path as FastAPIPath

from app.schemas.base import EpssBatchInput, EpssBatchResponse, EpssItem
from app.config import settings

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.pipelines.data_loader import fetch_epss_scores

router = APIRouter(prefix="/epss", tags=["EPSS"])


@router.get("/{cve_id}", response_model=EpssItem, summary="Fetch EPSS score for one CVE")
def epss_single(
    cve_id: str = FastAPIPath(..., description="CVE identifier, e.g. CVE-2021-44228"),
) -> EpssItem:
    normalized = cve_id.upper().strip()
    data = fetch_epss_scores([normalized])
    if normalized not in data:
        raise HTTPException(status_code=404, detail=settings.EPSS_NOT_FOUND_TEMPLATE.format(cve_id=normalized))

    entry = data[normalized]
    return EpssItem(
        cve_id=normalized,
        epss_score=entry["epss"],
        epss_percentile=entry["percentile"],
    )


@router.post("/batch", response_model=EpssBatchResponse, summary="Fetch EPSS scores for multiple CVEs")
def epss_batch(body: EpssBatchInput) -> EpssBatchResponse:
    normalized = [cve_id.upper().strip() for cve_id in body.cve_ids]
    data = fetch_epss_scores(normalized)

    results: list[EpssItem] = []
    not_found: list[str] = []
    for cve_id in normalized:
        if cve_id in data:
            entry = data[cve_id]
            results.append(
                EpssItem(
                    cve_id=cve_id,
                    epss_score=entry["epss"],
                    epss_percentile=entry["percentile"],
                )
            )
        else:
            not_found.append(cve_id)

    return EpssBatchResponse(results=results, not_found=not_found)
