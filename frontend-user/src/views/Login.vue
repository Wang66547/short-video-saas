<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-orb orb1"></div>
      <div class="bg-orb orb2"></div>
      <div class="bg-orb orb3"></div>
    </div>
    <div class="auth-container">
      <el-card class="auth-card" shadow="never">
        <div class="auth-header">
          <div class="auth-logo-wrap">
            <svg viewBox="0 0 40 40" width="44" height="44" fill="none">
              <rect width="40" height="40" rx="12" fill="url(#aLogo)"/>
              <defs><linearGradient id="aLogo" x1="0" y1="0" x2="40" y2="40"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
              <path d="M14 12l14 8-14 8V12z" fill="#fff"/>
            </svg>
          </div>
          <h1 class="auth-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</h1>
          <p class="auth-subtitle">{{ isRegister ? '开启你的爆款创作之旅' : '登录你的创作账号' }}</p>
        </div>

        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane v-if="!isRegister" label="密码登录" name="password">
            <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-position="top">
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="pwdForm.phone" placeholder="请输入手机号" size="large" />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input v-model="pwdForm.password" type="password" placeholder="请输入密码" size="large" show-password @keyup.enter="handlePwdLogin" />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" class="auth-submit-btn" @click="handlePwdLogin">登 录</el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane :label="isRegister ? '注册' : '验证码登录'" name="sms">
            <el-form ref="smsFormRef" :model="smsForm" :rules="smsRules" label-position="top">
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="smsForm.phone" placeholder="请输入手机号" size="large" />
              </el-form-item>
              <el-form-item label="验证码" prop="captcha">
                <el-input v-model="smsForm.captcha" placeholder="请输入验证码" size="large">
                  <template #append>
                    <el-button :disabled="countdown > 0" @click="handleSendCode" class="code-btn">
                      {{ countdown > 0 ? countdown + 's' : '获取验证码' }}
                    </el-button>
                  </template>
                </el-input>
              </el-form-item>
              <el-form-item v-if="isRegister" label="昵称" prop="nickname">
                <el-input v-model="smsForm.nickname" placeholder="请输入昵称" size="large" />
              </el-form-item>
              <el-form-item v-if="isRegister" label="密码" prop="password">
                <el-input v-model="smsForm.password" type="password" placeholder="设置密码（至少6位）" size="large" show-password />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" class="auth-submit-btn" @click="isRegister ? handleRegister() : handleSmsLogin()">{{ isRegister ? '注 册' : '登 录' }}</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="auth-divider">
          <span>其他登录方式</span>
        </div>
        <div class="third-party">
          <el-button class="wx-btn" @click="handleWechatLogin" :loading="loading">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#07c160">
              <path d="M8.5 11a1 1 0 100-2 1 1 0 000 2zm-3 0a1 1 0 100-2 1 1 0 000 2zm12.5 5a1 1 0 100-2 1 1 0 000 2zm-3 0a1 1 0 100-2 1 1 0 000 2z"/>
            </svg>
            微信登录
          </el-button>
        </div>

        <div class="auth-switch">
          <template v-if="!isRegister">
            还没有账号？
            <span class="switch-link" @click="toggleMode">立即注册</span>
          </template>
          <template v-else>
            已有账号？
            <span class="switch-link" @click="toggleMode">立即登录</span>
          </template>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from "vue"
import { useRouter, useRoute } from "vue-router"
import { ElMessage } from "element-plus"
import { useUserStore } from "@/stores/user"
import { login as loginApi, register as registerApi, sendCode } from "@/api/auth"

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const activeTab = ref("password")
const countdown = ref(0)
const isRegister = ref(false)
let timer = null

const pwdForm = reactive({ phone: "", password: "" })
const pwdFormRef = ref(null)
const smsForm = reactive({ phone: "", captcha: "", nickname: "", password: "" })
const smsFormRef = ref(null)

const pwdRules = {
  phone: [{ required: true, message: "请输入手机号", trigger: "blur" }, { pattern: /^1[3-9]\\d{9}$/, message: "手机号格式不正确", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }, { min: 6, message: "密码至少6位", trigger: "blur" }],
}
const smsRules = {
  phone: [{ required: true, message: "请输入手机号", trigger: "blur" }, { pattern: /^1[3-9]\\d{9}$/, message: "手机号格式不正确", trigger: "blur" }],
  captcha: [{ required: true, message: "请输入验证码", trigger: "blur" }, { len: 6, message: "验证码为6位数字", trigger: "blur" }],
}

function toggleMode() {
  isRegister.value = !isRegister.value
  activeTab.value = isRegister.value ? "sms" : "password"
}

onMounted(() => {
  if (route.name === "Register") { isRegister.value = true; activeTab.value = "sms" }
})
watch(() => route.name, (newName) => {
  if (newName === "Register") { isRegister.value = true; activeTab.value = "sms" }
  else { isRegister.value = false; activeTab.value = "password" }
})

