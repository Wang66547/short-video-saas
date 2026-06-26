# ============================================================
# 横向扩容方案 - 分布式视频处理集群
# ============================================================

# 当视频处理量增大时，可按以下方案扩容：

# ==================== 1. Celery Worker 水平扩展 ====================

# 方法A: Docker Compose 增加副本
# 在 docker-compose.prod.yml 中修改:
#   celery-worker:
#     deploy:
#       replicas: 4   # 从1扩展到4个worker

# 方法B: 使用 Kubernetes
# kubectl scale deployment celery-worker --replicas=8

# ==================== 2. 数据库读写分离 ====================

# 主库（写）: mysql-master:3306
# 从库（读）: mysql-slave1:3306, mysql-slave2:3306

# 修改 .env:
# DATABASE_URL=mysql+aiomysql://user:pass@mysql-master:3306/db
# DATABASE_READ_URL=mysql+aiomysql://user:pass@mysql-slave1:3306/db

# 在 SQLAlchemy 中配置读写分离:
# from sqlalchemy import create_engine
# engine = create_engine(DATABASE_URL)
# read_engine = create_engine(DATABASE_READ_URL)

# ==================== 3. Redis 集群 ====================

# 单机 Redis -> Redis Cluster (6节点: 3主3从)
# redis-0:6379 (master)
# redis-1:6379 (master)
# redis-2:6379 (master)
# redis-3:6379 (slave of 0)
# redis-4:6379 (slave of 1)
# redis-5:6379 (slave of 2)

# 修改 .env:
# REDIS_URL=redis://:pass@redis-cluster:6379/0
# CELERY_BROKER_URL=redis://:pass@redis-cluster:6379/1

# ==================== 4. Nginx 负载均衡 ====================

# 在 nginx.prod.conf 中:
# upstream backend_api {
#     ip_hash;  # 会话保持
#     server backend1:8000 weight=5;
#     server backend2:8000 weight=5;
#     server backend3:8000 weight=3;
#     server backend4:8000 weight=3;
#     keepalive 64;
# }

# ==================== 5. 对象存储（视频文件） ====================

# 本地存储 -> 阿里云 OSS / AWS S3

# 修改 .env:
# STORAGE_TYPE=oss          # 或 s3
# OSS_BUCKET=your-bucket
# OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
# OSS_ACCESS_KEY_ID=LTAI...
# OSS_ACCESS_KEY_SECRET=...
# S3_BUCKET=your-bucket
# S3_REGION=us-east-1
# S3_ACCESS_KEY=...
# S3_SECRET_KEY=...

# 在 services 中适配:
# from app.services.storage import get_storage
# storage = get_storage()  # 自动选择本地/OSS/S3

# ==================== 6. CDN 加速 ====================

# 静态资源 + 视频文件走 CDN
# 域名规划:
#   yourdomain.com       -> 前端 + API
#   cdn.yourdomain.com   -> 视频文件 + 静态资源
#   api.yourdomain.com   -> API 反向代理

# Nginx 配置:
# location /videos/ {
#     proxy_pass https://cdn.yourdomain.com/videos/;
#     expires 365d;
# }

# ==================== 7. 监控告警 ====================

# 7.1 Prometheus + Grafana
# docker-compose 中添加:
#   prometheus:
#     image: prom/prometheus:latest
#     volumes:
#       - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
#     ports:
#       - "9090:9090"
#
#   grafana:
#     image: grafana/grafana:latest
#     ports:
#       - "3001:3000"
#
#   node-exporter:
#     image: prom/node-exporter:latest
#     ports:
#       - "9100:9100"

# 7.2 FastAPI 指标中间件
# pip install prometheus-fastapi-instrumentator
# 在 main.py 中:
#   from prometheus_fastapi_instrumentator import Instrumentator
#   Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# 7.3 告警规则 (alertmanager)
# 规则示例:
#   - alert: HighErrorRate
#     expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
#     for: 2m
#     labels:
#       severity: critical
#     annotations:
#       summary: "API 错误率超过 5%"

# ==================== 8. 容量规划参考 ====================

# 单台 4C8G 服务器:
#   - 1x MySQL (主)
#   - 1x Redis
#   - 1x Backend (Gunicorn 4 workers)
#   - 2x Celery Worker
#   - 1x Nginx
#   承载: ~500 DAU, ~100 并发解析

# 双机高可用:
#   - Server A: MySQL主 + Backend + Nginx
#   - Server B: MySQL从 + Celery Workers + Nginx(备用)
#   - 独立 Redis 集群 + OSS 存储
#   承载: ~2000 DAU, ~500 并发解析

# 集群方案:
#   - K8s 集群 (3 master + 5 worker)
#   - MySQL MGR (3节点)
#   - Redis Cluster (6节点)
#   - Nginx + Keepalived (VIP漂移)
#   - OSS/S3 对象存储
#   承载: ~10000+ DAU, 弹性伸缩