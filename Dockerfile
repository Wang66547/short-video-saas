# ==================== 构建阶段 1: 构建前端用户端 ====================
FROM node:18-alpine AS user-frontend-builder
WORKDIR /app/frontend-user
COPY frontend-user/package*.json ./
RUN npm ci
COPY frontend-user/ ./
RUN npm run build

# ==================== 构建阶段 2: 构建前端管理后台 ====================
FROM node:18-alpine AS admin-frontend-builder
WORKDIR /app/frontend-admin
COPY frontend-admin/package*.json ./
RUN npm ci
COPY frontend-admin/ ./
RUN npm run build

# ==================== 构建阶段 3: 后端运行环境 ====================
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=user-frontend-builder /app/frontend-user/dist ./frontend-user/dist
COPY --from=admin-frontend-builder /app/frontend-admin/dist ./frontend-admin/dist

# 复制网关和启动脚本
COPY gateway.py ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# 暴露端口
EXPOSE 8000

# 环境变量默认值
ENV ENV=production
ENV PYTHONPATH=/app/backend

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]
