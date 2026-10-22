import os

# Point at a DB that does not exist so unit tests never need Postgres.
os.environ["DATABASE_URL"] = "postgresql://app:app@127.0.0.1:1/none"
os.environ["DB_POOL_TIMEOUT"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_does_not_need_db():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_ready_returns_503_when_db_down():
    with TestClient(app) as client:
        r = client.get("/ready")
        assert r.status_code == 503


def test_metrics_exposed():
    with TestClient(app) as client:
        client.get("/health")
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "http_requests_total" in r.text
