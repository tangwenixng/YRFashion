# CloudBase 后端部署操作说明

版本：v0.1  
日期：2026-03-14

本文对应当前仓库已经完成的后端改造，用于指导将 `backend` 部署到 CloudBase 云托管。

## 1. 当前代码已完成的准备

当前仓库已支持：

- 后端在本地模式下继续使用 `SQLite + 本地上传目录`
- 后端在云上模式下切换为 `MySQL + CloudBase 存储桶`
- 通过环境变量切换数据库与存储后端
- 使用 `backend/Dockerfile` 构建镜像
- 后台前端通过 `VITE_API_BASE_URL` 配置生产 API 地址

当前仓库尚未完成：

- 小程序真实 `code2Session` 登录接入
- 正式 API 域名与后台域名配置
- 生产环境密钥与管理员账号填写

## 2. 这次部署涉及的主要文件

后端相关：

- [backend/src/backend/core/config.py](/D:/Codes/YRFasion/backend/src/backend/core/config.py)
- [backend/src/backend/db/session.py](/D:/Codes/YRFasion/backend/src/backend/db/session.py)
- [backend/src/backend/main.py](/D:/Codes/YRFasion/backend/src/backend/main.py)
- [backend/src/backend/services/storage.py](/D:/Codes/YRFasion/backend/src/backend/services/storage.py)
- [backend/src/backend/api/routes/admin_products.py](/D:/Codes/YRFasion/backend/src/backend/api/routes/admin_products.py)
- [backend/.env.example](/D:/Codes/YRFasion/backend/.env.example)
- [backend/Dockerfile](/D:/Codes/YRFasion/backend/Dockerfile)
- [backend/.dockerignore](/D:/Codes/YRFasion/backend/.dockerignore)
- [backend/README.md](/D:/Codes/YRFasion/backend/README.md)

前端相关：

- [frontend/src/api/http.ts](/D:/Codes/YRFasion/frontend/src/api/http.ts)
- [frontend/vite.config.ts](/D:/Codes/YRFasion/frontend/vite.config.ts)
- [frontend/.env.production.example](/D:/Codes/YRFasion/frontend/.env.production.example)

## 3. 你需要先准备好的信息

以下信息仍需要你补齐：

- MySQL 数据库名
- MySQL 用户名与密码
- 生产环境 `SECRET_KEY`
- 初始后台管理员用户名、密码、显示名
- CloudBase 存储访问密钥：`STORAGE_SECRET_ID` / `STORAGE_SECRET_KEY`
- API 域名
- 后台前端域名
- 如要正式上线，小程序真实登录所需 `AppID` / `AppSecret`

说明：

- 你当前文档里填的 `10.31.104.148:3306` 只是数据库地址，不是完整的 `DATABASE_URL`
- 当前代码支持两种方式：
  - 直接提供 `DATABASE_URL`
  - 分开提供 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`

## 4. 建议的环境变量

建议在 CloudBase 云托管服务中配置以下环境变量：

```env
API_PREFIX=/api
MYSQL_HOST=10.31.104.148
MYSQL_PORT=3306
MYSQL_USER=你的数据库用户名
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=你的数据库名
MYSQL_CHARSET=utf8mb4

STORAGE_BACKEND=cloudbase
STORAGE_BUCKET=6465-dev-5ghesf7bc4147fee-1411342876
STORAGE_REGION=ap-shanghai
STORAGE_SECRET_ID=你的SecretId
STORAGE_SECRET_KEY=你的SecretKey
STORAGE_PUBLIC_BASE_URL=
STORAGE_PATH_PREFIX=

