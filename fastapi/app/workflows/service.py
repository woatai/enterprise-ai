"""工作流运行的业务规则和事务处理。"""

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import WorkflowRun
from app.workflows.exceptions import (
    IdempotencyConflictError,
    WorkflowPersistenceError,
)
from app.workflows.schemas import WorkflowRequest


@dataclass(frozen=True)
class CreateWorkflowResult:
    """创建工作流的结果，并标记是否属于幂等重放。"""

    workflow_run: WorkflowRun
    replayed: bool


def _get_by_idempotency_key(
    db: Session,
    idempotency_key: str,
) -> WorkflowRun | None:
    """根据幂等键查询已存在的工作流运行。"""

    return db.scalar(
        select(WorkflowRun).where(
            WorkflowRun.idempotency_key == idempotency_key
        )
    )


def _replay_or_raise_conflict(
    existing: WorkflowRun,
    request_data: dict[str, Any],
) -> CreateWorkflowResult:
    """相同请求返回原记录，不同请求报告幂等冲突。"""

    if existing.input_data != request_data:
        raise IdempotencyConflictError(
            "Idempotency-Key has already been used for another request"
        )

    return CreateWorkflowResult(workflow_run=existing, replayed=True)


def create_workflow_run(
    db: Session,
    data: WorkflowRequest,
    idempotency_key: str,
) -> CreateWorkflowResult:
    """创建工作流运行，并保证同键同请求可以安全重放。

    唯一约束负责阻止并发重复写入。如果两个相同请求同时通过首次查询，
    后提交的请求会在冲突回滚后重新查询，并返回先创建的记录。
    """

    request_data = data.model_dump(mode="json")

    try:
        existing = _get_by_idempotency_key(db, idempotency_key)
        if existing is not None:
            return _replay_or_raise_conflict(existing, request_data)

        workflow_run = WorkflowRun(
            run_id=str(uuid.uuid4()),
            idempotency_key=idempotency_key,
            user_id=data.user_id,
            task_type=data.task_type,
            department=data.department,
            input_data=request_data,
            status="accepted",
        )
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
    except IntegrityError as exc:
        db.rollback()
        try:
            concurrent_existing = _get_by_idempotency_key(db, idempotency_key)
        except SQLAlchemyError as lookup_exc:
            raise WorkflowPersistenceError(
                "Failed to persist workflow run"
            ) from lookup_exc

        if concurrent_existing is None:
            raise WorkflowPersistenceError(
                "Failed to persist workflow run"
            ) from exc

        return _replay_or_raise_conflict(concurrent_existing, request_data)
    except SQLAlchemyError as exc:
        db.rollback()
        raise WorkflowPersistenceError(
            "Failed to persist workflow run"
        ) from exc

    return CreateWorkflowResult(workflow_run=workflow_run, replayed=False)
