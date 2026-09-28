"""FastAPI 应用入口。"""

from fastapi import FastAPI

from app.workflows.router import router as workflow_router


app = FastAPI(title="Enterprise AI Automation API", version="0.2.0")
app.include_router(workflow_router)


@app.get("/health")
def health():
    """返回 FastAPI 进程的基础健康状态。"""

    return {"status": "ok"}
