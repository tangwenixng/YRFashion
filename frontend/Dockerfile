FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

ENV BACKEND_UPSTREAM=backend:8000
ENV ADMIN_ENTRY_PATH=/

COPY docker-entrypoint.d/10-admin-entry.envsh /docker-entrypoint.d/10-admin-entry.envsh
RUN chmod +x /docker-entrypoint.d/10-admin-entry.envsh
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
