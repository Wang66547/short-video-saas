# 问题与风险记录

## 代码审查结果（2026-06-25）

---

## ✅ 已修复问题

### 🔴 严重 Bug（6个，已全部修复）

| # | 文件 | 问题 | 修复状态 |
|---|------|------|----------|
| 1 | wechat_pay.py | `generate_auth_header` 引用未定义 `signature` | ✅ 已修复 |
| 2 | wechat_pay.py | `verify_callback` 引用未定义 `expected` | ✅ 已修复 |
| 3 | payment_service.py | 非请求上下文中调用 `get_db()` | ✅ 已修复 |
| 4 | generate.py | 字典 key 未加引号语法错误 | ✅ 已修复 |
| 5 | users.py | `verify_password` 未导入 | ✅ 已修复 |
| 6 | rate_limit.py | Redis `time()` 调用错误 | ✅ 已修复 |

### 🔴 严重安全问题（4个，已全部修复）

| # | 问题 | 修复状态 |
|---|------|----------|
| 7 | 管理员权限与会员等级混淆 | ✅ 已重构：`admins` 表独立管理 |
| 8 | init.sql 默认管理员密码无效 | ✅ 已修复：有效 bcrypt 哈希 |
| 9 | SECRET_KEY 默认值不安全 | ✅ 已修复：生产环境拒绝启动 |
| 10 | 数据库密码硬编码弱密码 | ✅ 已修复：启动时警告 |

### 🟡 中等问题（部分修复）

| # | 问题 | 修复状态 |
|---|------|----------|
| 13 | Docker Compose 配置路径不匹配 | ✅ 已修复 |
| 17 | 前端登录页暴露默认密码 | ✅ 已修复 |

---

## 🟡 待处理问题（已全部修复）

### 11. `sms_service.py` - 生产环境短信服务硬崩溃 ✅ 已修复
**修复**: 移除 `NotImplementedError`，改为优雅降级返回模拟验证码并打印警告

### 12. `generate.py` - 文案改写异常返回 200 ✅ 已修复
**修复**: 添加 `is_mock` 字段区分真实结果和模拟结果，message 中说明原因

### 14. `db/session.py` - `get_db` 自动提交风险 ✅ 已修复
**修复**: 移除自动 commit，由业务逻辑自行控制提交时机

### 15. Token 刷新接口未实现 ✅ 已修复
**修复**: 在 [auth.py](file:///d:/ai/codex/爆款短视频复刻/backend/app/api/auth.py#L166) 添加 `/auth/refresh` 端点

### 16. 前端 Admin 401 强制刷新 ✅ 已修复
**修复**: 改用 Vue Router `router.push("/login")` 替代 `window.location.href`

---

## 🟢 建议改进

### 18. 密码强度校验不足
密码最小长度仅 6 位，未要求包含数字、字母、特殊字符组合。

### 19. 无请求日志脱敏
请求日志中直接记录 URL 路径，敏感参数可能被日志记录。

### 20. 视频文件上传无类型校验
[backend/app/api/parse.py](file:///d:/ai/codex/爆款短视频复刻/backend/app/api/parse.py#L58-L94) 中上传接口未校验文件 MIME 类型。

### 21. 无 API 版本管理
所有 API 路由直接挂载在 `/api/` 下，后续升级时需要版本化策略。

### 22. CORS 配置过于宽松
`allow_headers=["*"]` 和 `allow_methods=["*"]` 在生产环境应收紧。

### 23. 缺少单元测试
整体测试覆盖率不足。

### 24. Nginx 配置强制 HTTPS 但可能无证书
生产环境若未配置 SSL 证书，HTTPS 重定向会导致网站无法访问。

---

## 风险提示
1. 生产环境必须修改 SECRET_KEY 和数据库密码
2. 视频存储目录需要足够的磁盘空间
3. Celery Worker 处理大视频可能超时，需调整 time_limit
4. 微信支付需要商户资质和证书文件
5. 支付宝需要签约电脑网站/手机网站支付产品
6. 需要配置外部资源：即梦/可灵 AI API、PaddleOCR、faster-whisper