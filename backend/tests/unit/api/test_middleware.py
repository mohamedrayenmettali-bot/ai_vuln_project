from __future__ import annotations

from backend.settings import PROCESS_TIME_HEADER, REQUEST_ID_HEADER


def test_request_headers_are_attached(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert PROCESS_TIME_HEADER in response.headers


def test_request_id_is_echoed(client):
    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "req-123"})
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
