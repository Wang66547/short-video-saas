# ============================================================
# 爆款短视频复刻SaaS平台 - 完整部署手册
# ============================================================

## 一、环境要求

### 最低硬件配置
| 组件 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发/测试 | 2核 | 4GB | 20GB |
| 生产（单台） | 4核 | 8GB | 100GB SSD |
| 生产（集群） | 16核+ | 32GB+ | 500GB+ SSD |

### 软件依赖
- Docker >= 20.10
- Docker Compose >= 2.0
- FFmpeg >= 6.0（Celery Worker 节点）

---

## 二、快速部署（单台服务器）

### 第1步：准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt install -y docker-compose-plugin

# 验证
docker --version
docker compose version
```

### 第2步：上传项目

```bash
# 创建项目目录
mkdir -p /opt/short-video && cd /opt/short-video

# 上传项目代码（Git 或 SCP）
git clone <your-repo> .
# 或: scp -r ./backend ./frontend-user ./frontend-admin ./nginx ./docker-compose.prod.yml root@server:/opt/short-video/
```

### 第3步：配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑关键配置
nano .env
```

**必须修改的配置项：**
```bash
# 1. 数据库密码
MYSQL_ROOT_PASSWORD=YourStrongPassword123!
MYSQL_PASSWORD=YourStrongPassword123!

# 2. JWT密钥（随机生成）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# 3. 域名
CORS_ORIGINS='["https://yourdomain.com"]'
WECHAT_NOTIFY_URL=https://yourdomain.com/api/payments/wechat/notify
ALIPAY_NOTIFY_URL=https://yourdomain.com/api/payments/alipay/notify

# 4. 支付密钥（接入时填写）
WECHAT_MCH_ID=
WECHAT_API_KEY=
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
```

### 第4步：准备 SSL 证书

```bash
# 创建证书目录
sudo mkdir -p /etc/nginx/ssl

# 生成自签名证书（测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/privkey.pem \
  -out /etc/nginx/ssl/fullchain.pem \
  -subj "/CN=yourdomain.com"

# 或使用 Let's Encrypt（生产推荐）
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
# 证书位置: /etc/letsencrypt/live/yourdomain.com/
# 复制证书到 Nginx 目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /etc/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /etc/nginx/ssl/
```

### 第5步：修改 Nginx 配置

```bash
# 编辑 Nginx 配置，替换域名
sed -i 's/yourdomain.com/yourdomain.com/g' nginx/nginx.prod.conf

# 确保 SSL 证书路径正确
# ssl_certificate     /etc/nginx/ssl/fullchain.pem;
# ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

### 第6步：初始化数据库

```bash
# 启动服务（先只启动 MySQL 和 Redis）
docker compose -f docker-compose.prod.yml up -d mysql redis

# 等待数据库启动
sleep 15

# 检查数据库健康状态
docker compose -f docker-compose.prod.yml ps

# 导入初始化脚本
docker compose -f docker-compose.prod.yml exec mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} short_video_saas < backend/init.sql

# 初始化系统配置（通过 API）
# 登录管理后台后，在「系统配置」页面点击「初始化默认配置」
```

### 第7步：构建前端

```bash
# 用户端前端
cd frontend-user
npm install
npm run build
# 产物在 dist/ 目录，会被 Nginx 挂载

# 管理后台前端
cd ../frontend-admin
npm install
npm run build
# 产物在 dist/ 目录
```

### 第8步：启动全部服务

```bash
cd /opt/short-video

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery-worker
```

### 第9步：验证部署

```bash
# 健康检查
curl http://localhost/health
# 预期: {"code":200,"message":"ok","data":{"status":"running"}}

# HTTPS 检查
curl -k https://localhost
# 应返回前端页面

# API 文档
# https://yourdomain.com/docs

# 管理后台
# https://yourdomain.com/admin
```

---

## 三、日常运维

### 查看日志

```bash
# 后端日志
docker compose -f docker-compose.prod.yml logs -f backend

# Celery Worker 日志
docker compose -f docker-compose.prod.yml logs -f celery-worker

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 系统日志
journalctl -u docker -f
```

### 服务管理

```bash
# 重启后端
docker compose -f docker-compose.prod.yml restart backend

# 重启所有服务
docker compose -f docker-compose.prod.yml restart

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 停止并删除数据卷（谨慎！）
docker compose -f docker-compose.prod.yml down -v
```

### 数据库备份

```bash
# 手动备份
docker compose -f docker-compose.prod.yml exec mysql mysqldump -uroot -p$MYSQL_ROOT_PASSWORD short_video_saas > backup_$(date +%Y%m%d).sql

# 自动备份（已配置 cron）
# 每天凌晨2点自动备份，保留30天
```

### 版本更新

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建
docker compose -f docker-compose.prod.yml build --no-cache backend

# 3. 滚动更新
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# 4. 验证
curl http://localhost/health
```

---

## 四、故障排查

### 常见问题

**Q1: 后端无法连接数据库**
```bash
# 检查 MySQL 是否启动
docker compose -f docker-compose.prod.yml ps mysql

# 检查数据库密码是否正确
docker compose -f docker-compose.prod.yml exec mysql mysql -uroot -p

# 检查网络连接
docker compose -f docker-compose.prod.yml exec backend ping mysql
```

**Q2: Celery Worker 不处理任务**
```bash
# 检查 Celery 状态
docker compose -f docker-compose.prod.yml exec celery-worker celery -A app.tasks.celery_app inspect ping

# 查看 Worker 日志
docker compose -f docker-compose.prod.yml logs -f celery-worker

# 检查 Redis Broker
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

**Q3: Nginx 返回 502**
```bash
# 检查后端是否运行
docker compose -f docker-compose.prod.yml ps backend

# 检查后端日志
docker compose -f docker-compose.prod.yml logs backend

# 检查端口映射
netstat -tlnp | grep 8000
```

**Q4: 视频处理超时**
```bash
# 增加超时时间
# 在 nginx.prod.conf 中:
proxy_read_timeout 600s;
proxy_send_timeout 600s;

# 增加 Celery 超时
# CELERY_TASK_TIME_LIMIT=600
# CELERY_TASK_SOFT_TIME_LIMIT=540
```

---

## 五、性能调优

### MySQL 优化

```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 优化索引
ANALYZE TABLE users;
ANALYZE TABLE orders;
ANALYZE TABLE parse_records;

-- 调整 InnoDB 缓冲池
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB
```

### Redis 优化

```bash
# 查看内存使用
redis-cli info memory

# 查看慢查询
redis-cli slowlog get 10

# 清理过期键
redis-cli --scan --pattern '*' | xargs redis-cli TTL | awk '$2 < 0 {print $1}' | xargs redis-cli DEL
```

### Nginx 优化

```nginx
# 在 nginx.prod.conf 中添加:
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 10240;
    multi_accept on;
    use epoll;
}

http {
    # 开启 gzip 压缩
    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # 开启 sendfile
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # 连接超时
    keepalive_timeout 65;
    keepalive_requests 1000;
}
```

---

## 六、安全加固清单

- [ ] 修改所有默认密码
- [ ] 生成强 SECRET_KEY
- [ ] 配置 HTTPS 证书
- [ ] 关闭不必要的端口（3306/6379 不对外）
- [ ] 配置防火墙规则
- [ ] 启用日志轮转
- [ ] 配置数据库定时备份
- [ ] 限制 API 访问频率
- [ ] 隐藏 /docs 端点（生产环境）
- [ ] 配置 SSL 安全头
- [ ] 定期更新 Docker 镜像
- [ ] 监控磁盘使用率