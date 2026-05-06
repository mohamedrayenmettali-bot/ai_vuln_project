from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectIntegrationSetting(Base):
    __tablename__ = "project_integration_settings"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    jira_url = Column(Text, nullable=False, default="")
    project_key = Column(String(64), nullable=False, default="")
    api_token = Column(Text, nullable=False, default="")
    user_email = Column(String(255), nullable=False, default="")
    default_issue_type = Column(String(64), nullable=False, default="Bug")
    auto_critical = Column(Boolean, nullable=False, default=True)
    auto_high_ai = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project")
