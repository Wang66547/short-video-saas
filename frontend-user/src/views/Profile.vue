<template>
  <div class="profile-page">
    <Header />
    <div class="page-container">
      <h2 class="page-title">个人中心</h2>
      <el-row :gutter="24">
        <el-col :xs="24" :lg="8">
          <el-card class="info-card" shadow="hover">
            <div class="avatar-section">
              <el-avatar :size="88" :src="userStore.userInfo?.avatar||''" class="avatar-glow">
                {{ userStore.userInfo?.nickname?.charAt(0)||userStore.userInfo?.phone?.slice(-2)||'U' }}
              </el-avatar>
              <h3 class="nickname">{{ userStore.userInfo?.nickname||'用户' }}</h3>
              <p class="phone">{{ userStore.userInfo?.phone||'未绑定手机号' }}</p>
              <el-tag :type="memberTagType" size="default" effect="dark" style="margin-top:8px;">{{ memberLabel }}</el-tag>
            </div>
            <el-divider />
            <div class="quick-stats">
              <div class="qs-item" v-for="s in qsItems" :key="s.label">
                <span class="qs-val">{{ s.value }}</span>
                <span class="qs-lbl">{{ s.label }}</span>
              </div>
            </div>
            <router-link to="/membership">
              <el-button type="primary" round class="upgrade-btn">升级会员</el-button>
            </router-link>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="16">
          <el-card shadow="never">
            <el-tabs v-model="activeTab" class="profile-tabs">
              <el-tab-pane label="基本信息" name="info">
                <el-form :model="profileForm" label-width="100px" style="max-width:400px;" label-position="top">
                  <el-form-item label="昵称"><el-input v-model="profileForm.nickname" size="large" /></el-form-item>
                  <el-form-item label="头像URL"><el-input v-model="profileForm.avatar" placeholder="输入头像链接" size="large" /></el-form-item>
                  <el-form-item><el-button type="primary" :loading="saving" size="large" @click="saveProfile">保存修改</el-button></el-form-item>
                </el-form>
              </el-tab-pane>
              <el-tab-pane label="修改密码" name="password">
                <el-form :model="pwdForm" label-width="100px" style="max-width:400px;" label-position="top">
                  <el-form-item label="原密码"><el-input v-model="pwdForm.old_password" type="password" show-password size="large" /></el-form-item>
                  <el-form-item label="新密码"><el-input v-model="pwdForm.new_password" type="password" show-password size="large" /></el-form-item>
                  <el-form-item label="确认密码"><el-input v-model="pwdForm.confirm_password" type="password" show-password size="large" /></el-form-item>
                  <el-form-item><el-button type="primary" :loading="changingPwd" size="large" @click="handleChangePwd">修改密码</el-button></el-form-item>
                </el-form>
              </el-tab-pane>
              <el-tab-pane label="卡密兑换" name="redeem">
                <div class="redeem-section">
                  <el-input v-model="keyCode" placeholder="请输入卡密" size="large">
                    <template #append><el-button type="success" :loading="redeeming" @click="handleRedeem">兑换</el-button></template>
                  </el-input>
                  <p class="redeem-hint">兑换后自动充值对应会员权益</p>
                </div>
              </el-tab-pane>
              <el-tab-pane label="账号安全" name="security">
                <div class="security-section">
                  <div class="sec-item" v-for="item in secItems" :key="item.label">
                    <span class="sec-label">{{ item.label }}</span>
                    <span class="sec-value">{{ item.value }}</span>
                    <el-button v-if="item.action" size="small" round @click="item.action">{{ item.actionText }}</el-button>
                  </div>
                  <el-divider />
                  <el-button type="danger" round @click="handleLogout">退出登录</el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"
import { useUserStore } from "@/stores/user"
import { updateProfile } from "@/api/auth"
import { redeem } from "@/api/membership"
import { changePassword } from "@/api/user"

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref("info")
const saving = ref(false)
const changingPwd = ref(false)
const redeeming = ref(false)
const keyCode = ref("")
const profileForm = reactive({ nickname: "", avatar: "" })
const pwdForm = reactive({ old_password: "", new_password: "", confirm_password: "" })

const memberTagType = computed(() => { const lvl = userStore.userInfo?.membership_level; return lvl==="premium"?"danger":lvl==="basic"?"warning":"info" })
const memberLabel = computed(() => { const lvl = userStore.userInfo?.membership_level; return {free:"免费版",basic:"基础会员",premium:"高级会员"}[lvl]||"免费版" })

