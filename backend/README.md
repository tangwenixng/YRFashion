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

## Environment

Copy `.env.example` to `.env` and override values as needed.

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
- `GET /api/miniapp/shop/contact`

## Verification

```bash
uv run pytest
uv run ruff check .
```
