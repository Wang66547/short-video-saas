<template>
  <div class="membership-page">
    <Header />
    <div class="page-container">
      <div class="page-hero">
        <h2 class="page-title">会员中心</h2>
        <p class="page-desc">解锁更多权益，畅享 AI 创作</p>
      </div>

      <!-- Status Card -->
      <el-card v-if="userStore.isLoggedIn" class="status-card" shadow="hover">
        <template #header>
          <div class="status-header">
            <span>当前会员状态</span>
            <el-tag :type="memberStatus.type" size="large" effect="dark">{{ memberStatus.label }}</el-tag>
          </div>
        </template>
        <el-row :gutter="24">
          <el-col :xs="12" :sm="6" v-for="s in statusItems" :key="s.label">
            <div class="status-item">
              <div class="status-val">{{ s.value }}</div>
              <div class="status-lbl">{{ s.label }}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- Plans -->
      <h3 class="section-heading">选择套餐</h3>
      <el-row :gutter="24" class="plans-row">
        <el-col :xs="24" :sm="12" :lg="6" v-for="plan in plans" :key="plan.id">
          <div class="plan-card" :class="{ popular: plan.plan_type === 'premium' }">
            <div class="plan-badge" v-if="plan.plan_type === 'premium'">最受欢迎</div>
            <div class="plan-icon">
              <el-icon :size="32" v-if="plan.plan_type==='free'"><Coin /></el-icon>
              <el-icon :size="32" v-else-if="plan.plan_type==='basic'"><Medal /></el-icon>
              <el-icon :size="32" v-else><Trophy /></el-icon>
            </div>
            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-type">{{ planTypeDesc(plan.plan_type) }}</div>
            <div class="plan-price">
              <span class="price-currency">￥</span>
              <span class="price-current">{{ plan.price }}</span>
              <span class="price-original" v-if="plan.original_price && plan.original_price > plan.price">￥{{ plan.original_price }}</span>
            </div>
            <ul class="plan-benefits">
              <li v-for="(b,bi) in plan.features" :key="bi">
                <el-icon color="#10b981"><Check /></el-icon> {{ b }}
              </li>
            </ul>
            <el-button :type="plan.plan_type==='premium'?'primary':'default'" round class="plan-btn"
              :disabled="plan.price===0" @click="plan.price>0?buyPlan(plan):router.push('/dashboard')">
              {{ plan.price===0?'当前套餐':'立即购买' }}
            </el-button>
          </div>
        </el-col>
      </el-row>

      <!-- Compare -->
      <h3 class="section-heading" style="margin-top:56px;">权益对比</h3>
      <el-card shadow="never">
        <el-table :data="compareData" stripe border size="default" class="compare-table">
          <el-table-column prop="feature" label="权益" width="160" />
          <el-table-column label="免费版" width="120"><template #default="{row}"><el-tag v-if="row.free" type="success" size="small" effect="light">{{ row.free }}</el-tag><el-tag v-else size="small">不支持</el-tag></template></el-table-column>
          <el-table-column label="基础会员" width="120"><template #default="{row}"><el-tag v-if="row.basic" type="primary" size="small" effect="light">{{ row.basic }}</el-tag><el-tag v-else size="small">不支持</el-tag></template></el-table-column>
          <el-table-column label="高级会员" width="120"><template #default="{row}"><el-tag v-if="row.premium" type="warning" size="small" effect="light">{{ row.premium }}</el-tag><el-tag v-else size="small">不支持</el-tag></template></el-table-column>
        </el-table>
      </el-card>

      <!-- Redeem -->
      <el-card style="margin-top:32px;max-width:500px;">
        <template #header><span>卡密兑换</span></template>
        <div class="redeem-area">
          <el-input v-model="keyCode" placeholder="请输入卡密" size="large" class="redeem-input">
            <template #append><el-button type="success" :loading="redeeming" @click="handleRedeem">兑换</el-button></template>
          </el-input>
          <p class="redeem-hint">兑换后自动充值对应会员权益</p>
        </div>
      </el-card>
    </div>

    <!-- Pay Dialog -->
    <el-dialog v-model="payDialogVisible" title="选择支付方式" width="420px" destroy-on-close>
      <div class="pay-modal">
        <div class="pay-plan-info">
          <span class="pay-plan-name">{{ selectedPlan?.name }}</span>
          <span class="pay-plan-price">￥{{ selectedPlan?.price }}</span>
        </div>
        <el-radio-group v-model="payMethod" class="pay-methods">
          <el-radio-button value="wechat"><svg width="16" height="16" viewBox="0 0 24 24" fill="#07c160"><path d="M8.5 11a1 1 0 100-2 1 1 0 000 2z"/></svg> 微信</el-radio-button>
          <el-radio-button value="alipay"><svg width="16" height="16" viewBox="0 0 24 24" fill="#1677ff"><circle cx="12" cy="12" r="6"/></svg> 支付宝</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :loading="paying" class="pay-btn" @click="doPay">确认支付</el-button>
        <p class="pay-tip">支付完成后自动开通会员权益</p>
      </div>
    </el-dialog>

    <Footer />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { Coin, Medal, Trophy, Check } from "@element-plus/icons-vue"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"
