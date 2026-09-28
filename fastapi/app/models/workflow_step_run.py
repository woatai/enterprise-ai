"""企业工作流中单个步骤及其重试记录的数据库模型。"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import DATETIME, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.workflow_run import WorkflowRun


class WorkflowStepRun(Base):
    """记录一次工作流步骤执行，包括每一次重试。"""

    __tablename__ = "workflow_step_run"
    __table_args__ = (
        CheckConstraint(
            "status IN ('accepted','running','succeeded','failed','cancelled','timed_out')",
            name="ck_workflow_step_run_status",
        ),
        # 同一步骤的每次 attempt_no 只能出现一次，防止重复记录同一次重试。
        UniqueConstraint(
            "workflow_run_id",
            "step_name",
            "attempt_no",
            name="uq_workflow_step_attempt",
        ),
        Index(
            "ix_workflow_step_run_id_created_at",
            "workflow_run_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    workflow_run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_run.id", ondelete="RESTRICT"),
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attempt_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    request_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="accepted",
        server_default="accepted",
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="steps")
