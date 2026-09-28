"""工作流领域异常。"""


class WorkflowError(Exception):
    """所有工作流领域异常的基类。"""


class IdempotencyConflictError(WorkflowError):
    """同一幂等键被用于不同的请求内容。"""


class WorkflowPersistenceError(WorkflowError):
    """工作流运行无法持久化。"""
