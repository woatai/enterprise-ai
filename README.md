# Enterprise AI Automation

用于企业自动化场景的后端服务原型。当前版本已经完成通用工作流请求的接收、幂等判断和运行记录落库；电商运营日报与异常处置闭环尚未进入功能实现阶段。

## 当前完成情况

截至 2026-09-30，项目处于“后端基础设施和通用工作流入口完成，电商 V1 业务功能待开发”阶段。当前的 `POST /workflow/run` 只创建一条状态为 `accepted` 的工作流运行记录，表示请求已经接收并保存，不表示工作流已经执行完成。

当前主流程：

```text
POST /workflow/run
    → FastAPI 校验请求体和 Idempotency-Key
    → Service 查询幂等键并判断新建、重放或冲突
    → SQLAlchemy 创建并提交 WorkflowRun
    → MySQL 保存 workflow_run 记录
    → 返回 HTTP 201、200、409 或 500
```

| 模块 | 状态 | 当前结果 |
| --- | --- | --- |
| 电商运营日报与异常处置 V1 需求 | 已实现 | [需求文档](docs/ecommerce-operations-requirements.md)已经定义业务范围、数据合同、指标、异常规则、人工审核、通知和验收标准 |
| FastAPI 应用基础 | 已验证 | 已提供 `GET /health` 和 `POST /workflow/run`，应用版本为 `0.2.0` |
| 工作流运行记录落库 | 已验证 | 首次请求创建 `accepted` 记录；同键同请求返回原记录；同键不同请求返回冲突 |
| 幂等与异常处理 | 已验证 | 已覆盖正常创建、重复请求、并发唯一约束冲突、缺少幂等键和数据库异常 |
| MySQL 与 Alembic | 已验证 | MySQL 8.4 容器健康；数据库位于 `20260920_0001 (head)`；`alembic check` 无待生成迁移 |
| FastAPI 与 MySQL Compose | 已验证 | API 镜像、健康检查、数据库依赖和 `enterprise-shared` 外部网络已配置；本机 Compose 启动、迁移、HTTP 写入和数据库记录已验证 |
| `workflow_run`、`workflow_step_run` 表 | 已实现 | 表、ORM 模型、约束和索引已经建立；当前接口只写入 `workflow_run` |
| 自动化测试 | 已验证 | 2026-09-30 执行测试共 8 个通过；当前测试使用 `FakeSession`，真实 MySQL 自动化集成测试仍待补充 |
| Excel 导入、清洗、指标和异常规则 | 计划中 | 已定义 V1 需求，尚无业务实现代码 |
| AI 日报、人工审核和异常任务 | 计划中 | 已定义输入输出和状态要求，尚未实现 |
| n8n 通知与回调 | 计划中 | 数据模型预留了相关字段，尚未连接 n8n |
| 端到端业务演示与验收 | 计划中 | 需要在上述业务功能完成后实施 |

下一阶段按照 V1 需求文档推进：先实现 Excel 数据导入、校验和版本化，再完成指标、基线与异常规则，之后接入 AI 日报、人工审核、异常任务和 n8n 通知。

## 项目结构

