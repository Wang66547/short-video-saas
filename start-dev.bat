@echo off
chcp 65001 >nul
echo ============================================================
echo  爆款短视频复刻SaaS平台 - 本地开发环境启动脚本
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] 检查 Docker 环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Docker，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 docker-compose
    pause
    exit /b 1
)

echo [2/4] 启动 MySQL 和 Redis...
docker-compose -f docker-compose.dev.yml up -d

echo.
echo [3/4] 等待 MySQL 启动...
timeout /t 15 /nobreak >nul

echo [4/4] 验证服务状态...
docker-compose -f docker-compose.dev.yml ps

echo.
echo ============================================================
echo  MySQL 连接信息:
echo    地址: localhost:3306
echo    用户名: dev_user
echo    密码: dev123456
echo    数据库: short_video_saas
echo.
echo  Redis 连接信息:
echo    地址: localhost:6379
echo ============================================================
echo.
echo  后端配置已准备: backend\.env.localdev
echo  启动后端前，请复制 .env.localdev 为 .env:
echo    copy backend\.env.localdev backend\.env
echo.
echo [完成] Docker 服务已启动
echo.
pause
