from __future__ import annotations


def test_public_smoke_routes(public_client):
    root_response = public_client.get("/")
    health_response = public_client.get("/health")
    api_health_response = public_client.get("/api/v1/health")

    assert root_response.status_code == 200
    assert health_response.status_code == 200
    assert api_health_response.status_code == 200
    assert root_response.json()["service"] == "AI Vulnerability Risk API"
    assert health_response.json()["status"] == "ok"
    assert api_health_response.json()["status"] == "ok"


def test_authenticated_smoke_routes(client):
    predict_response = client.post(
        "/predict",
        json={
            "description": "buffer overflow",
            "cve_id": "CVE-2024-1234",
            "epss_score": 0.2,
            "epss_percentile": 0.8,
        },
    )
    model_response = client.get("/model/info")

    assert predict_response.status_code == 200
    assert model_response.status_code == 200

    body = predict_response.json()
    assert body["cve_id"] == "CVE-2024-1234"
    assert 0.0 <= body["risk_score"] <= 10.0
    assert isinstance(body["risk_score"], (float, int))
    assert set(body["base_predictions"].keys()) == {"xgb", "lgbm", "cat", "mlp", "knn"}
    assert model_response.json()["model_path"].endswith("ai_risk_model.pkl")
