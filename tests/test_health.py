import pytest
from fastapi.testclient import TestClient

from estoque_doacoes.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"]["foreign_keys"] is True
    assert body["db"]["journal_mode"] == "wal"
