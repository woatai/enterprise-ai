"""一次完整企业工作流运行的数据库模型。"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.workflow_step_run import WorkflowStepRun


class WorkflowRun(Base):
    """记录一次从接收到结束的完整业务运行。"""

    __tablename__ = "workflow_run"
    __table_args__ = (
        # 数据库约束是最后一道防线，避免绕过应用代码写入未知状态。
        CheckConstraint(
            "status IN ('accepted','running','succeeded','failed','cancelled','timed_out')",
            name="ck_workflow_run_status",
        ),
        UniqueConstraint("run_id", name="uq_workflow_run_run_id"),
        UniqueConstraint(
            "idempotency_key",
            name="uq_workflow_run_idempotency_key",
        ),
        Index("ix_workflow_run_status_created_at", "status", "created_at"),
        Index("ix_workflow_run_user_created_at", "user_id", "created_at"),
        Index("ix_workflow_run_n8n_execution_id", "n8n_execution_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    run_id: Mapped[str] = mapped_column(CHAR(36), nullable=False)
    n8n_execution_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="accepted",
        server_default="accepted",
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    steps: Mapped[list["WorkflowStepRun"]] = relationship(
        back_populates="workflow_run",
        lazy="selectin",
        order_by="WorkflowStepRun.id",
    )
