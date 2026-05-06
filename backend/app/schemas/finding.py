from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.db.models.finding import SeverityLevel, FindingStatus

class FindingBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = SeverityLevel.MEDIUM
    status: Optional[FindingStatus] = FindingStatus.OPEN
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    ai_risk_score: Optional[float] = None
    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None
    scanner: Optional[str] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    external_updated_at: Optional[datetime] = None
    external_payload_hash: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    local_updated_at: Optional[datetime] = None
    sync_conflict: Optional[bool] = False
    assigned_to: Optional[str] = None

class FindingCreate(FindingBase):
    project_id: str

class FindingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    status: Optional[FindingStatus] = None
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    ai_risk_score: Optional[float] = None
    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None
    scanner: Optional[str] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    assigned_to: Optional[str] = None

class FindingOut(FindingBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
