@echo off
chcp 65001 >nul
echo ============================================================
echo  爆款短视频复刻SaaS平台 - 停止开发环境
echo ============================================================
echo.

cd /d "%~dp0"

echo 停止 MySQL 和 Redis...
docker-compose -f docker-compose.dev.yml down

echo.
echo [完成] 开发环境已停止
echo.
pause
