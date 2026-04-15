# Dual Environment Deployment

This repository can run production and staging on the same host by using two Compose projects with different env files.

## Files

- `deploy/prod.env.example`: production example
- `deploy/staging.env.example`: staging example

Copy them to local files before use:

```bash
cp deploy/prod.env.example deploy/prod.env
cp deploy/staging.env.example deploy/staging.env
```

## Recommended values

Production:

- `COMPOSE_PROJECT_NAME=yrfashion-prod`
- `FRONTEND_PORT=8080`
- `BACKEND_PORT=8000`
- `ADMIN_ENTRY_PATH=/fashion`

Staging:

- `COMPOSE_PROJECT_NAME=yrfashion-staging`
- `FRONTEND_PORT=8081`
- `BACKEND_PORT=8001`
- `ADMIN_ENTRY_PATH=/fashion-dev`

Using different project names keeps containers, networks, and the `backend_data` volume isolated.

## Start commands

Production:

```bash
docker compose --env-file deploy/prod.env up -d
```

Staging:

```bash
docker compose --env-file deploy/staging.env up -d
```

## Nginx Proxy Manager

Point the public prefixes to the matching frontend ports on `172.26.100.175`.

Production:

- `https://today.dcove.cn/fashion` -> `http://172.26.100.175:8080`

Staging:

- `https://today.dcove.cn/fashion-dev` -> `http://172.26.100.175:8081`

## Miniapp mapping

Recommended miniapp API mapping:

- `release` -> `https://today.dcove.cn/fashion/api`
- `develop` -> `https://today.dcove.cn/fashion-dev/api`
- `trial` -> `https://today.dcove.cn/fashion-dev/api`

## Notes

- Do not reuse the same `SECRET_KEY` between environments.
- Do not reuse the same admin password between environments.
- Do not point both environments at the same image tag if you need code isolation.
- Do not manually share SQLite files or uploads between the two environments.
