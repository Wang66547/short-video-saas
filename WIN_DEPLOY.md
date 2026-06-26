# ============================================================
# 爆款短视频复刻 - Windows Docker 上线部署指南
# ============================================================
# 适用环境：Windows 服务器 / 本地电脑
# 部署方式：Docker Compose（无域名，HTTP 访问）
# 最后更新：2026-06-26
# ============================================================

## 一、环境要求

### 必须安装
- Docker Desktop for Windows（https://www.docker.com/products/docker-desktop/）
- Node.js 18+（用于构建前端）
- npm（随 Node.js 一起安装）

### 推荐配置
| 配置项 | 最低要求 | 推荐配置 |
|--------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 50GB | 100GB+ SSD |

## 二、一键部署（推荐）

### 步骤 1：以管理员身份打开 PowerShell

右键点击项目文件夹 -> 在终端中打开

### 步骤 2：运行部署脚本

```powershell
.\deploy-win.ps1
```

脚本会自动完成：
1. 检查 Docker 环境
2. 构建前端（如未构建）
3. 创建必要目录
4. 拉取 Docker 镜像
5. 构建后端镜像
6. 启动所有服务
7. 验证服务状态

### 步骤 3：访问应用

部署成功后，打开浏览器访问：

| 服务 | 地址 |
|------|------|
| 用户端 | http://localhost |
| 管理后台 | http://localhost/admin/ |
| API 文档 | http://localhost:8000/docs |
| 后端直连 | http://localhost:8000 |

## 三、手动部署（进阶）

### 1. 构建前端

```powershell
# 用户端
cd frontend-user
npm install
npm run build

# 管理后台
cd ../frontend-admin
npm install
npm run build
```

### 2. 启动 Docker 服务

```powershell
# 启动所有服务
docker-compose -f docker-compose.win.yml up -d

# 查看服务状态
docker-compose -f docker-compose.win.yml ps

# 查看日志
docker-compose -f docker-compose.win.yml logs -f backend
```

### 3. 停止服务

```powershell
docker-compose -f docker-compose.win.yml down
```

## 四、配置修改

### 修改数据库密码

编辑 `docker-compose.win.yml`，找到以下字段：

```yaml
environment:
  MYSQL_ROOT_PASSWORD: Root@2024Secure
  MYSQL_PASSWORD: SvSaas@2024Secure
```

改为你的密码，然后重启：

```powershell
docker-compose -f docker-compose.win.yml down
docker-compose -f docker-compose.win.yml up -d
```

### 修改 SECRET_KEY（重要！）

生成随机密钥：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

编辑 `docker-compose.win.yml`，替换：

```yaml
SECRET_KEY: 这里粘贴你生成的随机字符串
```

### 配置 AI 服务密钥

后端容器内需要配置 AI 服务密钥，在 `docker-compose.win.yml` 的 `backend` 服务中添加环境变量：

```yaml
environment:
  # ... 其他配置 ...
  JIMENG_API_KEY: 你的即梦API密钥
  KLING_API_KEY: 你的可灵API密钥
  OPENAI_API_KEY: 你的大模型API密钥
```

### 配置微信支付/支付宝

在 `docker-compose.win.yml` 的 `backend` 服务中添加：

```yaml
environment:
  # 微信支付
  WECHAT_APPID: 你的微信AppID
  WECHAT_MCH_ID: 你的商户号
  WECHAT_API_KEY: 你的APIv3密钥
  WECHAT_NOTIFY_URL: http://localhost/api/payments/wechat/notify
  
  # 支付宝
  ALIPAY_APP_ID: 你的支付宝应用ID
  ALIPAY_PRIVATE_KEY: 你的应用私钥
  ALIPAY_PUBLIC_KEY: 你的支付宝公钥
  ALIPAY_NOTIFY_URL: http://localhost/api/payments/alipay/notify
```

## 五、常用运维命令

### 查看服务状态
```powershell
docker-compose -f docker-compose.win.yml ps
```

### 查看后端日志
```powershell
docker-compose -f docker-compose.win.yml logs -f backend
```

### 查看 Celery 日志
```powershell
docker-compose -f docker-compose.win.yml logs -f celery-worker
```

### 重启后端
```powershell
docker-compose -f docker-compose.win.yml restart backend celery-worker
```

### 进入后端容器
```powershell
docker exec -it sv_win_backend powershell
# 或
docker exec -it sv_win_backend /bin/bash
```

### 进入 MySQL 容器
```powershell
docker exec -it sv_win_mysql mysql -uroot -pRoot@2024Secure short_video_saas
```

### 备份数据库
```powershell
docker exec sv_win_mysql mysqldump -uroot -pRoot@2024Secure short_video_saas > backup.sql
```

### 清理未使用的镜像
```powershell
docker image prune -a
```

## 六、故障排查

### 1. 容器启动失败

```powershell
# 查看具体错误日志
docker-compose -f docker-compose.win.yml logs backend

# 重建并启动
docker-compose -f docker-compose.win.yml up -d --force-recreate backend
```

### 2. 前端无法访问

检查前端是否已构建：
```powershell
ls frontend-user\dist
ls frontend-admin\dist
```

如果没有 `dist` 目录，重新构建：
```powershell
cd frontend-user && npm run build
cd ../frontend-admin && npm run build
```

### 3. 后端连接数据库失败

检查 MySQL 是否启动：
```powershell
docker exec sv_win_mysql mysqladmin ping -uroot -pRoot@2024Secure
```

### 4. 端口冲突

如果 80 或 3306 端口被占用，修改 `docker-compose.win.yml` 中的端口映射：

```yaml
ports:
  - "8080:80"    # 将 80 端口改为 8080
  - "3307:3306"  # 将 3306 端口改为 3307
```

### 5. Docker 内存不足

Docker Desktop 默认内存限制为 2GB，建议调整为 4GB+：
- 打开 Docker Desktop -> Settings -> Resources -> Memory
- 调整为 4096 MB 或更高

## 七、安全注意事项

⚠️ **当前配置为本地开发/测试用途，生产环境请注意：**

1. **不要将本项目暴露在公网**，除非你：
   - 配置了域名 + SSL 证书
   - 修改了所有默认密码
   - 配置了防火墙规则

2. **修改默认密码**：
   - MySQL root 密码
   - SECRET_KEY
   - 支付平台密钥

3. **如需外网访问**，建议：
   - 购买域名并配置 DNS
   - 申请 SSL 证书（Let's Encrypt）
   - 修改 `nginx/nginx.win.conf` 为 HTTPS 配置
   - 或使用 `nginx/nginx.conf`（已有 HTTPS 模板）

## 八、数据持久化

所有数据通过 Docker 卷持久化：

| 数据 | 存储位置 |
|------|---------|
| MySQL 数据 | Docker volume: mysql_data |
| Redis 数据 | Docker volume: redis_data |
| 视频文件 | Docker volume: video_storage |
| 日志 | ./logs/ 目录 |

备份数据：
```powershell
# 导出 MySQL 数据
docker exec sv_win_mysql mysqldump -uroot -pRoot@2024Secure short_video_saas > backup_$(Get-Date -Format yyyyMMdd).sql

# 导出视频文件
docker run --rm -v sv_win_video_storage:/data -v ${PWD}:/backup alpine tar czf /backup/videos_$(Get-Date -Format yyyyMMdd).tar.gz -C /data .
```