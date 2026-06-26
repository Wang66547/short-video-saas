# 爆款短视频复刻SaaS平台 - 本地启动教程

## 一、环境准备

### 1. 系统要求
- Windows 10/11 或 Linux/macOS
- Python 3.10+
- Node.js 16+
- MySQL 8.0+
- Redis 7.0+
- FFmpeg 6.0+

### 2. 安装依赖

#### Python依赖
`ash
cd backend
pip install -r requirements.txt
`

#### 前端依赖
`ash
# 用户端
cd frontend-user
npm install

# 管理后台
cd ../frontend-admin
npm install
`

## 二、数据库配置

### 1. 创建数据库
`sql
CREATE DATABASE short_video_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
`

### 2. 配置环境变量
复制 .env.example 为 .env 并修改：
`ash
cp backend/.env.example backend/.env
`

编辑 ackend/.env：
`env
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/short_video_saas
DATABASE_SYNC_URL=mysql+pymysql://root:your_password@localhost:3306/short_video_saas
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-min-32-chars
`

## 三、启动服务

### 1. 启动MySQL和Redis
`ash
# 使用Docker Compose（推荐）
docker-compose up -d mysql redis
`

### 2. 启动后端
`ash
cd backend
uvicorn app.main:app --reload --port 8000
`

### 3. 启动Celery Worker
`ash
cd backend
celery -A app.tasks.celery_app worker -l info
`

### 4. 启动前端
`ash
# 用户端（端口5173）
cd frontend-user
npm run dev

# 管理后台（端口5174）
cd ../frontend-admin
npm run dev
`

## 四、访问地址

- 用户端：http://localhost:5173
- 管理后台：http://localhost:5174/admin
- API文档：http://localhost:8000/docs
- Celery Flower：http://localhost:5555

## 五、测试流程

1. 注册用户
2. 登录
3. 创建视频解析任务
4. 查看解析结果
5. 创建生成任务
6. 查看生成结果
7. 浏览会员套餐
8. 兑换卡密（如有）
9. 创建订单并支付（模拟）
10. 查看订单记录

## 六、生产环境部署

### 1. 使用Docker Compose
`ash
docker-compose up -d
`

### 2. 配置Nginx
编辑 
ginx/nginx.conf，配置域名和SSL证书。

### 3. 环境变量
生产环境务必修改：
- SECRET_KEY：使用强随机字符串
- 数据库密码
- 微信支付API密钥
- 支付宝私钥/公钥
- 短信服务AK/SK

## 七、常见问题

### Q: 数据库连接失败
A: 检查MySQL是否运行， DATABASE_URL配置是否正确

### Q: Redis连接失败
A: 检查Redis是否运行，REDIS_URL配置是否正确

### Q: FFmpeg未找到
A: 安装FFmpeg并添加到系统PATH

### Q: Celery任务不执行
A: 检查Celery Worker是否启动，Redis是否正常

### Q: 前端请求跨域
A: 检查CORS_ORIGINS配置，确保包含前端地址
