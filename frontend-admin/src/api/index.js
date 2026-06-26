import axios from "axios"
import { ElMessage } from "element-plus"
import router from "@/router"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 30000,
})

// 请求拦截：自动附加 admin token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：统一错误处理
api.interceptors.response.use(
  (r) => r.data,
  (e) => {
    const status = e.response?.status
    const data = e.response?.data

    if (status === 401) {
      localStorage.removeItem("admin_token")
      ElMessage.error("登录已过期，请重新登录")
      router.push("/login")
    } else if (status === 403) {
      ElMessage.error("权限不足，无法执行该操作")
    } else if (status >= 500) {
      ElMessage.error("服务器异常，请稍后再试")
    } else {
      const msg = data?.message || data?.detail || e.message || "请求失败"
      ElMessage.error(msg)
    }

    return Promise.reject(data || e)
  }
)

export default api