"""测试共享夹具。"""

import pytest


@pytest.fixture
def request_data() -> dict[str, str]:
    """返回一份有效的工作流请求。"""

    return {
        "user_id": "HR001",
        "task_type": "attendance",
        "department": "生产部",
    }
