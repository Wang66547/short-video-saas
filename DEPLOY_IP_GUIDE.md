# 生产环境部署指南 (IP访问版)

## 一、部署前准备

### 服务器要求
- CPU: 2核及以上（推荐4核）
- 内存: 4GB及以上（推荐8GB）
- 磁盘: 50GB+ SSD
- 操作系统: Ubuntu 20.04+ / CentOS 7+
- 网络: 公网IP，开放80端口

### 本地准备
前端已构建完成：
- `frontend-user/dist/` - 用户端前端
- `frontend-admin/dist/` - 管理端前端

## 二、快速部署

### 方式一：一键部署脚本（推荐）

```bash
# 1. 将整个项目上传到服务器 /opt/short-video/
scp -r ./ user@your-server-ip:/opt/short-video/

# 2. 登录服务器
ssh user@your-server-ip
cd /opt/short-video

# 3. 执行部署脚本
sudo bash deploy-prod.sh
```

### 方式二：手动部署

```bash
# 1. 创建数据目录
sudo mkdir -p /data/mysql /data/redis /data/videos /data/temp
sudo mkdir -p logs/backend logs/celery logs/nginx

# 2. 准备环境变量
cp .env.production .env
# 编辑 .env 修改密码等配置

# 3. 启动服务
docker compose -f docker-compose.prod-ip.yml up -d --build
```

## 三、部署后验证

### 访问地址
- 用户端: `http://你的服务器IP/`
- 管理端: `http://你的服务器IP/admin/`
- API文档: `http://你的服务器IP/docs`

### 服务检查

```bash
# 查看服务状态
docker compose -f docker-compose.prod-ip.yml ps

# 查看后端日志
docker compose -f docker-compose.prod-ip.yml logs -f backend

# 查看Nginx日志
docker compose -f docker-compose.prod-ip.yml logs -f nginx

# 健康检查
curl http://localhost:80/health
curl http://localhost:8000/health
```

## 四、初始管理员账号

部署完成后，需要创建管理员账号。可以通过以下方式：

```bash
# 进入后端容器
docker exec -it sv_saas_backend bash

# 创建管理员（根据实际接口调整）
python -c "
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            phone='13800138000',
            nickname='超级管理员',
            is_admin=True,
            is_active=True
        )
        admin.hashed_password = get_password_hash('Admin@123456')
        db.add(admin)
        await db.commit()
        print('管理员创建成功: 13800138000 / Admin@123456')

asyncio.run(create_admin())
"
```

## 五、安全加固

### 1. 修改默认密码
编辑 `.env` 文件，修改以下配置：
- `MYSQL_ROOT_PASSWORD` - MySQL root密码
- `MYSQL_PASSWORD` - MySQL应用密码
- `SECRET_KEY` - JWT密钥

### 2. 配置防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw deny 3306/tcp   # MySQL
sudo ufw deny 6379/tcp   # Redis
sudo ufw deny 8000/tcp   # 后端API
sudo ufw enable
```

### 3. 关闭API文档（可选）
编辑 `.env` 设置 `DEBUG=false`，Swagger文档将自动关闭。

## 六、日常维护

### 常用命令

```bash
# 启动服务
docker compose -f docker-compose.prod-ip.yml up -d

# 停止服务
docker compose -f docker-compose.prod-ip.yml down

# 重启服务
docker compose -f docker-compose.prod-ip.yml restart

# 查看所有服务日志
docker compose -f docker-compose.prod-ip.yml logs -f

# 查看单个服务日志
docker compose -f docker-compose.prod-ip.yml logs -f backend
docker compose -f docker-compose.prod-ip.yml logs -f celery-worker
docker compose -f docker-compose.prod-ip.yml logs -f nginx
```

### 数据库备份

```bash
# 备份数据库
docker exec sv_saas_mysql mysqldump -u root -p'你的密码' short_video_saas > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i sv_saas_mysql mysql -u root -p'你的密码' short_video_saas < backup.sql
```

## 七、升级到域名+HTTPS

当你有了域名后，可以按以下步骤升级：

1. 将域名解析到服务器IP
2. 申请SSL证书（推荐Let's Encrypt）
3. 使用 `docker-compose.prod.yml` 替换 `docker-compose.prod-ip.yml`
4. 使用 `nginx/nginx.prod.conf` 替换 `deploy/nginx.ip.conf`
5. 更新 `.env` 中的 `CORS_ORIGINS` 和回调地址

详细说明请参考 `PRODUCTION_DEPLOY.md`。
