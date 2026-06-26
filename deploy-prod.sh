#!/bin/bash
# ============================================================
# 爆款短视频复刻SaaS平台 - 一键部署脚本 (生产环境, IP访问版)
# ============================================================
set -e

echo "=========================================="
echo "  爆款短视频复刻SaaS平台 - 生产环境部署"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 root 用户或 sudo 执行此脚本"
    exit 1
fi

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
fi

# 检查 Docker Compose 是否安装
if ! docker compose version &> /dev/null; then
    echo "Docker Compose 插件未安装，正在安装..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

echo "Docker 环境检查通过"

# 创建数据目录
echo "创建数据目录..."
mkdir -p /data/mysql /data/redis /data/videos /data/temp
mkdir -p /opt/short-video/logs/backend /opt/short-video/logs/celery /opt/short-video/logs/nginx

# 设置目录权限
chmod 700 /data/mysql /data/redis
chmod 755 /data/videos
chmod 777 /data/temp

echo "数据目录创建完成"

# 检查项目文件
if [ ! -f "docker-compose.prod-ip.yml" ]; then
    echo "错误: 未找到 docker-compose.prod-ip.yml"
    exit 1
fi

if [ ! -d "frontend-user/dist" ] || [ ! -d "frontend-admin/dist" ]; then
    echo "错误: 前端构建产物不存在，请先构建前端"
    exit 1
fi

# 复制环境变量配置
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo "已复制 .env.production 为 .env"
    else
        cp .env.example .env
        echo "已复制 .env.example 为 .env"
    fi
fi

# 生成随机 SECRET_KEY
if grep -q "please-change-this-to-a-random" .env; then
    RANDOM_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 64 | tr -d '\n')
    sed -i "s|SECRET_KEY=please-change-this-to-a-random-string-at-least-32-chars|SECRET_KEY=$RANDOM_KEY|" .env
    echo "已生成随机 SECRET_KEY"
fi

echo ""
echo "=========================================="
echo "  开始构建和启动服务..."
echo "=========================================="

# 构建并启动服务
docker compose -f docker-compose.prod-ip.yml up -d --build

echo ""
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "=========================================="
echo "  服务状态检查"
echo "=========================================="
docker compose -f docker-compose.prod-ip.yml ps

# 健康检查
echo ""
echo "健康检查..."
sleep 5

if curl -s http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx 服务正常"
else
    echo "⚠️  Nginx 服务可能未就绪，请稍后检查"
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端 API 服务正常"
else
    echo "⚠️  后端服务可能未就绪，请稍后检查"
fi

# 获取本机 IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  用户端: http://$SERVER_IP/"
echo "  管理端: http://$SERVER_IP/admin/"
echo "  API文档: http://$SERVER_IP/docs"
echo ""
echo "常用命令:"
echo "  查看日志: docker compose -f docker-compose.prod-ip.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.prod-ip.yml down"
echo "  重启服务: docker compose -f docker-compose.prod-ip.yml restart"
echo "  查看状态: docker compose -f docker-compose.prod-ip.yml ps"
echo ""
echo "注意事项:"
echo "  1. 请修改 .env 文件中的默认密码和密钥"
echo "  2. 生产环境建议配置域名和 HTTPS"
echo "  3. 记得配置防火墙，仅开放必要端口"
echo ""
