# ============================================================
# 爆款短视频复刻SaaS平台 - Windows Docker 一键部署脚本
# ============================================================
# 使用方式: 右键 -> 使用 PowerShell 以管理员运行
# ============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   爆款短视频复刻 - Windows Docker 一键部署" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $ProjectRoot

# ==================== 前置检查 ====================
Write-Host "[1/7] 检查 Docker 环境..." -ForegroundColor Yellow

$dockerVersion = docker --version 2>$null
if (-not $dockerVersion) {
    Write-Host ""
    Write-Host "[错误] 未检测到 Docker！" -ForegroundColor Red
    Write-Host "  请先安装 Docker Desktop：" -ForegroundColor Yellow
    Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按回车退出"
    exit 1
}
Write-Host "  Docker 版本: $($dockerVersion.Trim())" -ForegroundColor Green

# 检查 Docker 是否运行
try {
    docker info >$null 2>&1
    Write-Host "  Docker 服务: 运行中" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[错误] Docker 服务未启动，请打开 Docker Desktop 并等待其完全启动" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车退出"
    exit 1
}

# ==================== 检查前端构建产物 ====================
Write-Host ""
Write-Host "[2/7] 检查前端构建产物..." -ForegroundColor Yellow

$userDist = Join-Path $ProjectRoot "frontend-user\dist"
$adminDist = Join-Path $ProjectRoot "frontend-admin\dist"

if (!(Test-Path $userDist) -or (Get-ChildItem $userDist -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "  [提示] 用户端前端未构建，正在构建..." -ForegroundColor Yellow
    Set-Location "frontend-user"
    npm install
    npm run build
    Set-Location ..
} else {
    Write-Host "  用户端前端: 已构建 ✓" -ForegroundColor Green
}

if (!(Test-Path $adminDist) -or (Get-ChildItem $adminDist -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "  [提示] 管理后台未构建，正在构建..." -ForegroundColor Yellow
    Set-Location "frontend-admin"
    npm install
    npm run build
    Set-Location ..
} else {
    Write-Host "  管理后台前端: 已构建 ✓" -ForegroundColor Green
}

# ==================== 创建必要目录 ====================
Write-Host ""
Write-Host "[3/7] 创建必要目录..." -ForegroundColor Yellow

$dirs = @("logs\backend", "logs\celery", "logs\nginx")
foreach ($dir in $dirs) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Write-Host "  目录创建完成" -ForegroundColor Green

# ==================== 停止旧容器 ====================
Write-Host ""
Write-Host "[4/7] 停止旧容器（如有）..." -ForegroundColor Yellow
docker-compose -f docker-compose.win.yml down 2>$null
Write-Host "  旧容器已清理" -ForegroundColor Green

# ==================== 拉取镜像 ====================
Write-Host ""
Write-Host "[5/7] 拉取 Docker 镜像..." -ForegroundColor Yellow
Write-Host "  （首次下载可能需要几分钟）" -ForegroundColor Gray
docker-compose -f docker-compose.win.yml pull
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 镜像拉取失败，请检查网络连接" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "  镜像拉取完成" -ForegroundColor Green

# ==================== 构建后端镜像 ====================
Write-Host ""
Write-Host "[6/7] 构建后端镜像..." -ForegroundColor Yellow
docker-compose -f docker-compose.win.yml build backend celery-worker
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 后端镜像构建失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "  后端镜像构建完成" -ForegroundColor Green

# ==================== 启动服务 ====================
Write-Host ""
Write-Host "[7/7] 启动所有服务..." -ForegroundColor Yellow
docker-compose -f docker-compose.win.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 服务启动失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# ==================== 等待服务就绪 ====================
Write-Host ""
Write-Host "  等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 20

# ==================== 验证服务 ====================
Write-Host ""
Write-Host "  验证服务状态..." -ForegroundColor Yellow
docker-compose -f docker-compose.win.yml ps

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   部署完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  访问地址:" -ForegroundColor White
Write-Host "    用户端: http://localhost" -ForegroundColor Cyan
Write-Host "    管理后台: http://localhost/admin/" -ForegroundColor Cyan
Write-Host "    API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  常用命令:" -ForegroundColor White
Write-Host "    查看日志: docker-compose -f docker-compose.win.yml logs -f" -ForegroundColor Gray
Write-Host "    停止服务: docker-compose -f docker-compose.win.yml down" -ForegroundColor Gray
Write-Host "    重启服务: docker-compose -f docker-compose.win.yml restart" -ForegroundColor Gray
Write-Host "    查看状态: docker-compose -f docker-compose.win.yml ps" -ForegroundColor Gray
Write-Host ""
Write-Host "  数据库信息:" -ForegroundColor White
Write-Host "    地址: localhost:3306" -ForegroundColor Gray
Write-Host "    用户名: sv_saas" -ForegroundColor Gray
Write-Host "    密码: SvSaas@2024Secure" -ForegroundColor Gray
Write-Host "    数据库: short_video_saas" -ForegroundColor Gray
Write-Host ""

Pop-Location
Read-Host "按回车退出"