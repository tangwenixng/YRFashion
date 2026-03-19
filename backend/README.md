# YRFasion Backend

YRFasion MVP 的 Python 管理后台服务。

## 环境准备

```bash
uv sync
uv run uvicorn backend.main:app --reload
```

服务在本地开发环境下默认使用以下配置：

- SQLite 数据库：`backend/data/app.db`
- 上传目录：`backend/data/uploads`
- API 基础路径：`/api`
- 本地静态上传访问路径：`/uploads/*`
- 初始管理员用户名：`admin`
- 初始管理员密码：`admin123456`

## 运行模式

后端支持两种运行组合：

1. 本地开发
- SQLite
- 本地上传目录
- 由 FastAPI 直接提供 `/uploads/*` 静态文件访问

2. CloudBase 部署
- MySQL
- 通过 COS SDK 接入 CloudBase 存储桶
- 商品图片 URL 返回公共存储访问地址

## 环境变量

将 `.env.example` 复制为 `.env`，再按需覆盖配置值。

### 核心变量

- `DATABASE_URL`
  当你已经有完整 DSN 时，优先使用该变量。
- `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE`
  当 `DATABASE_URL` 为空时使用。
- `STORAGE_BACKEND`
  可选值为 `local` 或 `cloudbase`
- `STORAGE_BUCKET`
  示例：`6465-dev-xxxxx-1411342876`
- `STORAGE_REGION`
  示例：`ap-shanghai`
- `STORAGE_SECRET_ID`
- `STORAGE_SECRET_KEY`
- `STORAGE_PUBLIC_BASE_URL`
  可选的 CDN 或自定义媒体域名。如果为空，后端会回退到 COS 的公共访问地址。
- `STORAGE_PATH_PREFIX`
  可选的对象前缀，例如 `dev`
- `CORS_ALLOW_ORIGINS`
  以逗号分隔的来源列表，例如：
  `https://admin.example.com,https://preview.example.com`
- `SECRET_KEY`
  在任何非本地环境中都必须替换。
- `MINIAPP_APP_ID`
  微信小程序 AppID，用于调用官方 `code2Session`。
- `MINIAPP_APP_SECRET`
  微信小程序 AppSecret。

### CloudBase 风格 MySQL 配置示例

```env
MYSQL_HOST=10.31.104.148
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=yrfasion
STORAGE_BACKEND=cloudbase
STORAGE_BUCKET=6465-dev-5ghesf7bc4147fee-1411342876
STORAGE_REGION=ap-shanghai
STORAGE_SECRET_ID=your_secret_id
STORAGE_SECRET_KEY=your_secret_key
STORAGE_PUBLIC_BASE_URL=
CORS_ALLOW_ORIGINS=https://admin.example.com
SECRET_KEY=replace-with-a-random-secret
MINIAPP_APP_ID=wx1234567890abcdef
MINIAPP_APP_SECRET=replace-with-miniapp-secret
```

## Docker 镜像

本地构建：

```bash
docker build -t yrfasion-backend ./backend
```

携带环境变量在本地运行：

```bash
docker run --rm -p 8000:8000 --env-file backend/.env yrfasion-backend
```

## GitHub Actions 镜像构建

仓库内已经包含后端镜像自动化工作流，路径为：
`.github/workflows/backend-docker.yml`。

- `pull_request`：执行后端检查，并验证 Docker 构建是否成功
- 推送到 `master`：执行检查、构建镜像并推送到 GHCR
- 如果仓库 Secrets 中配置了 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`，同一份镜像也会同步推送到 Docker Hub
- `workflow_dispatch`：支持在 GitHub Actions 页面中针对指定 ref 手动触发重建

发布后的镜像地址：

```text
ghcr.io/<github-owner>/yrfashion-backend
```

可选的 Docker Hub 镜像地址：

```text
docker.io/<dockerhub-username>/yrfashion-backend
```

生成的标签包括：

- 分支名
- commit SHA
- 默认分支上的 `latest`

发布到 Docker Hub 需要的仓库 Secrets：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

生产环境如果需要自动部署，建议在服务器侧使用 `systemd timer` 定时执行
`docker compose pull && docker compose up -d`。可参考文档：
`docs/11-CentOS7-systemd-timer自动部署说明.md`

## CloudBase 部署说明

当前仓库已经为基于镜像部署的 CloudBase 云托管场景做好准备。

推荐的生产环境组合：

- 后端：使用 `backend/Dockerfile` 构建并部署到 Cloud Hosting 服务
- 数据库：CloudBase 或腾讯云 MySQL
- 文件存储：CloudBase 存储桶
- 管理端前端站点：CloudBase 静态托管
- API 域名：将自定义域名映射到后端服务

在 CloudBase 中创建服务之前，请先确认你已经准备好：

- 可访问的 MySQL 实例和数据库名
- 存储桶所在地域与桶名称
- 可用的 `SECRET_KEY`
- 生产环境管理员初始化账号信息
- 管理端前端域名对应的 CORS 来源配置

## 主要管理端接口

- `POST /api/admin/auth/login`
- `GET /api/admin/auth/me`
- `GET /api/admin/dashboard/summary`
- `GET /api/admin/products`
- `POST /api/admin/products`
- `PUT /api/admin/products/{id}`
- `PUT /api/admin/products/{id}/sort`
- `POST /api/admin/products/{id}/images`
- `GET /api/admin/messages`
- `POST /api/admin/messages/{id}/read`
- `POST /api/admin/messages/{id}/unread`
- `POST /api/admin/messages/{id}/reply`
- `GET /api/admin/users`
- `GET /api/admin/settings`
- `PUT /api/admin/settings`

## 主要小程序端接口

- `POST /api/miniapp/auth/login`
- `GET /api/miniapp/home`
- `GET /api/miniapp/products`
- `GET /api/miniapp/products/{id}`
- `POST /api/miniapp/products/{id}/messages`
- `GET /api/miniapp/shop/contact`

## 校验命令

```bash
uv run pytest
uv run ruff check .
```
