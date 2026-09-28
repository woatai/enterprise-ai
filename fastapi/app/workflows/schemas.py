"""工作流接口的 Pydantic 输入输出模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkflowRequest(BaseModel):
    """创建一次工作流运行所需的业务输入。"""

    user_id: str = Field(min_length=1, max_length=100)
    task_type: str = Field(min_length=1, max_length=100)
    department: str = Field(min_length=1, max_length=100)


class WorkflowRunResponse(BaseModel):
    """工作流运行成功落库后的响应。"""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    user_id: str
    task_type: str
    department: str
    status: str
    created_at: datetime
