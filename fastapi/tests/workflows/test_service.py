"""工作流 Service 的业务规则测试。"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.workflows.exceptions import (
    IdempotencyConflictError,
    WorkflowPersistenceError,
)
from app.workflows.schemas import WorkflowRequest
from app.workflows.service import create_workflow_run
from tests.fakes import FakeSession, build_workflow_run


def duplicate_key_error() -> IntegrityError:
    return IntegrityError(
        "INSERT INTO workflow_run ...",
        {},
        Exception("duplicate key"),
    )


def test_concurrent_same_request_replays_after_unique_conflict(request_data) -> None:
    existing = build_workflow_run(request_data)
    db = FakeSession(
        scalar_results=[None, existing],
        commit_error=duplicate_key_error(),
    )

    result = create_workflow_run(
        db,
        WorkflowRequest(**request_data),
        "attendance-HR001-20260921",
    )

    assert result.replayed is True
    assert result.workflow_run is existing
    assert db.scalar_count == 2
    assert db.commit_count == 1
    assert db.rollback_count == 1


def test_concurrent_different_request_remains_conflict(request_data) -> None:
    existing_request = request_data | {"department": "研发部"}
    existing = build_workflow_run(existing_request)
    db = FakeSession(
        scalar_results=[None, existing],
        commit_error=duplicate_key_error(),
    )

    with pytest.raises(IdempotencyConflictError):
        create_workflow_run(
            db,
            WorkflowRequest(**request_data),
            "attendance-HR001-20260921",
        )

    assert db.scalar_count == 2
    assert db.commit_count == 1
    assert db.rollback_count == 1


def test_unrelated_integrity_error_is_persistence_error(request_data) -> None:
    db = FakeSession(
        scalar_results=[None, None],
        commit_error=duplicate_key_error(),
    )

    with pytest.raises(WorkflowPersistenceError):
        create_workflow_run(
            db,
            WorkflowRequest(**request_data),
            "attendance-HR001-20260921",
        )

    assert db.scalar_count == 2
    assert db.rollback_count == 1
