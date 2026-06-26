# ============================================================
# 生产环境安全加固脚本
# 部署在服务器上执行
# ============================================================

# 1. 创建必要的目录结构
mkdir -p /data/mysql /data/redis /data/videos /data/temp /data/backups/mysql
mkdir -p /etc/nginx/ssl /var/log/nginx /var/log/celery /var/log/backend
mkdir -p /opt/short-video

# 2. 设置目录权限
chmod 700 /data/mysql
chmod 700 /data/redis
chmod 755 /data/videos
chmod 777 /data/temp
chmod 755 /etc/nginx/ssl

# 3. 创建 .env 文件（从模板）
cp /opt/short-video/.env.example /opt/short-video/.env
# 编辑 .env 填入实际值
# nano /opt/short-video/.env

# 4. 生成安全的 SECRET_KEY
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" >> /opt/short-video/.env

# 5. 生成 SSL 证书（Let's Encrypt）
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d www.yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com

# 6. 配置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 3306/tcp    # MySQL 不对外
ufw deny 6379/tcp    # Redis 不对外
ufw deny 8000/tcp    # 后端不直连
ufw enable

# 7. 配置日志轮转
cat > /etc/logrotate.d/short-video << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}

/var/log/backend/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
}

/var/log/celery/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
}
EOF

# 8. 配置数据库定时备份
cat > /opt/short-video/backup-mysql.sh << 'BASH'
#!/bin/bash
BACKUP_DIR="/data/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_USER="${MYSQL_USER:-sv_saas}"
DB_PASS="${MYSQL_PASSWORD:-SvSaas@2024Secure}"
DB_NAME="${MYSQL_DATABASE:-short_video_saas}"

# 备份数据库
mysqldump -u"$DB_USER" -p"$DB_PASS" --single-transaction --routines --triggers "$DB_NAME" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 保留最近 30 天的备份
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "$(date): Backup completed: db_$DATE.sql.gz" >> "$BACKUP_DIR/backup.log"
BASH
chmod +x /opt/short-video/backup-mysql.sh

# 添加到 crontab（每天凌晨2点备份）
# (crontab -l 2>/dev/null; echo "0 2 * * * /opt/short-video/backup-mysql.sh") | crontab -

# 9. 配置视频存储清理（超过7天的临时文件）
cat > /opt/short-video/cleanup-temp.sh << 'BASH'
#!/bin/bash
# 清理临时目录
find /data/temp -type f -mtime +1 -delete
# 清理视频存储中超过30天的文件
find /data/videos -type f -mtime +30 -delete
# 清理日志
find /var/log -name "*.log.gz" -mtime +90 -delete
BASH
chmod +x /opt/short-video/cleanup-temp.sh

# 添加到 crontab（每天凌晨3点清理）
# (crontab -l 2>/dev/null; echo "0 3 * * * /opt/short-video/cleanup-temp.sh") | crontab -

# 10. 启动服务
cd /opt/short-video
docker-compose -f docker-compose.prod.yml up -d

# 11. 验证部署
sleep 10
curl -f http://localhost/health || echo "Backend health check failed"
curl -f https://yourdomain.com || echo "HTTPS check failed"