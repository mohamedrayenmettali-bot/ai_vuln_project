from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.bootstrap import create_schema, drop_schema
from app.db.models.auth_session import AuthSession
from app.db.models.finding import Finding, FindingStatus, SeverityLevel
from app.db.models.finding_event import FindingEvent
from app.db.models.notification import Notification
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.project import Project, ProjectStatus
from app.db.models.project_setting import ProjectIntegrationSetting
from app.db.models.user import User
from app.db.session import configure_database, get_sessionmaker
from app.schemas.base import BaseModelPredictions, PredictionResult
from app.services.predictor import PredictorService


@dataclass(slots=True)
class PredictorStub:
    model_loaded: bool = True
    nlp_encoder_ready: bool = True
    nlp_model_name: str = "fake-securebert"
    feature_cols: list[str] = None  # type: ignore[assignment]
    models: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.feature_cols is None:
            self.feature_cols = ["epss_score", "epss_percentile", "age_days", "cwe_total_risk"]
        if self.models is None:
            self.models = {
                "xgb": object(),
                "lgbm": object(),
                "cat": object(),
                "mlp": object(),
                "knn": object(),
                "meta": object(),
            }

    def load(self) -> None:
        self.model_loaded = True

    def warm_encoder(self) -> None:
        self.nlp_encoder_ready = True

    def predict_single(self, item) -> PredictionResult:
        return PredictionResult(
            risk_score=7.4,
            severity_label="High",
            base_predictions=BaseModelPredictions(root={
                "xgb": 7.1,
                "lgbm": 7.3,
                "cat": 7.2,
                "mlp": 7.4,
                "knn": 7.0,
            }),
            epss_score=item.epss_score,
            epss_percentile=item.epss_percentile,
            cve_id=item.cve_id,
        )

    def predict_batch(self, items) -> list[PredictionResult]:
        return [self.predict_single(item) for item in items]

    @property
    def uptime_seconds(self) -> float:
        return 42.0


def configure_test_database(tmp_path: Path) -> str:
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    configure_database(db_url)
    return db_url


async def bootstrap_test_schema() -> None:
    await create_schema()


async def teardown_test_schema() -> None:
    await drop_schema()


def patch_predictor_stub() -> PredictorStub:
    stub = PredictorStub()
    PredictorService._instance = stub  # type: ignore[attr-defined]
    return stub


async def create_user(
    *,
    email: str,
    password_hash: str,
    name: str = "Pytest User",
    role: str = "developer",
) -> User:
    async with get_sessionmaker()() as db:
        user = User(name=name, email=email, role=role, password_hash=password_hash)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def create_project(
    *,
    name: str,
    description: str = "",
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> Project:
    async with get_sessionmaker()() as db:
        project = Project(
            name=name,
            description=description,
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project


async def create_finding(
    *,
    project_id: str,
    title: str,
    severity: SeverityLevel = SeverityLevel.MEDIUM,
    status: FindingStatus = FindingStatus.OPEN,
    cvss_score: float | None = None,
    cve_id: str | None = None,
    ai_risk_score: float | None = None,
    epss_score: float | None = None,
    epss_percentile: float | None = None,
    scanner: str | None = None,
    source: str = "manual",
    external_id: str | None = None,
    assigned_to: str | None = None,
    description: str | None = None,
) -> Finding:
    async with get_sessionmaker()() as db:
        finding = Finding(
            project_id=project_id,
            title=title,
            description=description,
            severity=severity,
            status=status,
            cvss_score=cvss_score,
            cve_id=cve_id,
            ai_risk_score=ai_risk_score,
            epss_score=epss_score,
            epss_percentile=epss_percentile,
            scanner=scanner,
            source=source,
            external_id=external_id,
            assigned_to=assigned_to,
            created_at=datetime.now(timezone.utc),
        )
        db.add(finding)
        await db.commit()
        await db.refresh(finding)
        return finding


async def create_notification(
    *,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    project_id: str | None = None,
    finding_id: str | None = None,
    read: bool = False,
) -> Notification:
    async with get_sessionmaker()() as db:
        read_at = None
        if read:
            read_at = datetime.now(timezone.utc)
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            project_id=project_id,
            finding_id=finding_id,
            read_at=read_at,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification


async def create_project_settings(
    *,
    project_id: str,
    jira_url: str = "https://example.atlassian.net",
    project_key: str = "SEC",
    api_token: str = "",
    user_email: str = "sec@example.com",
    default_issue_type: str = "Bug",
    auto_critical: bool = True,
    auto_high_ai: bool = True,
) -> ProjectIntegrationSetting:
    async with get_sessionmaker()() as db:
        row = ProjectIntegrationSetting(
            project_id=project_id,
            jira_url=jira_url,
            project_key=project_key,
            api_token=api_token,
            user_email=user_email,
            default_issue_type=default_issue_type,
            auto_critical=auto_critical,
            auto_high_ai=auto_high_ai,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row


async def get_user_by_email(email: str) -> User | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()


async def get_auth_session_by_token(token: str) -> AuthSession | None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    async with get_sessionmaker()() as db:
        result = await db.execute(select(AuthSession).where(AuthSession.token_hash == token_hash))
        return result.scalars().first()


async def get_password_reset_tokens_for_user(user_id: str) -> list[PasswordResetToken]:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
        return list(result.scalars().all())


async def get_notification_by_id(notification_id: str) -> Notification | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        return result.scalars().first()


async def get_project_by_id(project_id: str) -> Project | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()


async def get_finding_by_id(finding_id: str) -> Finding | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(Finding).where(Finding.id == finding_id))
        return result.scalars().first()


async def get_project_settings_by_project_id(project_id: str) -> ProjectIntegrationSetting | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(select(ProjectIntegrationSetting).where(ProjectIntegrationSetting.project_id == project_id))
        return result.scalars().first()


async def get_finding_by_external_id(project_id: str, external_id: str) -> Finding | None:
    async with get_sessionmaker()() as db:
        result = await db.execute(
            select(Finding).where(
                Finding.project_id == project_id,
                Finding.external_id == external_id,
            )
        )
        return result.scalars().first()


async def get_finding_events(finding_id: str) -> list[FindingEvent]:
    async with get_sessionmaker()() as db:
        result = await db.execute(
            select(FindingEvent)
            .where(FindingEvent.finding_id == finding_id)
            .order_by(FindingEvent.created_at.asc())
        )
        return list(result.scalars().all())
