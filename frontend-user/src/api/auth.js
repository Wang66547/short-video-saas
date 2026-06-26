import api from "./index"

/**
 * 发送短信验证码
 * GET /api/auth/send-code?phone=xxx
 */
export function sendCode(phone) {
  return api.get("/auth/send-code", { params: { phone } })
}

/**
 * 用户登录（密码/验证码/微信）
 * POST /api/auth/login
 */
export function login(data) {
  return api.post("/auth/login", data)
}

/**
 * 用户注册
 * POST /api/auth/register
 */
export function register(data) {
  return api.post("/auth/register", data)
}

/**
 * 刷新令牌
 * POST /api/auth/refresh
 */
export function refreshToken(refreshTokenVal) {
  return api.post("/auth/refresh", null, { params: { refresh_token: refreshTokenVal } })
}

/**
 * 获取当前用户信息
 * GET /api/auth/me
 */
export function getMe() {
  return api.get("/auth/me")
}

/**
 * 退出登录
 * POST /api/auth/logout
 */
export function logout() {
  return api.post("/auth/logout")
}

/**
 * 更新个人资料
 * PUT /api/auth/profile
 */
export function updateProfile(data) {
  return api.put("/auth/profile", data)
}

/**
 * 获取用户的解析记录
 * GET /api/auth/parse-records
 */
export function listParseRecords(page = 1, size = 20) {
  return api.get("/auth/parse-records", { params: { page, size } })
}

/**
 * 获取用户的生成记录
 * GET /api/auth/generate-records
 */
export function listGenerateRecords(page = 1, size = 20) {
  return api.get("/auth/generate-records", { params: { page, size } })
}