from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

TEST_PASSWORD = "SecurePass123!"
TEST_ROLE = "admin"


def bootstrap_authenticated_client(client: TestClient, *, email: str | None = None, role: str = TEST_ROLE) -> dict[str, str]:
    email = email or f"pytest-{uuid4().hex[:10]}@example.com"
    register_payload = {
        "name": "Pytest User",
        "email": email,
        "password": TEST_PASSWORD,
        "confirmPassword": TEST_PASSWORD,
        "role": role,
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    if register_response.status_code not in (200, 201, 409):
        register_response.raise_for_status()

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    login_response.raise_for_status()

    token = login_response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return {"email": email, "token": token}
