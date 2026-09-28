"""测试工作流业务时使用的轻量数据库替身。"""

from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.models import WorkflowRun


class FakeSession:
    """只实现当前工作流 Service 用到的 Session 行为。"""

    def __init__(
        self,
        *,
        existing: WorkflowRun | None = None,
        scalar_results: list[WorkflowRun | None] | None = None,
        commit_error: SQLAlchemyError | None = None,
    ) -> None:
        self.existing = existing
        self.scalar_results = iter(scalar_results) if scalar_results else None
        self.commit_error = commit_error
        self.added: list[WorkflowRun] = []
        self.scalar_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def scalar(self, _statement):
        self.scalar_count += 1
        if self.scalar_results is not None:
            return next(self.scalar_results)
        return self.existing

    def add(self, workflow_run: WorkflowRun) -> None:
        self.added.append(workflow_run)

    def commit(self) -> None:
        self.commit_count += 1
        if self.commit_error is not None:
            raise self.commit_error

    @staticmethod
    def refresh(workflow_run: WorkflowRun) -> None:
        workflow_run.id = 1
        workflow_run.created_at = datetime(2026, 9, 21, 10, 0, 0)

    def rollback(self) -> None:
        self.rollback_count += 1


def build_workflow_run(
    request_data: dict[str, str],
    *,
    run_id: str = "01f5f919-0899-4c48-8cc5-8275f7debc40",
    idempotency_key: str = "attendance-HR001-20260921",
) -> WorkflowRun:
    """构造一个已经存在的工作流运行。"""

    workflow_run = WorkflowRun(
        run_id=run_id,
        idempotency_key=idempotency_key,
        user_id=request_data["user_id"],
        task_type=request_data["task_type"],
        department=request_data["department"],
        input_data=request_data,
        status="accepted",
    )
    workflow_run.created_at = datetime(2026, 9, 21, 10, 0, 0)
    return workflow_run
