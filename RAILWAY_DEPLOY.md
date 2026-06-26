# Railway 部署指南

## 简介

项目已内置 Railway 一键部署配置，使用 Docker 构建，支持 MySQL + Redis 插件。

## 部署前准备

1. **GitHub 账号** - 需要将代码推送到 GitHub
2. **Railway 账号** - 注册 https://railway.app/
3. **代码已推送到 GitHub 仓库**

## 快速部署（5 步）

### 第 1 步：创建 Railway 项目

1. 登录 https://railway.app/
2. 点击 "Start a New Project"
3. 选择 "Deploy from GitHub repo"
4. 授权并选择你的项目仓库

### 第 2 步：添加 MySQL 插件

1. 在项目 Dashboard 点击 "+ New"
2. 选择 "Database" → "MySQL"
3. 等待 MySQL 启动完成（约 1-2 分钟）

> Railway 的 MySQL 插件会自动设置 `MYSQL_URL` 环境变量，启动脚本会自动识别并转换格式。

### 第 3 步：添加 Redis 插件（推荐）

1. 点击 "+ New"
2. 选择 "Database" → "Redis"
3. 等待 Redis 启动完成

> Redis 用于缓存、限流、异步任务队列。不添加也能运行，但限流等功能会自动降级。

### 第 4 步：配置环境变量

在项目 Settings → Variables 中添加以下变量：

| 变量名 | 必填 | 说明 | 默认值 |
|--------|------|------|--------|
| `SECRET_KEY` | ✅ 建议 | JWT 密钥，建议 32 位以上随机字符串 | 自动生成（重启会变） |
| `ENV` | ❌ | 运行环境，设为 `production` | - |
| `DEBUG` | ❌ | 调试模式，生产环境设为 `false` | `false` |

**生成 SECRET_KEY 的方法：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 第 5 步：触发部署

1. 推送代码到 GitHub 会自动触发部署
2. 或在 Railway 项目页面点击 "Redeploy"
3. 等待构建和部署完成（约 3-5 分钟）

部署成功后，在 Railway 项目的 "Deployments" 页面可以看到访问地址。

## 访问地址

部署成功后，Railway 会分配一个域名，格式类似：
- `https://your-project-name.up.railway.app/`

访问路径：
- **用户端**: `https://你的域名.up.railway.app/`
- **管理端**: `https://你的域名.up.railway.app/admin/`
- **API 文档**: `https://你的域名.up.railway.app/docs`

## 默认账号

### 管理员账号
- 用户名: `admin`
- 密码: `Admin@123`

> ⚠️ 登录后请立即修改默认密码！

### 测试用户账号
- 手机号: `13800138000`
- 密码: `13800138000`

## 常用配置

### 开启/关闭用户注册

在环境变量中添加：
```
REGISTRATION_ENABLED=true   # 开启注册
REGISTRATION_ENABLED=false  # 关闭注册
```

### 修改免费用户额度

```
FREE_DAILY_PARSE_LIMIT=5     # 每日解析次数
FREE_DAILY_GENERATE_LIMIT=2  # 每日生成次数
```

### 配置支付（可选）

微信支付：
```
WECHAT_APPID=你的AppID
WECHAT_MCH_ID=你的商户号
WECHAT_API_KEY=你的APIv3密钥
WECHAT_NOTIFY_URL=https://你的域名/api/payments/wechat/notify
```

支付宝：
```
ALIPAY_APP_ID=你的应用ID
ALIPAY_PRIVATE_KEY=你的应用私钥
ALIPAY_PUBLIC_KEY=你的支付宝公钥
ALIPAY_NOTIFY_URL=https://你的域名/api/payments/alipay/notify
```

### 配置 AI 服务（可选）

即梦 AI（视频生成）：
```
JIMENG_API_KEY=你的即梦APIKey
```

可灵 AI（视频生成）：
```
KLING_API_KEY=你的可灵APIKey
```

## 常见问题

### Q: 部署失败怎么办？

A: 查看 Railway 的 Deploy Logs，常见原因：
1. MySQL 还没启动好就开始部署 → 等 MySQL 就绪后重新部署
2. SECRET_KEY 太短 → 确保 32 位以上
3. 构建超时 → 检查 Dockerfile 是否正确

### Q: 页面能打开但接口报错？

A: 检查：
1. 数据库是否正常连接
2. 环境变量 `DATABASE_URL` 是否正确
3. 查看后端日志：Railway → Deployments → View Logs

### Q: 视频上传/生成失败？

A: Railway 免费版的磁盘空间有限，且容器重启后数据会丢失。视频存储建议：
- 接入阿里云 OSS / 腾讯云 COS
- 或使用其他对象存储服务

### Q: 如何自定义域名？

A: 在 Railway 项目 Settings → Domains 中添加自定义域名，然后：
1. 将你的域名 CNAME 解析到 Railway 提供的地址
2. 等待 SSL 证书自动签发
3. 更新环境变量中的回调地址等配置

### Q: Redis 必须加吗？

A: 不是必须的。没有 Redis 时：
- 限流功能会自动关闭（不限制请求频率）
- Token 黑名单不生效（但 JWT 本身有过期时间）
- 缓存功能不可用
- 异步任务可能无法正常工作（Celery 需要 Redis）

## 费用说明

Railway 提供免费试用额度（约 $5 试用金），超出后按需付费：
- 基础部署（1 个服务 + MySQL + Redis）约 $10-20/月
- 具体价格参考: https://railway.app/pricing

## 升级到更高配置

如果需要更好的性能，可以：

1. **升级服务规格**: Railway → Settings → Service → Resources
2. **添加 Celery Worker**: 单独部署一个 Worker 服务处理异步任务
3. **使用 CDN**: 静态资源和视频走 CDN 加速

## 部署架构

```
┌─────────────────────────────────────┐
│           Railway 平台               │
│  ┌───────────────────────────────┐  │
│  │     Web 服务 (单容器)          │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Gateway (Python HTTP)  │  │  │
│  │  │  - 静态资源托管          │  │  │
│  │  │  - API 反向代理          │  │  │
│  │  └───────────┬─────────────┘  │  │
│  │              │                │  │
│  │  ┌───────────▼─────────────┐  │  │
│  │  │  FastAPI 后端 (Uvicorn) │  │  │
│  │  └───────────┬─────────────┘  │  │
│  └──────────────┼────────────────┘  │
│                 │                   │
│  ┌──────────────▼───┐  ┌────────┐  │
│  │   MySQL 数据库    │  │ Redis  │  │
│  │  (Railway 插件)   │  │(插件)  │  │
│  └──────────────────┘  └────────┘  │
└─────────────────────────────────────┘
```