```text
.
├── .env.example             # 环境变量模板
├── compose.yml              # FastAPI、MySQL 和共享网络配置
├── compose.local.yml        # Mac 本机 MySQL 端口映射
├── README.md
└── fastapi/
    ├── Dockerfile           # API 镜像构建
    ├── requirements.txt     # Python 依赖
    ├── alembic.ini          # Alembic 配置
    ├── app/
    │   ├── main.py          # FastAPI 入口和健康检查
    │   ├── core/config.py   # 环境变量与数据库连接配置
    │   ├── db/              # SQLAlchemy 基类与会话
    │   ├── models/          # 工作流运行和步骤的数据模型
    │   └── workflows/       # 工作流接口、请求模型和业务逻辑
    ├── migrations/          # Alembic 迁移环境与版本脚本
    └── tests/               # 工作流接口和业务逻辑测试
```

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r fastapi/requirements.txt
uvicorn --app-dir fastapi app.main:app --reload
```

接口文档：<http://127.0.0.1:8000/docs>

## Docker Compose 运行

复制环境变量模板并替换示例密码：

```bash
cp .env.example .env
```

首次运行前创建供 FastAPI 与外部 n8n Compose 共用的网络：

```bash
docker network create enterprise-shared
```

如果网络已经存在，Docker 会提示已存在，不需要重复创建。

启动 MySQL、构建 FastAPI 镜像并执行迁移：

```bash
docker compose up -d --wait mysql
docker compose build api
docker compose run --rm api alembic -c alembic.ini upgrade head
docker compose up -d api
docker compose ps
```

Compose 内部强制让 API 使用 `mysql:3306` 连接数据库；根目录 `.env` 中的
`MYSQL_HOST=127.0.0.1` 仍可供宿主机直接运行 Uvicorn 时使用。API 的 8000 端口
只映射到宿主机 `127.0.0.1`，不需要在云安全组中向公网开放。

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

工作流接口：

```bash
curl -X POST http://127.0.0.1:8000/workflow/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: attendance-HR001-20260921" \
  -d '{"user_id":"HR001","task_type":"attendance","department":"生产部"}'
```

首次成功创建返回 HTTP 201 和 `accepted` 状态。同一幂等键与相同请求再次调用时
返回原记录、HTTP 200，并附带 `Idempotent-Replay: true` 响应头；同一幂等键不能
用于不同请求。

### 连接已有 n8n

n8n 位于另一份 Compose 配置时，把它的服务同时接入外部网络：

```yaml
services:
  n8n:
    networks:
      - default
      - enterprise_shared

networks:
  enterprise_shared:
    name: enterprise-shared
    external: true
```

n8n 的 HTTP Request 节点使用 Docker 内部地址：

```text
http://enterprise-fastapi:8000/workflow/run
```

首次手工联调也可以执行 `docker network connect enterprise-shared n8n-n8n-1`，
但容器重新创建后手工连接可能丢失，长期应写入 n8n 的 Compose 配置。

### 后续发布新版本

本地测试并推送代码后，在服务器执行：

```bash
git pull --ff-only
docker compose build api
docker compose run --rm api alembic -c alembic.ini upgrade head
docker compose up -d --no-deps api
docker compose ps
curl http://127.0.0.1:8000/health
```

正常更新只重建 API，不删除 MySQL 数据卷。不要把
`docker compose down -v` 作为日常发布命令。

## MySQL 业务数据库

复制环境变量模板并修改本地密码：

```bash
cp .env.example .env
```

Mac 只启动 MySQL 8.4（用于宿主机直接运行 Uvicorn 或数据库客户端）：

```bash
docker compose -f compose.yml -f compose.local.yml up -d mysql
docker compose -f compose.yml -f compose.local.yml ps
```

公共 `compose.yml` 不发布 MySQL 端口；Mac 通过 `compose.local.yml` 追加
`127.0.0.1:${MYSQL_PORT:-3306}:3306`。服务器只使用 `compose.yml`，不要加载
`compose.local.yml`。

安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r fastapi/requirements.txt
```

通过 Alembic 执行第一版数据库迁移：

```bash
alembic -c fastapi/alembic.ini upgrade head
```

迁移会创建：

- `workflow_run`：一次完整业务运行。
- `workflow_step_run`：运行步骤及重试记录。

检查当前迁移版本以及模型和数据库是否一致：

```bash
alembic -c fastapi/alembic.ini current
alembic -c fastapi/alembic.ini check
```

验证数据库：

```bash
docker compose exec -T mysql sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u "$MYSQL_USER" "$MYSQL_DATABASE" \
  -e "SHOW TABLES; SHOW VARIABLES LIKE '\''character_set_server'\'';"'
```

数据库表结构只通过 Alembic 管理，不在应用启动时调用
`Base.metadata.create_all()` 自动建表。

## 运行测试

```bash
PYTHONPATH=fastapi pytest -q
```
