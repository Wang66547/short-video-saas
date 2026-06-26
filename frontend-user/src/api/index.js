import axios from "axios"
import { useUserStore } from "@/stores/user"
import router from "@/router"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
})

// 请求拦截器：自动附加 Token
api.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const userStore = useUserStore()
    if (error.response?.status === 401) {
      userStore.logout()
      router.push("/login")
    }
    return Promise.reject(error.response?.data || error)
  }
)

export default api