import { useUserStore } from "@/stores/user"
import { getPlans, redeem } from "@/api/membership"
import { createOrder, alipayPrepay as alipayPrepayApi } from "@/api/payment"

const router = useRouter()
const userStore = useUserStore()
const plans = ref([])
const payDialogVisible = ref(false)
const selectedPlan = ref(null)
const payMethod = ref("wechat")
const paying = ref(false)
const keyCode = ref("")
const redeeming = ref(false)

const memberStatus = reactive({ level: "免费版", expire: "永久", credits: 0, dailyParse: 3, label: "免费版", type: "info" })

const statusItems = computed(() => [
  { label: "会员等级", value: memberStatus.level },
  { label: "到期时间", value: memberStatus.expire },
  { label: "剩余积分", value: memberStatus.credits },
  { label: "每日解析", value: memberStatus.dailyParse + " 次" },
])

function planTypeDesc(t){return{free:"免费版",basic:"基础会员",premium:"高级会员"}[t]||t}

async function buyPlan(plan){selectedPlan.value=plan; payDialogVisible.value=true}

async function doPay(){
  if(!selectedPlan.value)return; paying.value=true
  try {
    const orderRes = await createOrder({ plan_id: selectedPlan.value.id, payment_method: payMethod.value })
    if(orderRes.code===200){
      const orderNo = orderRes.data?.order_no
      if(payMethod.value==="alipay"){
        const payRes=await alipayPrepayApi(orderNo)
        if(payRes.code===200&&payRes.data?.pay_url){window.open(payRes.data.pay_url,"_blank");payDialogVisible.value=false}
        else{ElMessage.success("支付已准备就绪");payDialogVisible.value=false}
      } else {
        ElMessage.success("支付已准备就绪，请联系商户接入真实支付")
        payDialogVisible.value=false
      }
    }
  } catch(e){ElMessage.error("支付发起失败"+(e.message||""))}
  finally{paying.value=false}
}

async function handleRedeem(){
  if(!keyCode.value.trim()){ElMessage.warning("请输入卡密");return}
  redeeming.value=true
  try{const res=await redeem(keyCode.value.trim())
    if(res.code===200){ElMessage.success("兑换成功！会员权益已到账");keyCode.value="";loadPlans()}
  }catch(e){ElMessage.error(e.message||e.detail||"兑换失败")}
  finally{redeeming.value=false}
}

const compareData = [
  {feature:"每日解析次数",free:"3次",basic:"10次",premium:"50次"},
  {feature:"每日生成次数",free:"1次",basic:"5次",premium:"20次"},
  {feature:"高清导出",free:"",basic:"",premium:"支持"},
  {feature:"OCR 字幕识别",free:"",basic:"基础",premium:"高级"},
  {feature:"Whisper 语音转写",free:"",basic:"",premium:"支持"},
  {feature:"AI 视频生成",free:"",basic:"",premium:"支持"},
  {feature:"专属客服",free:"",basic:"",premium:"支持"},
]

