"""创建工作流运行表和步骤运行表。

Revision ID: 20260920_0001
Revises:
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "20260920_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 Day 1 需要的两张业务表及其约束和索引。"""

    # 先创建父表，步骤表的外键才能引用 workflow_run.id。
    op.create_table(
        "workflow_run",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("n8n_execution_id", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("input_data", mysql.JSON(), nullable=False),
        sa.Column("output_data", mysql.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="accepted",
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("finished_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('accepted','running','succeeded','failed','cancelled','timed_out')",
            name="ck_workflow_run_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_workflow_run_run_id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_workflow_run_idempotency_key",
        ),
    )
    op.create_index(
        "ix_workflow_run_n8n_execution_id",
        "workflow_run",
        ["n8n_execution_id"],
    )
    op.create_index(
        "ix_workflow_run_status_created_at",
        "workflow_run",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_workflow_run_user_created_at",
        "workflow_run",
        ["user_id", "created_at"],
    )

    op.create_table(
        "workflow_step_run",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workflow_run_id", sa.BigInteger(), nullable=False),
        sa.Column("step_name", sa.String(length=100), nullable=False),
        sa.Column(
            "attempt_no",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("request_data", mysql.JSON(), nullable=True),
        sa.Column("response_data", mysql.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="accepted",
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("finished_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('accepted','running','succeeded','failed','cancelled','timed_out')",
            name="ck_workflow_step_run_status",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_run_id"],
            ["workflow_run.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_run_id",
            "step_name",
            "attempt_no",
            name="uq_workflow_step_attempt",
        ),
    )
    op.create_index(
        "ix_workflow_step_run_id_created_at",
        "workflow_step_run",
        ["workflow_run_id", "created_at"],
    )


def downgrade() -> None:
    """按外键依赖的相反顺序删除步骤表和运行表。"""

    op.drop_index(
        "ix_workflow_step_run_id_created_at",
        table_name="workflow_step_run",
    )
    op.drop_table("workflow_step_run")
    op.drop_index(
        "ix_workflow_run_user_created_at",
        table_name="workflow_run",
    )
    op.drop_index(
        "ix_workflow_run_status_created_at",
        table_name="workflow_run",
    )
    op.drop_index(
        "ix_workflow_run_n8n_execution_id",
        table_name="workflow_run",
    )
    op.drop_table("workflow_run")
