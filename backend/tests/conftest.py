from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.tests.auth_helpers import bootstrap_authenticated_client
from backend.tests.support import (
    bootstrap_test_schema,
    configure_test_database,
    patch_predictor_stub,
    teardown_test_schema,
)
from app.services.predictor import PredictorService


@pytest.fixture
def app_environment(tmp_path):
    configure_test_database(tmp_path)
    patch_predictor_stub()
    asyncio.run(bootstrap_test_schema())
    try:
        yield
    finally:
        asyncio.run(teardown_test_schema())
        PredictorService._instance = None  # type: ignore[attr-defined]


@pytest.fixture
def public_client(app_environment) -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(app_environment) -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        bootstrap_authenticated_client(test_client)
        yield test_client
