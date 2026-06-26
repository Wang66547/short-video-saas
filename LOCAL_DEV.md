# 爆款短视频复刻SaaS平台 - 本地启动教程

## 一、环境要求

| 软件 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端运行环境 |
| MySQL | 8.0+ | 关系型数据库 |
| Redis | 7.0+ | 缓存和消息队列 |
| FFmpeg | 6.0+ | 视频处理（可选，用于视频解析） |

---

## 二、快速启动（Docker Compose 一键部署）

### 1. 克隆项目

```bash
cd D:\ai\codex\爆款短视频复刻
```

### 2. 配置环境变量

```powershell
# 复制环境变量模板
Copy-Item backend\.env.example backend\.env
# 编辑 backend\.env 文件，填入实际配置
notepad backend\.env
```

### 3. 启动全部服务

```powershell
docker-compose up -d
```

这将启动：
- MySQL 8.0（端口 3306）
- Redis 7.0（端口 6379）
- FastAPI 后端（端口 8000）
- Celery Worker（视频异步处理）
- Nginx 反向代理（端口 80）

### 4. 初始化数据库

```powershell
# 等待 MySQL 启动后执行
docker exec -i sv_saas_mysql mysql -uroot -proot123 < backend/init.sql
```

### 5. 初始化系统配置

登录管理后台后，进入「系统配置」页面，点击「初始化默认配置」按钮。

### 6. 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 用户端 | http://localhost | Vue 3 前端 |
| 管理后台 | http://localhost/admin | Vue 3 管理后台 |
| API文档 | http://localhost/docs | Swagger 交互式文档 |
| Celery Flower | http://localhost:5555 | 任务监控面板 |

---

## 三、本地开发启动

### 后端开发模式

```powershell
# 1. 激活虚拟环境
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
Copy-Item .env.example .env
notepad .env

# 4. 初始化数据库
mysql -uroot -p < init.sql

# 5. 启动后端服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动 Celery Worker

```powershell
# 新终端窗口
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.tasks.celery_app worker -l info -c 4
```

### 用户端前端开发模式

```powershell
cd frontend-user
npm install
npm run dev
# 访问 http://localhost:5173
```

### 管理后台前端开发模式

```powershell
cd frontend-admin
npm install
npm run dev
# 访问 http://localhost:3000
```

---

## 四、管理员初始账号

| 字段 | 值 |
|------|-----|
| 昵称（账号） | admin |
| 密码 | Admin@123 |

> 首次登录后建议在系统配置中修改默认密码。

---

## 五、常见问题

### Q1: MySQL 连接失败
确保 MySQL 服务已启动，检查 `.env` 中的 `DATABASE_URL` 配置。

### Q2: Redis 连接失败
确保 Redis 服务已启动，检查 `.env` 中的 `REDIS_URL` 配置。

### Q3: 前端请求 404
检查 `vite.config.js` 中的 proxy 配置是否正确指向后端地址。

### Q4: Celery Worker 启动失败
检查 `CELERY_BROKER_URL` 是否正确指向 Redis。

### Q5: 微信支付/支付宝无法测试
需要真实的商户资质和证书文件，开发阶段可使用模拟数据。

---

## 六、FFmpeg 安装（可选）

如果需要视频解析功能，请安装 FFmpeg：

### Windows
```powershell
# 使用 winget 安装
winget install FFmpeg
# 或手动下载：https://ffmpeg.org/download.html
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install -y ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

安装后验证：
```bash
ffmpeg -version
```