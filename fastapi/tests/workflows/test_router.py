"""工作流 HTTP 路由测试。"""

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app
from tests.fakes import FakeSession, build_workflow_run


def make_client(db: FakeSession) -> TestClient:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_workflow_run_persists_orm_object(request_data) -> None:
    db = FakeSession()
    client = make_client(db)

    try:
        response = client.post(
            "/workflow/run",
            json=request_data,
            headers={"Idempotency-Key": "attendance-HR001-20260921"},
        )
    finally:
        app.dependency_overrides.clear()
        client.close()

    assert response.status_code == 201
    assert response.json()["status"] == "accepted"
    assert response.json()["created_at"] == "2026-09-21T10:00:00"
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert len(db.added) == 1
    assert db.added[0].input_data == request_data
    assert db.added[0].idempotency_key == "attendance-HR001-20260921"


def test_same_idempotency_key_replays_existing_run(request_data) -> None:
    existing = build_workflow_run(request_data)
    db = FakeSession(existing=existing)
    client = make_client(db)

    try:
        response = client.post(
            "/workflow/run",
            json=request_data,
            headers={"Idempotency-Key": "attendance-HR001-20260921"},
        )
    finally:
        app.dependency_overrides.clear()
        client.close()

    assert response.status_code == 200
    assert response.headers["Idempotent-Replay"] == "true"
    assert response.json()["run_id"] == existing.run_id
    assert db.added == []
    assert db.commit_count == 0


def test_same_idempotency_key_rejects_different_request(request_data) -> None:
    existing = build_workflow_run(request_data)
    db = FakeSession(existing=existing)
    client = make_client(db)

    try:
        response = client.post(
            "/workflow/run",
            json=request_data | {"department": "研发部"},
            headers={"Idempotency-Key": "attendance-HR001-20260921"},
        )
    finally:
        app.dependency_overrides.clear()
        client.close()

    assert response.status_code == 409
    assert db.added == []
    assert db.commit_count == 0


def test_database_error_returns_server_error(request_data) -> None:
    db = FakeSession(commit_error=SQLAlchemyError("database unavailable"))
    client = make_client(db)

    try:
        response = client.post(
            "/workflow/run",
            json=request_data,
            headers={"Idempotency-Key": "attendance-HR001-20260921"},
        )
    finally:
        app.dependency_overrides.clear()
        client.close()

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to persist workflow run"
    assert db.commit_count == 1
    assert db.rollback_count == 1


def test_missing_idempotency_key_is_rejected_before_writing(request_data) -> None:
    db = FakeSession()
    client = make_client(db)

    try:
        response = client.post("/workflow/run", json=request_data)
    finally:
        app.dependency_overrides.clear()
        client.close()

    assert response.status_code == 422
    assert db.added == []
    assert db.commit_count == 0
