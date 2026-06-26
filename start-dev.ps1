# 爆款短视频复刻SaaS平台 - 本地开发环境启动脚本
# 使用方式: 右键 -> 使用 PowerShell 运行

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 爆款短视频复刻SaaS平台 - 本地开发环境启动脚本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $ProjectRoot

try {
    Write-Host "[1/4] 检查 Docker 环境..." -ForegroundColor Yellow
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        Write-Host "[错误] 未安装 Docker，请先安装 Docker Desktop" -ForegroundColor Red
        Write-Host "下载地址: https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }
    Write-Host "  Docker 版本: $dockerVersion" -ForegroundColor Green

    Write-Host ""
    Write-Host "[2/4] 启动 MySQL 和 Redis..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml up -d
    if ($LASTEXITCODE -ne 0) { throw "docker-compose 启动失败" }
    Write-Host "  服务已启动" -ForegroundColor Green

    Write-Host ""
    Write-Host "[3/4] 等待 MySQL 启动就绪..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    Write-Host ""
    Write-Host "[4/4] 验证服务状态..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml ps

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " MySQL 连接信息:" -ForegroundColor White
    Write-Host "   地址: localhost:3306" -ForegroundColor White
    Write-Host "   用户名: dev_user" -ForegroundColor White
    Write-Host "   密码: dev123456" -ForegroundColor White
    Write-Host "   数据库: short_video_saas" -ForegroundColor White
    Write-Host ""
    Write-Host " Redis 连接信息:" -ForegroundColor White
    Write-Host "   地址: localhost:6379" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 后端配置已准备: backend\.env.localdev" -ForegroundColor Yellow
    Write-Host ""
    Write-Host " 启动后端前，请执行以下命令切换配置:" -ForegroundColor Yellow
    Write-Host "   cd backend" -ForegroundColor Gray
    Write-Host "   copy .env.localdev .env" -ForegroundColor Gray
    Write-Host "   python init_db.py" -ForegroundColor Gray
    Write-Host "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[完成] Docker 服务已启动!" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "[错误] $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车退出"
} finally {
    Pop-Location
}
