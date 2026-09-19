from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI(title="Enterprise AI Automation API", version="0.1.0")


class WorkflowRequest(BaseModel):
    user_id: str
    task_type: str
    department: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/workflow/run")
def run_workflow(data: WorkflowRequest):

    run_id = str(uuid.uuid4())

    return {
        "run_id": run_id,
        "user_id": data.user_id,
        "task_type": data.task_type,
        "department": data.department,
        "status": "success",
    }
