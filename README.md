# Enterprise AI Automation

用于企业自动化场景的后端服务原型。当前版本提供健康检查和工作流执行接口。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r fastapi/requirements.txt
uvicorn --app-dir fastapi main:app --reload
```

接口文档：<http://127.0.0.1:8000/docs>

## Docker 运行

```bash
docker build -t enterprise-fastapi:0.1 ./fastapi
docker run --rm --name enterprise-fastapi -p 8000:8000 enterprise-fastapi:0.1
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

工作流接口：

```bash
curl -X POST http://127.0.0.1:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"user_id":"HR001","task_type":"attendance","department":"生产部"}'
```
