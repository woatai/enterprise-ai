"""工作流领域的 HTTP 路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import WorkflowRun
from app.workflows.exceptions import (
    IdempotencyConflictError,
    WorkflowPersistenceError,
)
from app.workflows.schemas import WorkflowRequest, WorkflowRunResponse
from app.workflows.service import create_workflow_run


router = APIRouter(tags=["workflow"])

DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


@router.post(
    "/workflow/run",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_workflow(
    data: WorkflowRequest,
    response: Response,
    idempotency_key: IdempotencyKey,
    db: DbSession,
) -> WorkflowRun:
    """创建并持久化一次工作流运行。"""

    try:
        result = create_workflow_run(db, data, idempotency_key)
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except WorkflowPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if result.replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replay"] = "true"

    return result.workflow_run
