from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.db.models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.ACTIVE

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_scan: Optional[datetime] = None
    pipeline_status: Optional[str] = None
    tech_stack: list[str] = Field(default_factory=list)
    findings_summary: dict[str, int] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)