onMounted(()=>{
  loadPlans()
  if(userStore.userInfo){
    const lvl=userStore.userInfo.membership_level||"free"
    memberStatus.level={free:"免费版",basic:"基础会员",premium:"高级会员"}[lvl]||lvl
    memberStatus.credits=userStore.userInfo.remaining_credits??0
    memberStatus.expire=userStore.userInfo.membership_expire_at||"永久"
    memberStatus.dailyParse={free:3,basic:10,premium:50}[lvl]||3
    memberStatus.type=lvl==="premium"?"danger":lvl==="basic"?"warning":"info"
    memberStatus.label=memberStatus.level
  }
})

async function loadPlans(){
  try{const res=await getPlans()
    if(res.code===200){const raw=res.data||[]; plans.value=raw.map(p=>({...p,
      features:[`每日 ${p.daily_parse_count} 次解析`,`每日 ${p.daily_generate_count} 次生成`,p.support_hd_export?"支持高清导出":"标准画质",p.plan_type==='lifetime'?'永久有效':`${planTypeDesc(p.plan_type)}有效`]}))}
  }catch(e){}
}
</script>

<style scoped>
.membership-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 1100px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-hero { text-align: center; margin-bottom: 40px; }
.page-title { font-size: 2rem; font-weight: 800; color: var(--primary); margin-bottom: 8px; }
.page-desc { color: var(--text-light); font-size: 1rem; }

.status-card { margin-bottom: 48px; border-radius: var(--radius-xl); }
.status-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.status-item { text-align: center; padding: 16px 8px; }
.status-val { font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.status-lbl { font-size: 0.82rem; color: var(--text-light); margin-top: 4px; }

.section-heading { font-size: 1.3rem; font-weight: 700; color: var(--primary); margin-bottom: 28px; }
.plans-row { margin-bottom: 48px; }
.plan-card {
  background: var(--bg-light); border: 1px solid var(--border); border-radius: var(--radius-xl);
  padding: 32px 20px; text-align: center; transition: all 0.35s;
  position: relative; height: 100%;
}
.plan-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-xl); }
.plan-card.popular { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 8px 30px rgba(59,130,246,0.12); }
.plan-badge { position:absolute; top:-12px; left:50%; transform:translateX(-50%); background:linear-gradient(135deg,#f59e0b,#fbbf24); color:#fff; font-size:0.72rem; padding:3px 14px; border-radius:var(--radius-full); font-weight:600; }
.plan-icon { margin-bottom: 12px; color: var(--accent); }
.plan-name { font-size: 1.15rem; font-weight: 700; color: var(--primary); margin-bottom: 4px; }
.plan-type { font-size: 0.82rem; color: var(--text-light); margin-bottom: 16px; }
.plan-price { margin-bottom: 24px; min-height: 48px; display: flex; align-items: baseline; justify-content: center; gap: 4px; }
.price-current { font-size: 2.4rem; font-weight: 800; color: var(--primary); }
.price-currency { font-size: 1rem; color: var(--text-secondary); }
.price-original { font-size: 0.85rem; color: var(--text-light); text-decoration: line-through; margin-left: 8px; }
.plan-benefits { list-style: none; text-align: left; margin-bottom: 24px; }
.plan-benefits li { padding: 7px 0; font-size: 0.85rem; color: var(--text); display: flex; align-items: center; gap: 6px; }
.plan-btn { width: 100%; height: 46px; font-size: 0.95rem; font-weight: 600; }

.redeem-area { padding: 8px 0; }
.redeem-input { margin-bottom: 8px; }
.redeem-hint { font-size: 0.8rem; color: var(--text-light); }

.pay-modal { padding: 8px 0; }
.pay-plan-info { display:flex; justify-content:space-between; align-items:center; padding:14px 16px; background:var(--bg-light); border-radius:var(--radius); margin-bottom:20px; }
.pay-plan-name { font-weight: 600; }
.pay-plan-price { font-size: 1.2rem; color: var(--primary); font-weight: 700; }
.pay-methods { display: flex; gap: 12px; margin-bottom: 20px; }
.pay-methods .el-radio-button { flex: 1; }
.pay-btn { width: 100%; height: 46px; font-size: 1rem; font-weight: 600; }
.pay-tip { font-size: 0.75rem; color: var(--text-light); text-align: center; margin-top: 12px; }
.compare-table { border-radius: var(--radius); }

@media (max-width: 768px) {
  .page-title { font-size: 1.5rem; }
}
</style>
