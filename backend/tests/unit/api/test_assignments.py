from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from backend.tests.auth_helpers import TEST_PASSWORD
from backend.tests.support import create_project, create_user


def _register_and_login(client, *, role: str = "developer") -> tuple[str, dict[str, str]]:
    """Register a fresh user with the given role and return (user_id, auth_headers)."""
    email = f"test-{uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": TEST_PASSWORD, "confirmPassword": TEST_PASSWORD, "role": role},
    )
    assert reg_resp.status_code in (200, 201)
    login_resp = client.post("/api/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]
    return user_id, {"Authorization": f"Bearer {token}"}


def _admin_headers(client) -> dict[str, str]:
    """Return headers for the already-authenticated admin client."""
    return dict(client.headers)


# ---------------------------------------------------------------------------
# Admin assignment endpoints
# ---------------------------------------------------------------------------


def test_admin_can_assign_user_to_project(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, _dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Assign Test"))

    resp = public_client.post(
        f"/api/admin/users/{dev_id}/projects/{project.id}",
        headers=admin_hdrs,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == dev_id
    assert body["project_id"] == project.id


def test_admin_cannot_assign_same_user_twice(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, _dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Dupe Assign Test"))

    public_client.post(f"/api/admin/users/{dev_id}/projects/{project.id}", headers=admin_hdrs)
    resp = public_client.post(
        f"/api/admin/users/{dev_id}/projects/{project.id}",
        headers=admin_hdrs,
    )
    assert resp.status_code == 409


def test_non_admin_cannot_use_assignment_endpoint(public_client):
    _admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Forbidden Assign Test"))

    resp = public_client.post(
        f"/api/admin/users/{dev_id}/projects/{project.id}",
        headers=dev_hdrs,
    )
    assert resp.status_code == 403


def test_admin_can_remove_user_from_project(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, _dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Remove Assign Test"))

    public_client.post(f"/api/admin/users/{dev_id}/projects/{project.id}", headers=admin_hdrs)
    resp = public_client.delete(
        f"/api/admin/users/{dev_id}/projects/{project.id}",
        headers=admin_hdrs,
    )
    assert resp.status_code == 204


def test_admin_can_list_projects_for_user(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, _dev_hdrs = _register_and_login(public_client, role="developer")
    p1 = asyncio.run(create_project(name="List Project A"))
    p2 = asyncio.run(create_project(name="List Project B"))

    public_client.post(f"/api/admin/users/{dev_id}/projects/{p1.id}", headers=admin_hdrs)
    public_client.post(f"/api/admin/users/{dev_id}/projects/{p2.id}", headers=admin_hdrs)

    resp = public_client.get(f"/api/admin/users/{dev_id}/projects", headers=admin_hdrs)
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()}
    assert p1.id in ids
    assert p2.id in ids


def test_admin_can_list_users_for_project(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, _dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Users For Project"))

    public_client.post(f"/api/admin/users/{dev_id}/projects/{project.id}", headers=admin_hdrs)

    resp = public_client.get(f"/api/admin/projects/{project.id}/users", headers=admin_hdrs)
    assert resp.status_code == 200
    ids = {u["id"] for u in resp.json()}
    assert dev_id in ids


# ---------------------------------------------------------------------------
# Access control on /projects
# ---------------------------------------------------------------------------


def test_non_admin_only_sees_assigned_projects(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, dev_hdrs = _register_and_login(public_client, role="developer")
    visible = asyncio.run(create_project(name="Visible Project"))
    _hidden = asyncio.run(create_project(name="Hidden Project"))

    # Assign developer only to the first project.
    public_client.post(f"/api/admin/users/{dev_id}/projects/{visible.id}", headers=admin_hdrs)

    resp = public_client.get("/api/projects/", headers=dev_hdrs)
    assert resp.status_code == 200
    returned_ids = {p["id"] for p in resp.json()}
    assert visible.id in returned_ids
    assert _hidden.id not in returned_ids


def test_admin_sees_all_projects(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    p1 = asyncio.run(create_project(name="Admin All A"))
    p2 = asyncio.run(create_project(name="Admin All B"))

    resp = public_client.get("/api/projects/", headers=admin_hdrs)
    assert resp.status_code == 200
    ids = {p["id"] for p in resp.json()}
    assert p1.id in ids
    assert p2.id in ids


def test_non_admin_cannot_access_unassigned_project(public_client):
    _admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Forbidden Project"))

    resp = public_client.get(f"/api/projects/{project.id}", headers=dev_hdrs)
    assert resp.status_code == 403


def test_non_admin_can_access_assigned_project(public_client):
    admin_id, admin_hdrs = _register_and_login(public_client, role="admin")
    dev_id, dev_hdrs = _register_and_login(public_client, role="developer")
    project = asyncio.run(create_project(name="Permitted Project"))

    public_client.post(f"/api/admin/users/{dev_id}/projects/{project.id}", headers=admin_hdrs)

    resp = public_client.get(f"/api/projects/{project.id}", headers=dev_hdrs)
    assert resp.status_code == 200
    assert resp.json()["id"] == project.id


# ---------------------------------------------------------------------------
# Sync notifications on login
# ---------------------------------------------------------------------------


def test_login_creates_sync_notifications(public_client):
    """Login should fire a background sync that produces sync-type notifications."""
    email = f"sync-test-{uuid4().hex[:8]}@example.com"
    public_client.post(
        "/api/auth/register",
        json={"name": "Sync Test", "email": email, "password": TEST_PASSWORD, "confirmPassword": TEST_PASSWORD, "role": "developer"},
    )
    login_resp = public_client.post("/api/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    hdrs = {"Authorization": f"Bearer {token}"}

    # Fetch sync-type notifications (background task may have run by now).
    notif_resp = public_client.get("/api/notifications", headers=hdrs, params={"notification_type": "sync"})
    assert notif_resp.status_code == 200
    sync_notifications = notif_resp.json()
    # At minimum the "sync started" notification should exist.
    assert len(sync_notifications) >= 1
    titles = {n["title"] for n in sync_notifications}
    assert "DefectDojo sync started" in titles
