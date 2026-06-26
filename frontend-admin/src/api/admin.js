import api from "./index"

// ==================== 认证 ====================
export function adminLogin(data) {
  return api.post("/admin/login", data)
}

// ==================== 数据统计 ====================
export function getStats() {
  return api.get("/admin/stats")
}

export function getStatsTrend(days = 7) {
  return api.get("/admin/stats/trend", { params: { days } })
}

// ==================== 用户管理 ====================
export function listUsers(page = 1, size = 20, params = {}) {
  return api.get("/admin/users", { params: { page, size, ...params } })
}

export function getUserDetail(userId) {
  return api.get(`/admin/users/${userId}`)
}

export function updateUser(userId, data) {
  return api.put(`/admin/users/${userId}`, data)
}

export function toggleUser(userId) {
  return api.put(`/admin/users/${userId}/toggle`)
}

// ==================== 订单管理 ====================
export function listOrders(page = 1, size = 20, params = {}) {
  return api.get("/admin/orders", { params: { page, size, ...params } })
}

export function getOrderDetail(orderNo) {
  return api.get(`/admin/orders/${orderNo}`)
}

export function manualPayOrder(orderNo) {
  return api.post(`/admin/orders/${orderNo}/manual-pay`)
}

// ==================== 套餐管理 ====================
export function listPlans(page = 1, size = 20) {
  return api.get("/admin/plans", { params: { page, size } })
}

export function createPlan(data) {
  return api.post("/admin/plans", data)
}

export function updatePlan(planId, data) {
  return api.put(`/admin/plans/${planId}`, data)
}

export function deletePlan(planId) {
  return api.delete(`/admin/plans/${planId}`)
}

export function togglePlan(planId) {
  return api.put(`/admin/plans/${planId}/toggle`)
}

// ==================== 系统配置 ====================
export function listConfigs(category = null) {
  const params = category ? { category } : {}
  return api.get("/admin/configs", { params })
}

export function getConfig(key) {
  return api.get(`/admin/configs/${key}`)
}

export function updateConfig(data) {
  return api.put("/admin/configs", data)
}

export function initDefaultConfigs() {
  return api.post("/admin/configs/init-default")
}

// ==================== 卡密管理 ====================
export function listCardKeys(page = 1, size = 20, isUsed = null) {
  const params = { page, size }
  if (isUsed !== null) params.is_used = isUsed
  return api.get("/admin/card-keys", { params })
}

export function batchGenerateCardKeys(data) {
  return api.post("/admin/card-keys/batch-generate", data)
}

export function deleteCardKey(cardKeyId) {
  return api.delete(`/admin/card-keys/${cardKeyId}`)
}

// ==================== 视频任务管理 ====================
export function listParseRecords(page = 1, size = 20, status = null) {
  const params = { page, size }
  if (status) params.status = status
  return api.get("/admin/parse-records", { params })
}

export function listGenerateRecords(page = 1, size = 20, status = null) {
  const params = { page, size }
  if (status) params.status = status
  return api.get("/admin/generate-records", { params })
}

// ==================== 批量处理管理 ====================
export function getBatchParseStatus(taskId) {
  return api.get(`/admin/batch-parse-status/${taskId}`)
}

export function getBatchGenStatus(taskId) {
  return api.get(`/admin/batch-gen-status/${taskId}`)
}

// ==================== 文案改写 ====================
export function rewriteScript(data) {
  return api.post("/generate/rewrite-script", data)
}

export function getRewriteModes() {
  return api.get("/generate/rewrite-modes")
}

// ==================== 配音服务 ====================
export function synthesizeVoice(data) {
  return api.post("/generate/synthesize-voice", data)
}

export function getVoices(provider = "ali") {
  return api.get("/generate/voices", { params: { provider } })
}

// ==================== 平台优化 ====================
export function optimizeForPlatform(data) {
  return api.post("/generate/optimize", data)
}