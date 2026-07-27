from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.style_api import app


def test_style_experiment_submit_and_retrieve(monkeypatch, tmp_path):
    monkeypatch.setenv("HCB_STYLE_EXPERIMENT_ROOT", str(tmp_path))
    client = TestClient(app)
    payload = {
        "experiment_id": "API-ACCOM-001",
        "human_baseline": "Direct claim. Brief wording.",
        "model_baseline": "Consider the broader context: several interacting possibilities may matter?",
        "human_revised": "Direct claim with context: several possibilities matter.",
        "model_followup": "Several possibilities matter. Direct claim with context.",
        "minimum_identity_retention": 0.4,
    }

    created = client.post("/v1/interoperability/style-experiments/accommodation", json=payload)
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "PASS"
    assert body["governance"]["verified_model_origin_claim"] is False
    assert body["governance"]["maximum_claim"] == "observed_feature_convergence"

    fetched = client.get("/v1/interoperability/style-experiments/API-ACCOM-001")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_style_experiment_ids_are_immutable(monkeypatch, tmp_path):
    monkeypatch.setenv("HCB_STYLE_EXPERIMENT_ROOT", str(tmp_path))
    client = TestClient(app)
    payload = {
        "experiment_id": "API-IMMUTABLE-001",
        "human_baseline": "Human baseline.",
        "model_baseline": "Model baseline with a longer construction.",
        "human_revised": "Human revised construction.",
        "model_followup": "Model revised construction.",
        "minimum_identity_retention": 0.5,
    }
    assert client.post("/v1/interoperability/style-experiments/accommodation", json=payload).status_code == 200
    duplicate = client.post("/v1/interoperability/style-experiments/accommodation", json=payload)
    assert duplicate.status_code == 409


def test_style_experiment_rejects_path_traversal(monkeypatch, tmp_path):
    monkeypatch.setenv("HCB_STYLE_EXPERIMENT_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/v1/interoperability/style-experiments/%2E%2E%2Fsecret")
    assert response.status_code in {400, 404}


def test_style_api_health_declares_claim_boundary():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["origin_attribution"] is False