async function handleSendCode() {
  if (!smsForm.phone || !/^1[3-9]\\d{9}$/.test(smsForm.phone)) { ElMessage.warning("请输入正确的手机号"); return }
  try {
    const res = await sendCode(smsForm.phone)
    if (res.code === 200 || res.code === 201) {
      ElMessage.success(import.meta.env.DEV ? "验证码已发送（测试模式验证码：123456）" : "验证码已发送")
      countdown.value = 60
      timer = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(timer) }, 1000)
    }
  } catch (e) { ElMessage.error("发送失败：" + (e.message || e.detail || "")) }
}

async function handlePwdLogin() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await loginApi({ phone: pwdForm.phone, password: pwdForm.password })
    const data = res.data || res
    const token = data.access_token || data.token
    if (token) {
      userStore.token.value = token
      userStore.refreshToken.value = data.refresh_token || data.refreshToken || ""
      localStorage.setItem("token", token)
      localStorage.setItem("refresh_token", data.refresh_token || data.refreshToken || "")
      await userStore.fetchUserInfo()
      ElMessage.success("登录成功")
      router.push(route.query.redirect || "/dashboard")
    }
  } catch (e) { ElMessage.error(e.message || e.detail || "登录失败") }
  finally { loading.value = false }
}

async function handleSmsLogin() {
  const valid = await smsFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await loginApi({ phone: smsForm.phone, captcha: smsForm.captcha })
    const data = res.data || res
    const token = data.access_token || data.token
    if (token) {
      userStore.token.value = token
      userStore.refreshToken.value = data.refresh_token || data.refreshToken || ""
      localStorage.setItem("token", token)
      localStorage.setItem("refresh_token", data.refresh_token || data.refreshToken || "")
      await userStore.fetchUserInfo()
      ElMessage.success("登录成功")
      router.push(route.query.redirect || "/dashboard")
    }
  } catch (e) { ElMessage.error(e.message || e.detail || "登录失败") }
  finally { loading.value = false }
}

async function handleRegister() {
  const valid = await smsFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await registerApi({ phone: smsForm.phone, nickname: smsForm.nickname || smsForm.phone.slice(-6), password: smsForm.password || smsForm.captcha })
    if (res.code === 201 || res.code === 200) { ElMessage.success("注册成功，请登录"); isRegister.value = false; activeTab.value = "password" }
  } catch (e) { ElMessage.error(e.message || e.detail || "注册失败") }
  finally { loading.value = false }
}

function handleWechatLogin() { ElMessage.info("微信登录功能待接入") }
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.auth-page {
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
.auth-bg { position: absolute; inset: 0; }
.bg-orb {
  position: absolute; border-radius: 50%; filter: blur(60px);
}
.orb1 { width: 500px; height: 500px; top: -150px; right: -100px; background: rgba(59, 130, 246, 0.12); animation: float 8s ease-in-out infinite; }
.orb2 { width: 350px; height: 350px; bottom: -100px; left: -80px; background: rgba(139, 92, 246, 0.1); animation: float 10s ease-in-out infinite reverse; }
.orb3 { width: 200px; height: 200px; top: 50%; left: 60%; background: rgba(59, 130, 246, 0.08); animation: float 7s ease-in-out infinite; animation-delay: 3s; }
.auth-container { position: relative; z-index: 1; width: 100%; max-width: 440px; }
.auth-card {
  border-radius: 20px !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  background: rgba(30, 41, 59, 0.95) !important;
  backdrop-filter: blur(20px);
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5) !important;
  padding: 8px;
}
.auth-header { text-align: center; margin-bottom: 28px; padding: 12px 0 4px; }
.auth-logo-wrap { margin-bottom: 14px; }
.auth-title { font-size: 1.6rem; font-weight: 800; color: var(--primary); margin-bottom: 6px; }
.auth-subtitle { color: var(--text-light); font-size: 0.9rem; }
.auth-tabs { margin-top: 4px; }
.auth-tabs :deep(.el-tabs__header) { margin-bottom: 20px; border-bottom: 1px solid var(--border-light); }
.auth-tabs :deep(.el-tabs__item) { font-weight: 600; padding: 0 20px; height: 44px; line-height: 44px; }
.auth-tabs :deep(.el-tabs__active-bar) { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
.auth-submit-btn {
  width: 100%; height: 48px; font-size: 1rem; font-weight: 600;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
  margin-top: 8px;
}
.auth-submit-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(59, 130, 246, 0.4) !important; }
.code-btn { background: linear-gradient(135deg, #3b82f6, #2563eb) !important; color: #fff !important; border: none !important; }
.auth-divider {
  display: flex; align-items: center; gap: 12px;
  margin: 24px 0 16px; color: var(--text-light); font-size: 0.82rem;
}
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.third-party { display: flex; justify-content: center; }
.wx-btn {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg-light); border: 1px solid var(--border);
  color: #07c160; font-weight: 500;
  border-radius: var(--radius);
  transition: all 0.2s;
}
.wx-btn:hover { border-color: #07c160; box-shadow: 0 2px 8px rgba(7, 193, 96, 0.2); }
.auth-switch { text-align: center; margin-top: 20px; font-size: 0.88rem; color: var(--text-light); }
.switch-link { color: var(--accent); font-weight: 600; margin-left: 4px; cursor: pointer; }
.switch-link:hover { text-decoration: underline; }
</style>