CORS_ALLOW_ORIGINS=https://你的后台域名
SECRET_KEY=替换为高强度随机字符串
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=替换为强密码
BOOTSTRAP_ADMIN_DISPLAY_NAME=Store Admin
```

补充说明：

- 如果后续给图片单独配了 CDN 域名，把 `STORAGE_PUBLIC_BASE_URL` 填成该域名即可
- 如果暂时没有 CDN，可以先留空，后端会回退到 COS 公网访问地址
- 如果你已经有完整 `DATABASE_URL`，也可以只填 `DATABASE_URL` 而不填分拆的 MySQL 字段

## 5. 镜像部署步骤

根据 CloudBase 官方文档，云托管支持镜像部署；新建服务时需要填写镜像地址、服务端口、环境变量等信息。当前建议按下面流程操作：

### 5.1 本地构建镜像

在仓库根目录执行：

```bash
docker build -t yrfasion-backend ./backend
```

### 5.2 推送镜像到镜像仓库

建议使用腾讯云 TCR。

通用流程：

1. 在腾讯云创建或选择一个镜像仓库
2. 登录本地 Docker 到该仓库
3. 给本地镜像打 tag
4. 推送镜像

示例命令中的地址、命名空间、仓库名请按你的实际情况替换：

```bash
docker tag yrfasion-backend ccr.ccs.tencentyun.com/你的命名空间/yrfasion-backend:latest
docker push ccr.ccs.tencentyun.com/你的命名空间/yrfasion-backend:latest
```

### 5.3 在 CloudBase 云托管创建服务

在 CloudBase 控制台中：

1. 进入目标环境：`dev-5ghesf7bc4147fee`
2. 打开“云托管”
3. 选择“从容器镜像部署”
4. 填入镜像地址
5. 服务端口填写：`8000`
6. 配置环境变量
7. 设置实例规格与伸缩策略
8. 开始部署

建议的初始设置：

- 端口：`8000`
- 最小实例数：开发环境可先设为 `0`
- 最大实例数：先从较小值起步
- 部署完成后先验证默认访问域名是否可通

## 6. HTTP 访问服务与 API 域名

后端服务部署成功后，需要再配置对外访问入口。

建议做法：

1. 进入 CloudBase “HTTP 访问服务”
2. 把云托管服务关联进去
3. 触发路径建议保持 `/`
4. 先用默认域名联调
5. 确认接口可访问后，再绑定正式自定义域名

正式环境建议：

- API 使用自定义域名，例如 `api.xxx.com`
- 默认域名只用于测试，不作为正式长期入口

## 7. 后台前端部署步骤

后台前端当前已支持通过环境变量指定生产 API 地址。

### 7.1 本地构建前准备

在 [frontend/.env.production.example](/D:/Codes/YRFasion/frontend/.env.production.example) 基础上，准备生产环境变量：

```env
VITE_API_BASE_URL=https://你的API域名/api
```

### 7.2 构建

```bash
cd frontend
npm install
npm run build
```

### 7.3 部署到 CloudBase 静态网站托管

在 CloudBase 控制台中：

1. 打开“静态网站托管”
2. 上传 `frontend/dist`
3. 获取默认域名验证页面可访问
4. 绑定后台正式域名

## 8. 域名与备案

需要特别注意：

- CloudBase 默认域名更适合测试
- 正式环境建议绑定自定义域名
- 浏览器直接访问后台站点或 API 的生产环境，应提前准备备案域名和证书

建议顺序：

1. 先用默认域名完成联调
2. 再接入自定义域名
3. 最后切换到正式域名进行灰度验证

## 9. 当前建议的实际推进顺序

1. 先把 MySQL 数据库名、用户、密码补齐
2. 准备 `SECRET_KEY` 和后台管理员账号
3. 准备存储 `SecretId/SecretKey`
4. 本地构建并推送后端镜像
5. 在 CloudBase 新建云托管服务并配置环境变量
6. 用默认域名测试后端接口
7. 构建并上传后台前端到静态网站托管
8. 配置 HTTP 访问服务和后台站点默认入口
9. 再接入自定义域名与备案

## 10. 后续仍需我处理的内容

等你补齐剩余信息后，我可以继续做：

- 接入小程序真实 `code2Session`
- 把小程序 `miniapp/utils/config.js` 切到正式 API 域名
- 补 CloudBase 生产环境 `.env` 模板
- 继续补一版“上线检查清单”

## 11. 参考文档

- CloudBase 云托管概述：https://docs.cloudbase.net/run/introduction
- CloudBase 镜像部署：https://docs.cloudbase.net/run/deploy/deploy/deploying-image
- CloudBase 部署服务：https://docs.cloudbase.net/run/deploy/deploy-service
- CloudBase HTTP 访问服务与自定义域名：https://docs.cloudbase.net/service/custom-domain
- CloudBase 静态网站托管概述：https://docs.cloudbase.net/hosting/introduce
