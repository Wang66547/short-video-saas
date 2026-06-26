# 爆款短视频复刻SaaS平台 - API文档

## 用户认证接口

### 1. 发送短信验证码
- **URL**: `POST /api/auth/send-code`
- **参数**: `phone` (手机号)
- **响应**: 
```json
{
  "code": 200,
  "message": "验证码发送成功",
  "data": {"sent": true}
}
```

### 2. 用户注册
- **URL**: `POST /api/auth/register`
- **参数**: 
```json
{
  "phone": "13800138000",
  "captcha": "123456",
  "password": "123456",
  "nickname": "测试用户"
}
```
- **响应**: 
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {"user_id": 1}
}
```

### 3. 用户登录
- **URL**: `POST /api/auth/login`
- **参数**: 
```json
{
  "phone": "13800138000",
  "password": "123456"
}
```
- **响应**: 
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 4. 微信授权登录
- **URL**: `POST /api/auth/login`
- **参数**: 
```json
{
  "wechat_code": "wx_auth_code"
}
```

### 5. 获取用户信息
- **URL**: `GET /api/auth/me`
- **认证**: 需要JWT Token
- **响应**: 
```json
{
  "id": 1,
  "phone": "13800138000",
  "nickname": "测试用户",
  "avatar": "",
  "membership_level": "free",
  "membership_expire_at": null,
  "remaining_credits": 0,
  "status": "active",
  "last_login_at": "2024-01-01T00:00:00",
  "created_at": "2024-01-01T00:00:00"
}
```

### 6. 更新个人资料
- **URL**: `PUT /api/auth/profile`
- **认证**: 需要JWT Token
- **参数**: 
```json
{
  "nickname": "新昵称",
  "avatar": "https://example.com/avatar.jpg"
}
```

## 解析记录接口

### 1. 创建解析任务
- **URL**: `POST /api/parse/create`
- **认证**: 需要JWT Token
- **参数**: 
```json
{
  "video_url": "https://example.com/video.mp4"
}
```
- **响应**: 
```json
{
  "code": 201,
  "message": "解析任务已创建",
  "data": {"record_id": 1}
}
```

### 2. 上传视频并解析
- **URL**: `POST /api/parse/upload`
- **认证**: 需要JWT Token
- **参数**: `file` (视频文件)
- **响应**: 
```json
{
  "code": 201,
  "message": "视频上传成功，解析任务已创建",
  "data": {"record_id": 1, "file_path": "/path/to/video.mp4"}
}
```

### 3. 获取解析记录列表
- **URL**: `GET /api/parse/list?page=1&size=20`
- **认证**: 需要JWT Token
- **响应**: 
```json
{
  "code": 200,
  "message": "success",
  "data": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### 4. 获取单个解析记录
- **URL**: `GET /api/parse/{record_id}`
- **认证**: 需要JWT Token

## 生成记录接口

### 1. 创建生成任务
- **URL**: `POST /api/generate/create`
- **认证**: 需要JWT Token
- **参数**: 
```json
{
  "parse_id": 1,
  "params_json": "{}"
}
```
- **响应**: 
```json
{
  "code": 201,
  "message": "生成任务已创建",
  "data": {"record_id": 1}
}
```

### 2. 获取生成记录列表
- **URL**: `GET /api/generate/list?page=1&size=20`
- **认证**: 需要JWT Token

## 卡密兑换接口

### 1. 卡密兑换
- **URL**: `POST /api/card-keys/redeem`
- **认证**: 需要JWT Token
- **参数**: 
```json
{
  "key_code": "ABCDEF1234567890"
}
```
- **响应**: 
```json
{
  "code": 200,
  "message": "兑换成功",
  "data": {"plan_name": "月度会员"}
}
```

## 权限控制

### 每日次数限制
- **免费用户**: 3次解析/天，1次生成/天
- **基础会员**: 10次解析/天，5次生成/天
- **高级会员**: 50次解析/天，20次生成/天

### 错误响应
- **403**: 次数不足
```json
{
  "code": 403,
  "message": "今日解析次数已达上限(3次)，请明天再来或升级会员",
  "data": null
}
```

## 短信服务

### 阿里云短信集成
- 配置环境变量：
  - `ALIBABA_CLOUD_ACCESS_KEY_ID`
  - `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
  - `ALIBABA_CLOUD_SMS_TEMPLATE_ID`
  - `ALIBABA_CLOUD_SIGN_NAME`

### 降级策略
- 开发环境或未配置时返回测试验证码
- 测试验证码: 1234
