from __future__ import annotations

import asyncio

from app.core.security import get_password_hash
from app.db.models.project import ProjectStatus
from app.db.models.finding import SeverityLevel, FindingStatus
from app.services.defectdojo import defectdojo_service

from backend.tests.support import (
    create_finding,
    create_notification,
    create_project,
    create_user,
    get_auth_session_by_token,
    get_finding_by_id,
    get_finding_by_external_id,
    get_finding_events,
    get_notification_by_id,
    get_password_reset_tokens_for_user,
    get_project_by_id,
    get_project_settings_by_project_id,
)
from backend.tests.auth_helpers import TEST_PASSWORD


def _auth_headers(client, token: str) -> dict[str, str]:
    headers = dict(client.headers)
    headers["Authorization"] = f"Bearer {token}"
    return headers


def test_auth_sessions_persist_and_soft_revoke(public_client):
    user = asyncio.run(
        create_user(
            email="persisted-auth@example.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            name="Persisted Auth",
            role="developer",
        )
    )

    login_response = public_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = _auth_headers(public_client, token)

    me_response = public_client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == user.email

    session = asyncio.run(get_auth_session_by_token(token))
    assert session is not None
    assert session.revoked_at is None

    logout_response = public_client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    revoked_session = asyncio.run(get_auth_session_by_token(token))
    assert revoked_session is not None
    assert revoked_session.revoked_at is not None

    revoked_me_response = public_client.get("/api/auth/me", headers=headers)
    assert revoked_me_response.status_code == 401


def test_forgot_password_sends_configured_reset_email(public_client, monkeypatch):
    user = asyncio.run(
        create_user(
            email="reset@example.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            name="Reset User",
            role="developer",
        )
    )
    sent: dict[str, object] = {}

    def fake_send(to_email: str, reset_url: str, expires_in_seconds: int) -> None:
        sent["to_email"] = to_email
        sent["reset_url"] = reset_url
        sent["expires_in_seconds"] = expires_in_seconds

    monkeypatch.setattr("app.core.auth.is_password_reset_email_configured", lambda: True)
    monkeypatch.setattr("app.core.auth.build_password_reset_url", lambda token: f"https://dashboard/reset?token={token}")
    monkeypatch.setattr("app.core.auth.send_password_reset_email", fake_send)

    response = public_client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})

    assert response.status_code == 200
    assert sent["to_email"] == "reset@example.com"
    assert str(sent["reset_url"]).startswith("https://dashboard/reset?token=")
    tokens = asyncio.run(get_password_reset_tokens_for_user(user.id))
    assert len(tokens) == 1
    assert len(tokens[0].token_hash) == 64


