from sqlalchemy import Boolean, Column, String, DateTime, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
import uuid

class SeverityLevel(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"

class FindingStatus(str, enum.Enum):
    OPEN = "Open"
    MITIGATED = "Mitigated"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    status = Column(Enum(FindingStatus), default=FindingStatus.OPEN)
    cvss_score = Column(Float, nullable=True)

    cve_id = Column(String(50), nullable=True)
    ai_risk_score = Column(Float, nullable=True)
    epss_score = Column(Float, nullable=True)
    epss_percentile = Column(Float, nullable=True)
    scanner = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True, default="manual")
    external_id = Column(String(100), nullable=True, index=True)
    dedupe_key = Column(String(128), nullable=True, index=True)
    external_updated_at = Column(DateTime(timezone=True), nullable=True)
    external_payload_hash = Column(String(64), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    local_updated_at = Column(DateTime(timezone=True), nullable=True)
    sync_conflict = Column(Boolean, nullable=False, default=False)
    assigned_to = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="findings")
    events = relationship("FindingEvent", back_populates="finding", cascade="all, delete-orphan")
