content = @\"
# 爆款短视频复刻SaaS平台 - 生产环境部署说明

## 一、服务器要求

### 硬件配置
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 100GB+ SSD（视频存储需要大量空间）
- 带宽: 10Mbps+

### 软件要求
- OS: Ubuntu 20.04+ / CentOS 8+
- Docker: 20.10+
- Docker Compose: 2.0+

## 二、部署步骤

### 1. 克隆代码
`ash
git clone <repository-url>
cd short-video-saas
`

### 2. 配置环境变量
`ash
# 复制并编辑环境变量
cp backend/.env.example backend/.env
`

生产环境必填项：
`env
# 数据库
DATABASE_URL=mysql+aiomysql://user:strong_password@localhost:3306/short_video_saas
DATABASE_SYNC_URL=mysql+pymysql://user:strong_password@localhost:3306/short_video_saas

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT密钥（32位以上随机字符串）
SECRET_KEY=<生成强随机字符串>

# 微信支付
WECHAT_APPID=<你的微信应用ID>
WECHAT_MCH_ID=<你的商户号>
WECHAT_API_KEY=<你的APIv3密钥>
WECHAT_NOTIFY_URL=https://your-domain.com/api/payments/wechat/notify

# 支付宝
ALIPAY_APP_ID=<你的支付宝应用ID>
ALIPAY_PRIVATE_KEY=<你的应用私钥>
ALIPAY_PUBLIC_KEY=<你的支付宝公钥>
ALIPAY_NOTIFY_URL=https://your-domain.com/api/payments/alipay/notify

# 短信服务
ALIBABA_CLOUD_ACCESS_KEY_ID=<你的AccessKey ID>
ALIBABA_CLOUD_ACCESS_KEY_SECRET=<你的AccessKey Secret>
ALIBABA_CLOUD_SMS_TEMPLATE_ID=<你的短信模板ID>
ALIBABA_CLOUD_SIGN_NAME=<你的短信签名>
`

### 3. 构建前端
`ash
# 用户端
cd frontend-user
npm install
npm run build

# 管理后台
cd ../frontend-admin
npm install
npm run build
`

### 4. 启动服务
`ash
# 使用Docker Compose
docker-compose up -d

# 启动Celery Worker
docker-compose up -d celery-worker

# 启动Flower（任务监控）
docker-compose up -d flower
`

## 三、Nginx配置

编辑 
ginx/nginx.conf，配置域名和SSL证书。

## 四、SSL证书

使用Let's Encrypt获取免费SSL证书：
`ash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
`

## 五、数据库初始化

`ash
# 进入后端容器
docker exec -it sv_saas_backend bash

# 初始化数据库
python -c \"from app.database import init_db; import asyncio; asyncio.run(init_db())\"
`

## 六、定时任务

### 取消过期订单
在服务器上添加cron任务：
`ash
# 每小时执行一次
0 * * * * docker exec sv_saas_backend python -c \"from app.services.payment_service import cancel_expired_orders; import asyncio; asyncio.run(cancel_expired_orders())\"
`

## 七、监控和维护

### 1. 查看日志
`ash
docker logs -f sv_saas_backend
docker logs -f sv_saas_celery
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
`

### 2. 监控Celery任务
访问 http://your-domain.com:5555 查看Flower面板

### 3. 备份数据库
`ash
mysqldump -u root -p short_video_saas > backup.sql
`

### 4. 清理临时文件
`ash
find /path/to/temp -type f -mtime +7 -delete
`

## 八、性能优化

### 1. Gunicorn配置
编辑 ackend/gunicorn_conf.py：
`python
bind = \"0.0.0.0:8000\"
workers = 4
worker_class = \"uvicorn.workers.UvicornWorker\"
timeout = 120
`

### 2. 数据库连接池
在 pp/db/session.py 中调整：
`python
pool_size=20
max_overflow=40
pool_recycle=3600
`

### 3. Redis缓存
确保Redis持久化配置正确，定期备份RDB文件。

## 九、安全加固

1. 修改默认数据库密码
2. 使用强SECRET_KEY
3. 配置防火墙，只开放80/443端口
4. 禁用Swagger文档（生产环境）
5. 配置HTTPS
6. 定期更新依赖包
7. 监控异常登录
8. 配置CSRF保护
9. 限制上传文件大小
10. 定期备份数据
\"@