def test_notifications_persist_and_track_read_state(public_client):
    user = asyncio.run(
        create_user(
            email="notifications@example.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            name="Notification User",
            role="developer",
        )
    )

    login_response = public_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = _auth_headers(public_client, token)

    first = asyncio.run(
        create_notification(
            user_id=user.id,
            notification_type="pipeline",
            title="Scan queued",
            message="A new scan is waiting in the queue.",
        )
    )
    second = asyncio.run(
        create_notification(
            user_id=user.id,
            notification_type="system",
            title="Policy updated",
            message="The workspace policy has been refreshed.",
        )
    )

    notifications_response = public_client.get(
        "/api/notifications",
        headers=headers,
        params={"unread_only": True},
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    # Login triggers a background sync which creates additional "sync" notifications;
    # verify that our two manually-created notifications are present among the unread ones.
    notification_ids = {item["id"] for item in notifications}
    assert first.id in notification_ids
    assert second.id in notification_ids

    unread_count_response = public_client.get("/api/notifications/unread-count", headers=headers)
    assert unread_count_response.status_code == 200
    initial_unread_count = unread_count_response.json()["count"]
    assert initial_unread_count >= 2

    mark_read_response = public_client.patch(f"/api/notifications/{first.id}/read", headers=headers)
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["read"] is True

    stored_first = asyncio.run(get_notification_by_id(first.id))
    assert stored_first is not None
    assert stored_first.read_at is not None

    unread_count_after_single_read = public_client.get("/api/notifications/unread-count", headers=headers)
    assert unread_count_after_single_read.status_code == 200
    assert unread_count_after_single_read.json()["count"] == initial_unread_count - 1

    mark_all_response = public_client.post("/api/notifications/mark-all-read", headers=headers)
    assert mark_all_response.status_code == 200
    assert mark_all_response.json()["updated"] >= 1

    stored_second = asyncio.run(get_notification_by_id(second.id))
    assert stored_second is not None
    assert stored_second.read_at is not None

    unread_after_mark_all = public_client.get("/api/notifications/unread-count", headers=headers)
    assert unread_after_mark_all.status_code == 200
    assert unread_after_mark_all.json()["count"] == 0


def test_project_dashboard_routes_persist_state(client):
    project = asyncio.run(
        create_project(
            name="Dashboard",
            description="Security portal",
            status=ProjectStatus.ACTIVE,
        )
    )
    asyncio.run(
        create_finding(
            project_id=project.id,
            title="SQL injection",
            severity=SeverityLevel.CRITICAL,
            status=FindingStatus.OPEN,
            cvss_score=9.8,
            cve_id="CVE-2024-0001",
            ai_risk_score=8.9,
            scanner="SonarQube",
            source="manual",
        )
    )
    asyncio.run(
        create_finding(
            project_id=project.id,
            title="Cross-site scripting",
            severity=SeverityLevel.HIGH,
            status=FindingStatus.IN_PROGRESS,
            cvss_score=7.5,
            cve_id="CVE-2024-0002",
            ai_risk_score=6.1,
            scanner="OWASP ZAP",
            source="manual",
        )
    )

    overview_response = client.get(f"/api/projects/{project.id}/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total"] == 2
    assert overview["critical"] == 1
    assert overview["high"] == 1

    findings_response = client.get(f"/api/projects/{project.id}/findings")
    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert len(findings) == 2
    assert {item["scanner"] for item in findings} == {"SonarQube", "OWASP ZAP"}

    pipeline_response = client.get(f"/api/projects/{project.id}/pipeline")
    assert pipeline_response.status_code == 200
    pipeline = pipeline_response.json()
    assert pipeline["summary"]["sast"]["status"] == "failed"
    assert pipeline["runs"][0]["status"] == "failed"
    assert pipeline["project_status"] == "active"

    settings_payload = {
        "jira_url": "https://example.atlassian.net",
        "project_key": "DASH",
        "api_token": "secret-token",
        "user_email": "security@example.com",
        "default_issue_type": "Bug",
        "auto_critical": True,
        "auto_high_ai": False,
    }
    settings_response = client.put(f"/api/projects/{project.id}/settings", json=settings_payload)
    assert settings_response.status_code == 200
    settings_body = settings_response.json()
    assert settings_body["configured"] is True
    assert settings_body["project_key"] == "DASH"

    stored_settings = asyncio.run(get_project_settings_by_project_id(project.id))
    assert stored_settings is not None
    assert stored_settings.project_key == "DASH"
    assert stored_settings.api_token == "secret-token"
    assert stored_settings.auto_high_ai is False

    jira_response = client.get(f"/api/projects/{project.id}/jira-tickets")
    assert jira_response.status_code == 200
    jira_tickets = jira_response.json()
    assert len(jira_tickets) == 2
    assert jira_tickets[0]["id"] == "DASH-001"

    scan_response = client.post(f"/api/projects/{project.id}/scan")
    assert scan_response.status_code == 200
    assert scan_response.json()["status"] == "queued"

    scanned_project = asyncio.run(get_project_by_id(project.id))
    assert scanned_project is not None
    assert scanned_project.status == ProjectStatus.SCANNING

    pipeline_after_scan = client.get(f"/api/projects/{project.id}/pipeline")
    assert pipeline_after_scan.status_code == 200
    assert pipeline_after_scan.json()["runs"][0]["status"] == "running"

    scan_notifications = client.get(
        "/api/notifications",
        params={"notification_type": "pipeline"},
    )
    assert scan_notifications.status_code == 200
    assert any(item["title"] == "Security scan queued" for item in scan_notifications.json())


def test_project_sync_imports_defectdojo_findings(client, monkeypatch):
    project = asyncio.run(
        create_project(
            name="Sync Dashboard",
            description="Project used to verify DefectDojo sync",
            status=ProjectStatus.SCANNING,
        )
    )

    raw_findings = [
        {
            "id": "dojo-1",
            "title": "Stored XSS",
            "description": "Reflected content can be stored in the database.",
            "severity": "Critical",
            "active": True,
            "cvss_score": 9.1,
            "scanner": "DefectDojo Import",
            "vulnerability_ids": [{"vulnerability_id": "CVE-2024-1234"}],
        }
    ]

    monkeypatch.setattr(defectdojo_service, "fetch_findings", lambda limit=100: raw_findings)
    monkeypatch.setattr(
        defectdojo_service,
        "enrich_findings",
        lambda findings, use_epss=True: [
            {
                **finding,
                "_epss_score": 0.61,
                "_epss_percentile": 0.93,
            }
            for finding in findings
        ],
    )

    response = client.post(f"/api/projects/{project.id}/sync", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["updated"] == 0
    assert body["imported_critical"] == 1
    assert body["total_imported"] == 1

    stored_project = asyncio.run(get_project_by_id(project.id))
    assert stored_project is not None
    assert stored_project.status == ProjectStatus.ACTIVE

    finding = asyncio.run(get_finding_by_external_id(project.id, "dojo-1"))
    assert finding is not None
    assert finding.title == "Stored XSS"
    assert finding.source == "defectdojo"
    assert finding.external_id == "dojo-1"
    assert finding.scanner == "DefectDojo Import"

    status_response = client.patch(f"/api/findings/{finding.id}/status", json={"status": "In Progress"})
    assert status_response.status_code == 200

    raw_findings[0].update(
        {
            "title": "Stored XSS updated upstream",
            "active": False,
            "updated": "2026-05-05T10:00:00Z",
        }
    )
    conflict_response = client.post(f"/api/projects/{project.id}/sync", params={"limit": 5})
    assert conflict_response.status_code == 200
    conflict_body = conflict_response.json()
    assert conflict_body["created"] == 0
    assert conflict_body["updated"] == 1
    assert conflict_body["conflicts"] == 1

    conflicted_finding = asyncio.run(get_finding_by_external_id(project.id, "dojo-1"))
    assert conflicted_finding is not None
    assert conflicted_finding.title == "Stored XSS updated upstream"
    assert conflicted_finding.status == FindingStatus.IN_PROGRESS
    assert conflicted_finding.sync_conflict is True
    conflict_events = asyncio.run(get_finding_events(conflicted_finding.id))
    assert any(event.event_type == "sync_conflict" for event in conflict_events)

    notifications_response = client.get(
        "/api/notifications",
        params={"notification_type": "pipeline"},
    )
    assert notifications_response.status_code == 200
    assert any(item["title"] == "Finding sync completed" for item in notifications_response.json())


def test_finding_routes_record_history_and_notifications(client):
    project = asyncio.run(create_project(name="Finding Dashboard", description="History checks"))
    finding = asyncio.run(
        create_finding(
            project_id=project.id,
            title="Prototype pollution",
            severity=SeverityLevel.MEDIUM,
            status=FindingStatus.OPEN,
            cvss_score=5.4,
            cve_id="CVE-2024-2222",
            ai_risk_score=4.2,
            scanner="Semgrep",
            source="manual",
        )
    )
    assignee = asyncio.run(
        create_user(
            email="assignee@example.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            name="Assignee",
            role="developer",
        )
    )

    status_response = client.patch(f"/api/findings/{finding.id}/status", json={"status": "In Progress"})
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"

    assignment_response = client.patch(f"/api/findings/{finding.id}/assign", json={"user_id": assignee.id})
    assert assignment_response.status_code == 200
    assert assignment_response.json()["assigned"] == assignee.id

    feedback_response = client.post(
        f"/api/findings/{finding.id}/feedback",
        json={"vote": "up", "comment": "The risk was confirmed and triaged."},
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["feedback"]["vote"] == "up"

    stored_finding = asyncio.run(get_finding_by_id(finding.id))
    assert stored_finding is not None
    assert stored_finding.status == FindingStatus.IN_PROGRESS
    assert stored_finding.assigned_to == assignee.id

    events = asyncio.run(get_finding_events(finding.id))
    assert [event.event_type for event in events] == ["status", "assignment", "feedback"]

    finding_notifications = client.get("/api/notifications", params={"notification_type": "finding"})
    assert finding_notifications.status_code == 200
    finding_notification_titles = {item["title"] for item in finding_notifications.json()}
    assert "Finding status updated" in finding_notification_titles
    assert "Finding assigned" in finding_notification_titles
