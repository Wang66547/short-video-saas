<template>
  <div class="login-wrapper">
    <div class="login-bg">
      <div class="bg-shape s1"></div>
      <div class="bg-shape s2"></div>
      <div class="bg-shape s3"></div>
    </div>
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <svg viewBox="0 0 48 48" width="48" height="48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#lLogo)"/>
            <defs><linearGradient id="lLogo" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
            <path d="M16 16l18 8-18 8V16z" fill="#fff"/>
          </svg>
        </div>
        <h1 class="login-title">管理后台</h1>
        <p class="login-desc">爆款短视频复刻 SaaS 平台</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入管理员账号" prefix-icon="User" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <p class="hint">首次部署请使用数据库初始化脚本创建管理员账号</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { adminLogin } from "@/api/admin"
import { useAdminStore } from "@/stores/admin"

const router = useRouter()
const adminStore = useAdminStore()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: "", password: "" })
const rules = {
  username: [{ required: true, message: "请输入管理员账号", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
}

async function handleLogin(){
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await adminLogin(form)
    if (res.code === 200) {
      const token = res.data?.token
      if (token) { adminStore.setToken(token); ElMessage.success("登录成功"); router.push("/admin/dashboard") }
      else { ElMessage.error("未获取到令牌") }
    }
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || "登录失败"
    ElMessage.error(msg)
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #1e40af 70%, #3b82f6 100%);
  background-size: 200% 200%;
  animation: gradientShift 10s ease infinite;
  position: relative;
  overflow: hidden;
  padding: 20px;
}
.login-bg { position: absolute; inset: 0; }
.bg-shape { position: absolute; border-radius: 50%; background: rgba(59,130,246,0.08); }
.s1 { width: 500px; height: 500px; top: -150px; right: -100px; animation: float 8s ease-in-out infinite; }
.s2 { width: 350px; height: 350px; bottom: -100px; left: -80px; animation: float 10s ease-in-out infinite reverse; }
.s3 { width: 200px; height: 200px; top: 40%; left: 15%; background: rgba(139,92,246,0.06); animation: float 7s ease-in-out infinite; animation-delay: 3s; }
.login-card {
  position: relative; z-index: 1; width: 100%; max-width: 420px;
  background: rgba(255,255,255,0.97);
  border-radius: 20px;
  padding: 48px 40px 36px;
  box-shadow: 0 25px 60px rgba(0,0,0,0.3);
  backdrop-filter: blur(10px);
}
.login-header { text-align: center; margin-bottom: 36px; }
.login-logo { margin-bottom: 16px; }
.login-title { font-size: 1.6rem; font-weight: 800; color: var(--admin-primary); margin-bottom: 4px; }
.login-desc { font-size: 0.85rem; color: var(--admin-text-light); }
.login-btn {
  width: 100%; height: 46px; font-size: 1rem; font-weight: 600; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(59,130,246,0.3) !important;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(59,130,246,0.4) !important; }
.login-footer { text-align: center; margin-top: 24px; }
.hint { font-size: 0.75rem; color: var(--admin-text-light); }
@media(max-width:480px){ .login-card{padding:36px 24px 28px} .login-title{font-size:1.3rem} }
</style>
