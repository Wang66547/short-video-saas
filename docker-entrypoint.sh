#!/bin/bash
set -e

cd /app/backend

echo "[1/2] 初始化数据库..."
python init_db.py 2>&1 || echo "数据库初始化跳过或已完成"

echo "[2/2] 启动服务..."
export GATEWAY_PORT=${PORT:-8080}
export BACKEND_URL="http://localhost:8000"

cd /app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!

cd /app
python gateway.py &
GATEWAY_PID=$!

echo "========================================="
echo "  服务启动完成！"
echo "  端口: ${GATEWAY_PORT}"
echo "========================================="

wait
