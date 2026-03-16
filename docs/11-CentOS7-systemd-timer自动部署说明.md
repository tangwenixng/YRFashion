# CentOS 7 使用 systemd timer 自动部署说明

本文档适用于当前项目的生产部署方式：

- GitHub Actions 负责构建并推送 `backend`、`frontend` 镜像
- 生产服务器通过 `docker compose` 或 `docker-compose` 拉取新镜像
- 生产服务器使用 `systemd timer` 定时执行部署脚本

这种方案不依赖 GitHub webhook、SSH 反连或 self-hosted runner，适合当前 `CentOS 7` 环境。

## 一、前置条件

- 服务器已经安装 Docker
- 服务器已经安装 `docker compose` 插件，或者安装了独立版 `docker-compose`
- 项目部署目录固定为 `/root/YRFashion`
- 部署目录中已经存在生产环境使用的 `docker-compose.yml`
- 部署目录中已经存在生产环境使用的 `.env`
- 如果 GHCR 镜像是私有的，服务器已经执行过 `docker login ghcr.io`

如果 GHCR 镜像为私有，建议使用有 `read:packages` 权限的 GitHub PAT 登录：

```bash
docker login ghcr.io
```

## 二、部署脚本

在服务器创建脚本 `/usr/local/bin/yrfashion-deploy.sh`：

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

DEPLOY_DIR="/root/YRFashion"
LOCK_FILE="/var/lock/yrfashion-deploy.lock"

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker-compose"
else
  COMPOSE_BIN="docker compose"
fi

mkdir -p /var/lock

(
  flock -n 9 || exit 0

  cd "$DEPLOY_DIR"

  $COMPOSE_BIN pull
  $COMPOSE_BIN up -d --remove-orphans
  docker image prune -f
) 9>"$LOCK_FILE"
```

赋予执行权限：

```bash
chmod +x /usr/local/bin/yrfashion-deploy.sh
```

说明：

- `flock` 用来避免定时任务重叠执行
- 如果当前服务器没有 `docker compose` 插件，脚本会自动回退到 `docker-compose`
- 没有新镜像时，`pull` 和 `up -d` 不会产生实际重启

## 三、systemd service

创建文件 `/etc/systemd/system/yrfashion-deploy.service`：

```ini
[Unit]
Description=YRFashion docker compose deploy
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/yrfashion-deploy.sh
User=root
Group=root
```

## 四、systemd timer

创建文件 `/etc/systemd/system/yrfashion-deploy.timer`：

```ini
[Unit]
Description=Run YRFashion deploy every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true
Unit=yrfashion-deploy.service

[Install]
WantedBy=timers.target
```

这里的配置表示：

- 服务器启动 2 分钟后执行首次部署
- 之后每 5 分钟轮询一次
- 如果机器重启或定时器错过执行窗口，`Persistent=true` 会在恢复后补跑

## 五、启动与验证

加载配置并启动 timer：

```bash
systemctl daemon-reload
systemctl enable --now yrfashion-deploy.timer
systemctl list-timers | grep yrfashion-deploy
```

建议先手动试跑一次：

```bash
systemctl start yrfashion-deploy.service
journalctl -u yrfashion-deploy.service -n 100 --no-pager
```

查看 timer 日志：

```bash
journalctl -u yrfashion-deploy.timer -n 50 --no-pager
```

## 六、建议的运维策略

- GitHub Actions 继续只负责构建与推送镜像，不在 workflow 内直接做生产部署
- 生产环境优先使用固定镜像仓库地址，不在服务器上本地构建
- 如果后续经常修改 `docker-compose.yml`，需要手动同步到 `/root/YRFashion`
- 如果后续希望连 `docker-compose.yml` 也自动同步，可以把 `/root/YRFashion` 改为一个 Git 工作目录，再在脚本里增加 `git pull`

## 七、当前仓库侧建议

当前仓库的 GitHub Actions 应只保留：

- 后端检查
- 前端构建检查
- 后端镜像构建与推送
- 前端镜像构建与推送

生产部署由服务器侧 `systemd timer` 独立负责。
