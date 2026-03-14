# YRFasion Backend

Python admin backend for the YRFasion MVP.

## Setup

```bash
uv sync
uv run uvicorn backend.main:app --reload
```

The service starts with these local-development defaults:

- SQLite database: `backend/data/app.db`
- Upload directory: `backend/data/uploads`
- API base path: `/api`
- Local static uploads: `/uploads/*`
- Bootstrap admin username: `admin`
- Bootstrap admin password: `admin123456`

## Runtime modes

The backend supports two runtime combinations:

1. Local development
- SQLite
- local upload directory
- `/uploads/*` served by FastAPI

2. CloudBase deployment
- MySQL
- CloudBase storage bucket via COS SDK
- product image URLs returned as public storage URLs

## Environment

Copy `.env.example` to `.env` and override values as needed.

### Core variables

- `DATABASE_URL`
  Preferred when you already have a full DSN.
- `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE`
  Used when `DATABASE_URL` is empty.
- `STORAGE_BACKEND`
  `local` or `cloudbase`
- `STORAGE_BUCKET`
  Example: `6465-dev-xxxxx-1411342876`
- `STORAGE_REGION`
  Example: `ap-shanghai`
- `STORAGE_SECRET_ID`
- `STORAGE_SECRET_KEY`
- `STORAGE_PUBLIC_BASE_URL`
  Optional CDN or custom media domain. If empty, the backend falls back to the COS public URL.
- `STORAGE_PATH_PREFIX`
  Optional object prefix such as `dev`
- `CORS_ALLOW_ORIGINS`
  Comma-separated origins, for example:
  `https://admin.example.com,https://preview.example.com`
- `SECRET_KEY`
  Must be replaced in any non-local environment.

### Example CloudBase-style MySQL configuration

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
```

## Docker image

Build locally:

```bash
docker build -t yrfasion-backend ./backend
```

Run locally with environment variables:

```bash
docker run --rm -p 8000:8000 --env-file backend/.env yrfasion-backend
```

## GitHub Actions image build

The repository includes an automated backend image workflow at
`.github/workflows/backend-docker.yml`.

- `pull_request`: runs backend checks and verifies the Docker build
- `push` to `master`: runs checks, builds the image, and pushes it to GHCR
- if `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured as repository secrets, the same image is also pushed to Docker Hub
- `workflow_dispatch`: allows a manual rebuild from the GitHub Actions UI on the selected ref

Published image:

```text
ghcr.io/<github-owner>/yrfashion-backend
```

Optional Docker Hub image:

```text
docker.io/<dockerhub-username>/yrfashion-backend
```

Generated tags include:

- branch name
- commit SHA
- `latest` on the default branch

Required repository secrets for Docker Hub publishing:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## CloudBase deployment notes

This repository is prepared for CloudBase cloud hosting using image deployment.

Recommended production setup:

- Backend: Cloud Hosting service built from `backend/Dockerfile`
- Database: CloudBase or Tencent Cloud MySQL
- File storage: CloudBase storage bucket
- Frontend admin site: CloudBase static hosting
- API domain: custom domain mapped to the backend service

Before creating the service in CloudBase, make sure you have:

- a reachable MySQL instance and database name
- storage bucket region and bucket name
- a usable `SECRET_KEY`
- production admin bootstrap credentials
- CORS origins for the admin frontend domain

## Main admin endpoints

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

## Main miniapp endpoints

- `POST /api/miniapp/auth/login`
- `GET /api/miniapp/home`
- `GET /api/miniapp/products`
- `GET /api/miniapp/products/{id}`
- `POST /api/miniapp/products/{id}/messages`
- `GET /api/miniapp/shop/contact`

## Verification

```bash
uv run pytest
uv run ruff check .
```
