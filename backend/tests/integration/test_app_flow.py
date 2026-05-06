from __future__ import annotations


def test_root_and_health_flow(client):
    root_response = client.get("/")
    health_response = client.get("/health")
    api_health_response = client.get("/api/v1/health")

    assert root_response.status_code == 200
    assert health_response.status_code == 200
    assert api_health_response.status_code == 200
    assert root_response.json()["service"] == "AI Vulnerability Risk API"
    assert health_response.json()["status"] == "ok"
    assert api_health_response.json()["status"] == "ok"


def test_prediction_flow(client):
    response = client.post(
        "/api/v1/predict",
        json={
            "description": "buffer overflow",
            "cve_id": "CVE-2024-1234",
            "epss_score": 0.2,
            "epss_percentile": 0.8,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cve_id"] == "CVE-2024-1234"
    assert 0.0 <= body["risk_score"] <= 10.0
    assert isinstance(body["risk_score"], (float, int))
    assert set(body["base_predictions"].keys()) == {"xgb", "lgbm", "cat", "mlp", "knn"}


def test_model_info_flow(client):
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    assert response.json()["model_path"].endswith("ai_risk_model.pkl")
