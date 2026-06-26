<template>
  <div class="register-container">
    <div class="register-bg">
      <div class="reg-orb o1"></div>
      <div class="reg-orb o2"></div>
    </div>
    <el-card class="register-card" shadow="never">
      <template #header>
        <div class="card-header">
          <svg viewBox="0 0 40 40" width="36" height="36" fill="none">
            <rect width="40" height="40" rx="10" fill="url(#rLogo)"/>
            <defs><linearGradient id="rLogo" x1="0" y1="0" x2="40" y2="40"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
            <path d="M14 12l14 8-14 8V12z" fill="#fff"/>
          </svg>
          <div>
            <h2 class="register-title">创建账号</h2>
            <p class="register-subtitle">开启你的爆款创作之旅</p>
          </div>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3-50个字符" prefix-icon="User" size="large" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="选填，用于找回密码" prefix-icon="Phone" size="large" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少6位" prefix-icon="Lock" show-password size="large" />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="再次输入密码" prefix-icon="Lock" show-password size="large" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :loading="loading" class="register-btn" size="large" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
        
        <div class="register-footer">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { register } from "@/api/auth"

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: "", phone: "", password: "", confirm_password: "" })

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }, { min: 3, max: 50, message: "3-50个字符", trigger: "blur" }],
  phone: [{ pattern: /^1[3-9]\\d{9}$/, message: "手机号格式不正确", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }, { min: 6, message: "密码至少6位", trigger: "blur" }],
  confirm_password: [{ required: true, message: "请再次输入密码", trigger: "blur" }],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await register(form)
    if (res.code === 201) { ElMessage.success("注册成功，请登录"); router.push("/login") }
  } catch (error) { ElMessage.error(error.message || "注册失败") }
  finally { loading.value = false }
}
</script>

<style scoped>
.register-container {
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
.register-bg { position: absolute; inset: 0; }
.reg-orb {
  position: absolute; border-radius: 50%; filter: blur(60px);
}
.o1 { width: 400px; height: 400px; top: -120px; right: -80px; background: rgba(139, 92, 246, 0.12); animation: float 8s ease-in-out infinite; }
.o2 { width: 300px; height: 300px; bottom: -80px; left: -60px; background: rgba(59, 130, 246, 0.1); animation: float 10s ease-in-out infinite reverse; }
.register-card {
  width: 440px; max-width: 100%;
  border-radius: 20px !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  background: rgba(255, 255, 255, 0.97) !important;
  backdrop-filter: blur(20px);
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3) !important;
}
.card-header { display: flex; align-items: center; gap: 14px; }
.register-title { margin: 0; font-size: 1.5rem; font-weight: 800; color: var(--primary); }
.register-subtitle { margin: 2px 0 0; font-size: 0.85rem; color: var(--text-light); }
.register-btn {
  width: 100%; height: 48px; font-size: 1rem; font-weight: 600;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
}
.register-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(59, 130, 246, 0.4) !important; }
.register-footer { text-align: center; font-size: 0.88rem; color: var(--text-light); padding: 16px 0 4px; }
.register-footer a { color: var(--accent); font-weight: 600; margin-left: 8px; }
.register-footer a:hover { text-decoration: underline; }
</style>
