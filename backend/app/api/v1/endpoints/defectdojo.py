import asyncio

from fastapi import APIRouter, HTTPException, Query
from app.services.defectdojo import defectdojo_service
import sys
import os

# Ensure the ai package can be imported if needed. 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
try:
    from ai.pipelines.feature_engineering import process_findings
except ImportError:
    process_findings = None

router = APIRouter(prefix="/defectdojo", tags=["defectdojo"])

@router.get("/pull", summary="Pull and enrich findings from DefectDojo")
async def pull_findings(
    limit: int = Query(100, ge=1, le=1000, description="Number of findings to fetch per request"),
    enrich_epss: bool = Query(True, description="Enrich with EPSS scores"),
    feature_engineer: bool = Query(False, description="Convert extracted data to features using feature_engineering module")
):
    """
    Fetch findings directly from DefectDojo API, enrich with EPSS and other tags, 
    and optionally engineer features.
    """
    try:
        raw_findings = await asyncio.to_thread(defectdojo_service.fetch_findings, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
        
    try:
        enriched = await asyncio.to_thread(defectdojo_service.enrich_findings, raw_findings, enrich_epss)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if feature_engineer:
        if not process_findings:
            raise HTTPException(
                status_code=501, 
                detail="Feature engineering module not found or could not be imported."
            )
        try:
            df = await asyncio.to_thread(process_findings, enriched)
            # Return records as JSON
            return {
                "count": len(df),
                "features": df.to_dict(orient="records")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to engineer features: {str(e)}")

    return {
        "count": len(enriched),
        "data": enriched
    }
