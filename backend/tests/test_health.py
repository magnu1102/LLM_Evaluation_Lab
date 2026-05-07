from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_shape():
    with patch("app.routes.health.db_ok", return_value=False):
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "db" in body
    assert "provider" in body
    assert "provider_configured" in body
