#!/bin/bash
set -e

echo "========================================="
echo "  爆款短视频复刻SaaS平台 - 启动中"
echo "  环境: ${ENV:-production}"
echo "========================================="

cd /app/backend

# ============================================================
# 1. 环境变量适配 (Railway 兼容)
# ============================================================

# 自动生成 SECRET_KEY（如果未设置）
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-change-in-production-min-32-chars" ]; then
    export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    echo "[INFO] 自动生成 SECRET_KEY（首次启动，重启后会变化，建议手动设置）"
fi

# 适配 Railway MySQL 插件提供的 DATABASE_URL
if [ -n "$MYSQL_URL" ] && [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="$MYSQL_URL"
    echo "[INFO] 使用 MYSQL_URL 作为 DATABASE_URL"
fi

# 适配 Railway MySQL 的连接格式 - 确保使用 aiomysql
if [ -n "$DATABASE_URL" ]; then
    # 将 mysql:// 转换为 mysql+aiomysql://
    if [[ "$DATABASE_URL" == mysql://* ]]; then
        export DATABASE_URL="${DATABASE_URL/mysql:\/\//mysql+aiomysql:\/\/}"
        echo "[INFO] DATABASE_URL 已转换为 aiomysql 格式"
    fi
    # 设置同步连接 URL
    if [ -z "$DATABASE_SYNC_URL" ]; then
        SYNC_URL="${DATABASE_URL/mysql+aiomysql:\/\//mysql+pymysql:\/\/}"
        export DATABASE_SYNC_URL="$SYNC_URL"
        echo "[INFO] 自动生成 DATABASE_SYNC_URL"
    fi
fi

# 适配 Railway Redis 插件
if [ -n "$REDIS_URL" ]; then
    # 设置 Celery 相关 Redis URL
    if [ -z "$CELERY_BROKER_URL" ]; then
        # 将 /0 替换为 /1 作为 broker
        export CELERY_BROKER_URL="${REDIS_URL%/*}/1"
        echo "[INFO] 自动生成 CELERY_BROKER_URL"
    fi
    if [ -z "$CELERY_RESULT_BACKEND" ]; then
        # 将 /0 替换为 /2 作为 result backend
        export CELERY_RESULT_BACKEND="${REDIS_URL%/*}/2"
        echo "[INFO] 自动生成 CELERY_RESULT_BACKEND"
    fi
fi

# 自动设置 CORS（允许所有来源，Railway 动态域名）
if [ -z "$CORS_ORIGINS" ]; then
    export CORS_ORIGINS='["*"]'
    echo "[INFO] CORS_ORIGINS 设置为允许所有来源"
fi

# 确保 WHISPER_DEVICE 为 cpu（Railway 无 GPU）
export WHISPER_DEVICE=cpu

# 创建必要的目录
mkdir -p /app/videos /app/temp /app/logs

# ============================================================
# 2. 数据库初始化
# ============================================================
echo ""
echo "[1/3] 初始化数据库..."
python init_db.py 2>&1 || echo "[WARN] 数据库初始化跳过或已完成，继续启动..."

# ============================================================
# 3. 启动后端服务
# ============================================================
echo ""
echo "[2/3] 启动后端 API 服务..."
cd /app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!

# 等待后端启动
echo "等待后端服务就绪..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "后端服务已就绪"
        break
    fi
    sleep 2
done

# ============================================================
# 4. 启动网关（静态资源 + 反向代理）
# ============================================================
echo ""
echo "[3/3] 启动部署网关..."
export GATEWAY_PORT=${PORT:-8080}
export BACKEND_URL="http://localhost:8000"
cd /app
python gateway.py &
GATEWAY_PID=$!

echo ""
echo "========================================="
echo "  🎉 服务启动完成！"
echo "  端口: ${GATEWAY_PORT}"
echo "  用户端: http://localhost:${GATEWAY_PORT}/"
echo "  管理端: http://localhost:${GATEWAY_PORT}/admin/"
echo "  API文档: http://localhost:${GATEWAY_PORT}/docs"
echo "========================================="
echo ""

# 等待所有进程
wait