const qsItems = computed(() => [
  { label: "剩余积分", value: userStore.userInfo?.remaining_credits ?? 0 },
  { label: "会员到期", value: (() => { const exp = userStore.userInfo?.membership_expire_at; return exp ? exp.substring(0,10) : "永久" })() },
])

const secItems = computed(() => [
  { label: "手机号", value: userStore.userInfo?.phone || '未绑定' },
  { label: "微信绑定", value: userStore.userInfo?.wechat_openid ? '已绑定' : '未绑定', action: () => ElMessage.info("微信绑定功能待接入"), actionText: "绑定微信" },
  { label: "注册时间", value: userStore.userInfo?.created_at || '-' },
  { label: "最后登录", value: userStore.userInfo?.last_login_at || '未知' },
])

onMounted(() => { if(userStore.userInfo){ profileForm.nickname=userStore.userInfo.nickname||""; profileForm.avatar=userStore.userInfo.avatar||"" } })

async function saveProfile(){ saving.value=true; try{ await updateProfile(profileForm); ElMessage.success("保存成功"); await userStore.fetchUserInfo() } catch(e){ ElMessage.error("保存失败") } finally{ saving.value=false } }

async function handleChangePwd(){
  if(!pwdForm.old_password){ElMessage.warning("请输入原密码");return}
  if(!pwdForm.new_password||pwdForm.new_password.length<6){ElMessage.warning("新密码至少6位");return}
  if(pwdForm.new_password!==pwdForm.confirm_password){ElMessage.warning("两次密码不一致");return}
  changingPwd.value = true
  try {
    await changePassword({ old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    ElMessage.success("密码修改成功")
    pwdForm.old_password = ""
    pwdForm.new_password = ""
    pwdForm.confirm_password = ""
  } catch(e) { ElMessage.error(e.message || e.detail || "修改失败") }
  finally { changingPwd.value = false }
}

async function handleRedeem(){
  if(!keyCode.value.trim()){ElMessage.warning("请输入卡密");return}
  redeeming.value=true; try{ const res=await redeem(keyCode.value.trim()); if(res.code===200){ElMessage.success("兑换成功！");keyCode.value=""} } catch(e){ ElMessage.error(e.message||e.detail||"兑换失败") } finally{ redeeming.value=false }
}
function handleLogout(){ ElMessageBox.confirm("确定要退出登录吗？","提示",{type:"warning"}).then(()=>{ userStore.logout(); ElMessage.success("已退出登录"); router.push("/login") }).catch(()=>{}) }
</script>

<style scoped>
.profile-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 1100px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-title { font-size: 1.8rem; font-weight: 800; color: var(--primary); margin-bottom: 36px; }
.info-card { margin-bottom: 24px; border-radius: var(--radius-xl); }
.avatar-section { text-align: center; padding: 28px 0 20px; }
.avatar-glow { box-shadow: 0 0 0 4px var(--accent-glow), 0 4px 16px rgba(59,130,246,0.15); }
.nickname { font-size: 1.3rem; font-weight: 700; margin: 12px 0 4px; }
.phone { color: var(--text-light); font-size: 0.85rem; margin: 0 0 10px; }
.quick-stats { display: flex; justify-content: space-around; padding: 20px 0; }
.qs-item { text-align: center; }
.qs-val { display: block; font-size: 1.4rem; font-weight: 700; color: var(--primary); }
.qs-lbl { font-size: 0.8rem; color: var(--text-light); }
.upgrade-btn { width: 100%; font-weight: 600; }
.profile-tabs :deep(.el-tabs__header) { margin-bottom: 28px; }
.profile-tabs :deep(.el-tabs__active-bar) { background: linear-gradient(90deg, #3b82f6, #8b5cf6); height: 3px; }
.profile-tabs :deep(.el-tabs__item) { font-weight: 600; padding: 0 20px; height: 44px; line-height: 44px; }
.redeem-section { padding: 20px 0; }
.redeem-hint { font-size: 0.8rem; color: var(--text-light); margin-top: 8px; }
.security-section { padding: 8px 0; }
.sec-item { display: flex; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px solid var(--border-light); }
.sec-label { width: 80px; color: var(--text-light); font-size: 0.9rem; flex-shrink: 0; }
.sec-value { flex: 1; font-size: 0.9rem; }
</style>
