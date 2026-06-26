# 爆款短视频复刻SaaS平台 - 生产环境部署指南

## 一、生产环境架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (HTTPS)    │
                    │  :443       │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
      ┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
      │  用户端    │  │ 管理后台  │  │ 静态资源  │
      │  SPA      │  │  SPA     │  │  /videos │
      └─────┬─────┘  └────┬─────┘  └──────────┘
            │              │
            └──────┬───────┘
                   │
            ┌──────▼───────┐
            │  FastAPI     │
            │  :8000       │
            │  (Gunicorn)  │
            └──────┬───────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
  ┌─────▼───┐ ┌───▼───┐ ┌───▼────┐
  │ MySQL   │ │ Redis  │ │Celery  │
  │ :3306   │ │ :6379  │ │Worker  │
  └─────────┘ └────────┘ └────────┘
```

---

## 二、服务器要求

| 配置 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 50GB SSD | 100GB+ SSD |
| 带宽 | 5Mbps | 10Mbps+ |

---

## 三、部署步骤

### 1. 服务器初始化

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip \
    nginx redis-server mysql-server npm curl wget ffmpeg

# 设置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 数据库配置

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE short_video_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sv_saas'@'localhost' IDENTIFIED BY 'your-strong-password';
GRANT ALL PRIVILEGES ON short_video_saas.* TO 'sv_saas'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 导入初始化脚本
mysql -u sv_saas -p short_video_saas < /opt/short-video/backend/init.sql
```

### 3. Redis 配置

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 4. 后端部署

```bash
# 创建应用目录
sudo mkdir -p /opt/short-video
cd /opt/short-video

# 上传项目代码（或使用 Git）
git clone <your-repo> .

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cp backend/.env.example backend/.env
nano backend/.env
# 编辑以下关键配置：
# - SECRET_KEY: 生成随机密钥
# - DATABASE_URL: 指向 MySQL
# - WECHAT_MCH_ID / WECHAT_API_KEY: 微信支付配置
# - ALIPAY_APP_ID / ALIPAY_PRIVATE_KEY: 支付宝配置

# 创建必要的目录
mkdir -p videos temp
chmod 755 videos temp
```

### 5. 前端构建

```bash
# 用户端前端
cd frontend-user
npm install
npm run build
# 产物在 dist/ 目录

# 管理后台前端
cd ../frontend-admin
npm install
npm run build
# 产物在 dist/ 目录
```

### 6. Nginx 配置

```nginx
# /etc/nginx/sites-available/short-video

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # 用户端前端
    location / {
        root /opt/short-video/frontend-user/dist;
        try_files $uri $uri/ /index.html;
    }

    # 管理后台前端
    location /admin/ {
        alias /opt/short-video/frontend-admin/dist/;
        try_files $uri $uri/ /admin/index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }

    # 视频文件静态托管
    location /videos/ {
        alias /opt/short-video/videos/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Swagger 文档（生产环境建议关闭或加认证）
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/short-video /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Gunicorn + Supervisor 守护进程

```ini
# /etc/supervisor/conf.d/short-video.conf

[program:short-video-backend]
command=/opt/short-video/venv/bin/gunicorn app.main:app -c /opt/short-video/backend/gunicorn_conf.py
directory=/opt/short-video/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/short-video/backend.err.log
stdout_logfile=/var/log/short-video/backend.out.log

[program:short-video-celery]
command=/opt/short-video/venv/bin/celery -A app.tasks.celery_app worker -l info -c 4
directory=/opt/short-video/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/short-video/celery.err.log
stdout_logfile=/var/log/short-video/celery.out.log
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 8. SSL 证书（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 3 * * * certbot renew --quiet
```

---

## 四、安全加固

### 1. 修改默认密钥

```bash
# 生成强随机密钥
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# 将此值填入 .env 的 SECRET_KEY
```

### 2. 数据库安全

```sql
-- 禁止远程 root 登录
UPDATE mysql.user SET Host='localhost' WHERE User='root';
FLUSH PRIVILEGES;
```

### 3. 防火墙规则

```bash
sudo ufw deny 3306/tcp   # MySQL 不对外开放
sudo ufw deny 6379/tcp   # Redis 不对外开放
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 4. 隐藏 API 文档（可选）

在 `backend/.env` 中设置 `DEBUG=false`，FastAPI 将不再暴露 /docs。

---

## 五、监控与维护

### 日志查看

```bash
# 后端日志
sudo tail -f /var/log/short-video/backend.err.log

# Celery 日志
sudo tail -f /var/log/short-video/celery.err.log

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 定期备份

```bash
#!/bin/bash
# /opt/backup.sh
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u sv_saas -p'your-password' short_video_saas | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份视频文件
tar -czf $BACKUP_DIR/videos_$DATE.tar.gz -C /opt/short-video/videos .

# 保留30天
find $BACKUP_DIR -mtime +30 -delete
```

```bash
crontab -e
# 每天凌晨2点备份
0 2 * * * /opt/backup.sh
```

---

## 六、性能优化建议

1. **数据库索引**：确保 `users.phone`、`users.wechat_openid`、`orders.user_id` 等字段有索引
2. **Redis 缓存**：热点数据（如套餐列表）使用 Redis 缓存
3. **CDN 加速**：视频文件上传至 OSS/CDN
4. **Gunicorn Workers**：根据 CPU 核心数调整，公式 `2*CPU+1`
5. **Celery Concurrency**：根据服务器内存调整 worker 数量
6. **HTTPS**：生产环境必须启用 HTTPS