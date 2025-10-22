import os
from importlib import import_module
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path):
    test_db = tmp_path / "test_wagonee.db"
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass

    os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
    app = import_module("app.main").app
    with TestClient(app) as c:
        yield c


def test_rfc7807_on_not_found(client):
    r = client.get(
        "/workouts/a1b2c3d4-e5f6-7890-1234-567890abcdef",
        headers={"X-Forwarded-For": "127.0.0.2"},
    )
    assert r.status_code == 404
    data = r.json()
    assert "type" in data and "title" in data and "status" in data and "detail" in data
    assert "correlation_id" in data


def test_validation_error_returns_problem(client):
    long_note = "x" * 2000
    r = client.post(
        "/workouts/",
        json={"workout_date": "2025-09-25", "note": long_note},
        headers={"X-Forwarded-For": "127.0.0.3"},
    )
    assert r.status_code == 422
    data = r.json()
    assert data.get("title") == "Validation Error"
    assert "correlation_id" in data
