"""
Integration tests for the Bot Detector REST API (api.py).

These tests are written BEFORE api.py exists (Wave 1 test-first contract).
They will fail with ImportError until Wave 2 implements api.py.

Fixtures:
    client: FastAPI TestClient with a minimal trained system loaded from a temp joblib file.
            Patches MODEL_PATH env var so api.py loads the test system, not a real trained_system.joblib.
"""

import importlib

import joblib
import pytest
from fastapi.testclient import TestClient


VALID_PAYLOAD = {
    "account_id": "test_001",
    "username": "testuser",
    "submission_num": 10.0,
    "comment_num_1": 5.0,
    "comment_num_2": 3.0,
    "subreddit_list": ["news", "science"],
    "profile": "A regular user who posts about news",
    "messages": [
        {"text": "hello world this is a test message", "ts": 1700000000.0},
        {"text": "another message for testing", "ts": 1700003600.0},
    ],
}


@pytest.fixture
def client(minimal_system, tmp_path, monkeypatch):
    """
    Build a FastAPI TestClient backed by a minimal trained system.

    Steps:
      1. Serialize the minimal_system to a temp joblib file.
      2. Patch MODEL_PATH env var so api.py reads from the temp file.
      3. Import (or reload) the api module AFTER patching so the env var
         is already set when the module-level MODEL_PATH = os.environ.get(...)
         line executes.
      4. Return a TestClient wrapping the app with lifespan events triggered.
    """
    system, S2, edges_S2, nodes_total = minimal_system

    model_path = tmp_path / "test_system.joblib"
    joblib.dump(system, model_path)

    monkeypatch.setenv("MODEL_PATH", str(model_path))

    import api as api_module
    importlib.reload(api_module)
    from api import app

    return TestClient(app)


def test_predict_returns_200(client):
    """POST /predict with a valid payload must return HTTP 200 with p_final and label."""
    response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "p_final" in data
    assert "label" in data


def test_predict_output_range(client):
    """p_final must be in [0.0, 1.0]; label must be 0 or 1 and consistent with p_final."""
    response = client.post("/predict", json=VALID_PAYLOAD)
    data = response.json()
    assert 0.0 <= data["p_final"] <= 1.0
    assert data["label"] in (0, 1)
    assert data["label"] == int(data["p_final"] >= 0.5)


def test_startup_loads_system(client):
    """The app.state.system must be loaded at startup and have a stage1 attribute."""
    assert client.app.state.system is not None
    assert hasattr(client.app.state.system, "stage1")


def test_missing_account_id_returns_422(client):
    """A request body missing the required account_id field must return HTTP 422."""
    response = client.post("/predict", json={"username": "noaccountid"})
    assert response.status_code == 422


def test_wrong_type_returns_422(client):
    """A request body with a wrong type for submission_num (string) must return HTTP 422."""
    response = client.post(
        "/predict",
        json={"account_id": 123, "username": "test", "submission_num": "not_a_number"},
    )
    assert response.status_code == 422
