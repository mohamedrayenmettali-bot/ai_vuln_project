from __future__ import annotations

import pytest

from backend.settings import EPSS_BATCH_MAX_CVES, PREDICT_BATCH_MAX_FINDINGS


@pytest.mark.parametrize("path", ["/api/predict/batch", "/api/v1/predict/batch"])
def test_predict_batch_rejects_more_than_max_findings(client, path):
    body = {
        "findings": [{"description": "item"} for _ in range(PREDICT_BATCH_MAX_FINDINGS + 1)]
    }
    response = client.post(path, json=body)
    assert response.status_code == 422


@pytest.mark.parametrize("path", ["/api/epss/batch", "/api/v1/epss/batch"])
def test_epss_batch_rejects_more_than_max_cves(client, path):
    body = {
        "cve_ids": [f"CVE-2024-{index:04d}" for index in range(EPSS_BATCH_MAX_CVES + 1)]
    }
    response = client.post(path, json=body)
    assert response.status_code == 422
