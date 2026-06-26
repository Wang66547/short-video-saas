import api from "./index"

// ========== 解析相关 ==========

/** 创建解析任务（URL方式） */
export function createParse(data) {
  return api.post("/parse/create", data)
}

/** 上传视频并解析 */
export function uploadParse(formData) {
  return api.post("/parse/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })
}

/** 批量解析 */
export function batchCreateParse(data) {
  return api.post("/parse/batch-create", data)
}

/** 查询批量任务状态 */
export function getBatchParseStatus(taskId) {
  return api.get(`/parse/batch-status/${taskId}`)
}

/** 解析记录列表 */
export function listParseRecords(page = 1, size = 20) {
  return api.get("/parse/list", { params: { page, size } })
}

/** 解析记录详情 */
export function getParseDetail(recordId) {
  return api.get(`/parse/${recordId}`)
}

// ========== 生成相关 ==========

/** 创建生成任务 */
export function createGenerate(data) {
  return api.post("/generate/create", data)
}

/** 批量生成 */
export function batchCreateGenerate(data) {
  return api.post("/generate/batch-create", data)
}

/** 编辑生成参数 */
export function editGenerate(recordId, data) {
  return api.post(`/generate/edit/${recordId}`, data)
}

/** 生成记录列表 */
export function listGenerateRecords(page = 1, size = 20) {
  return api.get("/generate/list", { params: { page, size } })
}

/** 生成记录详情 */
export function getGenerateDetail(recordId) {
  return api.get(`/generate/${recordId}`)
}

/** 获取解析详情（用于复刻编辑） */
export function getParseForEdit(parseId) {
  return api.get(`/generate/parse/${parseId}`)
}

// ========== 文案改写 ==========

/** AI 文案改写 */
export function rewriteScript(data) {
  return api.post("/generate/rewrite-script", data)
}

/** 获取改写模式 */
export function getRewriteModes() {
  return api.get("/generate/rewrite-modes")
}

/** 平台文案优化 */
export function optimizeForPlatform(data) {
  return api.post("/generate/optimize", data)
}

// ========== 配音服务 ==========

/** TTS 语音合成 */
export function synthesizeVoice(data) {
  return api.post("/generate/synthesize-voice", data)
}

/** 获取音色列表 */
export function getVoices(provider = "ali") {
  return api.get("/generate/voices", { params: { provider } })
}

// ========== 视频管理 ==========

/** 删除解析记录 */
export function deleteParse(recordId) {
  return api.delete(`/parse/${recordId}`)
}

/** 删除生成记录 */
export function deleteGenerate(recordId) {
  return api.delete(`/generate/${recordId}`)
}