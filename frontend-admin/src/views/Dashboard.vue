<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="admin-topbar">
        <div class="topbar-left">
          <h2 class="page-title">数据概览</h2>
        </div>
        <div class="topbar-right">
          <el-tag size="default" type="success" effect="dark">在线</el-tag>
          <span class="topbar-time">{{ currentTime }}</span>
        </div>
      </div>

      <el-row :gutter="16" style="margin-top:20px;">
        <el-col :xs="12" :sm="8" :lg="4" v-for="item in metricCards" :key="item.label">
          <div class="metric-card" :class="'mc-'+item.color">
            <div class="mc-icon"><el-icon :size="24"><component :is="item.icon" /></el-icon></div>
            <div class="mc-info">
              <div class="mc-value">{{ item.value }}</div>
              <div class="mc-label">{{ item.label }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top:20px;">
        <el-col :xs="24" :lg="16">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>营收趋势</span>
                <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
                  <el-radio-button :label="7">近7天</el-radio-button>
                  <el-radio-button :label="30">近30天</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div class="chart-container" ref="revenueChartRef">
              <canvas ref="revenueCanvas" width="800" height="300"></canvas>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="chart-card">
            <template #header><span>用户分布</span></template>
            <div class="user-distribution">
              <div class="dist-item" v-for="d in userDist" :key="d.label">
                <div class="dist-bar-bg"><div class="dist-bar" :style="{width:d.percent+'%',background:d.color}"></div></div>
                <div class="dist-label">{{ d.label }}</div>
                <div class="dist-value">{{ d.value }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top:20px;">
        <el-col :span="24">
          <el-card shadow="never" class="chart-card">
            <template #header><div class="card-header"><span>业务趋势</span></div></template>
            <div class="chart-container" ref="bizChartRef"><canvas ref="bizCanvas" width="800" height="280"></canvas></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top:20px;">
        <el-col :span="24">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="card-header" style="justify-content:space-between;">
                <span>最近订单</span>
                <router-link to="/admin/orders" style="color:#3b82f6;font-size:0.85rem;">查看全部 →</router-link>
              </div>
            </template>
            <el-table :data="recentOrders" stripe size="small">
              <el-table-column prop="order_no" label="订单号" width="220" />
              <el-table-column label="金额" width="100">
                <template #default="{row}"><span style="color:#ef4444;font-weight:600;">￥{{ row.amount }}</span></template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{row}"><el-tag :type="orderTagType(row.payment_status)" size="small">{{ orderTagLabel(row.payment_status) }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="180" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from "vue"
import Sidebar from "@/components/Sidebar.vue"
import { getStats, getStatsTrend } from "@/api/admin"
import { User, Document, Money, VideoCamera, TrendCharts, ShoppingBag, Headset, Connection, Brush, Timer } from "@element-plus/icons-vue"

const stats = ref({})
const trendData = ref([])
const trendDays = ref(7)
const revenueCanvas = ref(null)
const bizCanvas = ref(null)
const bizChartRef = ref(null)
const revenueChartRef = ref(null)
const recentOrders = ref([])
const userDist = ref([])
const metricCards = ref([])
let clockTimer = null
const currentTime = ref("")

function updateClock(){ const now=new Date(); currentTime.value=now.toLocaleString("zh-CN") }

function drawLineChart(canvas,data,labels,series){
  if(!canvas)return;
  const ctx=canvas.getContext("2d");
  const W=canvas.width,H=canvas.height;
  ctx.clearRect(0,0,W,H);
  const pad={t:20,r:20,b:40,l:50};
  const cW=W-pad.l-pad.r, cH=H-pad.t-pad.b;
  let maxVal=0;
  series.forEach(s=>{s.data.forEach(v=>{if(v>maxVal)maxVal=v})});
  maxVal*=1.1;
  // Grid
  ctx.strokeStyle="#f1f5f9";ctx.lineWidth=1;
  for(let i=0;i<=4;i++){const y=pad.t+cH*(1-i/4);ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(W-pad.r,y);ctx.stroke();
    ctx.fillStyle="#94a3b8";ctx.font="11px sans-serif";ctx.textAlign="right";ctx.fillText(Math.round(maxVal*i/4),pad.l-8,y+4);}
  // Labels
  ctx.fillStyle="#94a3b8";ctx.font="11px sans-serif";ctx.textAlign="center";
  labels.forEach((l,i)=>{const x=pad.l+(cW/(labels.length-1||1))*i;ctx.fillText(l,x,H-pad.b+20)});
  // Lines
  series.forEach(s=>{
    ctx.beginPath();ctx.strokeStyle=s.color;ctx.lineWidth=2.5;ctx.lineJoin="round";
    s.data.forEach((v,i)=>{const x=pad.l+(cW/(s.data.length-1||1))*i, y=pad.t+cH*(1-v/maxVal);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});
    ctx.stroke();
    if(s.fill){ctx.lineTo(pad.l+cW,pad.t+cH);ctx.lineTo(pad.l,pad.t+cH);ctx.closePath();
      const grad=ctx.createLinearGradient(0,pad.t,0,pad.t+cH);grad.addColorStop(0,s.color+"33");grad.addColorStop(1,s.color+"05");ctx.fillStyle=grad;ctx.fill();}
  });
}

async function loadStats(){
  try{
    const res=await getStats()
    if(res.code===200){
      const d=res.data||{}
      stats.value=d
      const total=d.total_users||1
      metricCards.value=[
        {value:d.total_users||0,label:"总用户",icon:"User",color:"blue"},
        {value:d.active_users||0,label:"活跃用户",icon:"Headset",color:"green"},
        {value:d.total_orders||0,label:"总订单",icon:"ShoppingBag",color:"purple"},
        {value:"￥"+(d.total_revenue||0).toFixed(0),label:"总收入",icon:"Money",color:"orange"},
        {value:d.total_parses||0,label:"总解析",icon:"VideoCamera",color:"red"},
        {value:d.total_generates||0,label:"总生成",icon:"TrendCharts",color:"cyan"},
      ]
      userDist.value=[
        {label:"免费版",value:d.total_users-(d.active_users||0),percent:Math.round(((d.total_users-(d.active_users||0))/total)*100),color:"#94a3b8"},
        {label:"基础会员",value:Math.floor(total*0.15),percent:15,color:"#f59e0b"},
        {label:"高级会员",value:Math.floor(total*0.1),percent:10,color:"#3b82f6"},
      ]
      recentOrders.value=[]
    }
  }catch(e){console.error(e)}
}

async function loadTrend(){
  try{
    const res=await getStatsTrend(parseInt(trendDays.value))
    if(res.code===200){
      trendData.value=res.data?.trends||[]
      await nextTick(()=>{
        const labels=trendData.value.map(d=>d.date||"")
        const revData=trendData.value.map(d=>d.revenue||0)
        const ordData=trendData.value.map(d=>d.orders||0)
        if(revenueCanvas.value)drawLineChart(revenueCanvas.value,trendData.value,labels,[{data:revData,color:"#3b82f6",fill:true},{data:ordData.map(v=>v*50),color:"#10b981",fill:false}])
        const parData=trendData.value.map(d=>d.parses||0)
        const genData=trendData.value.map(d=>d.generates||0)
        if(bizCanvas.value)drawLineChart(bizCanvas.value,trendData.value,labels,[{data:parData,color:"#8b5cf6",fill:true},{data:genData,color:"#f59e0b",fill:false}])
      })
    }
  }catch(e){console.error(e)}
}

function orderTagType(s){const m={paid:"success",pending:"warning",refunded:"info",cancelled:"danger"};return m[s]||"info"}
function orderTagLabel(s){const m={paid:"已支付",pending:"待支付",refunded:"已退款",cancelled:"已取消"};return m[s]||s}

onMounted(()=>{loadStats();loadTrend();updateClock();clockTimer=setInterval(updateClock,1000)})
onUnmounted(()=>{if(clockTimer)clearInterval(clockTimer)})
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }
.admin-main {
  flex: 1; margin-left: 240px; padding: 0 28px 28px;
  background: var(--admin-bg); min-height: 100vh;
}
.admin-topbar { display:flex; justify-content:space-between; align-items:center; padding:18px 0 0; }
.page-title { font-size:1.4rem; font-weight:700; color:var(--admin-primary); margin:0; }
.topbar-right { display:flex; align-items:center; gap:12px; }
.topbar-time { font-size:0.85rem; color:var(--admin-text-light); font-family:monospace; }

.metric-card {
  display:flex; align-items:center; gap:14px;
  background:var(--admin-white); border-radius:var(--admin-radius);
  padding:18px 16px; box-shadow:var(--admin-shadow);
  border: 1px solid var(--admin-border);
  margin-bottom:16px; transition:all 0.25s;
}
.metric-card:hover { transform:translateY(-2px); box-shadow:var(--admin-shadow-md); }
.mc-icon {
  width:48px; height:48px; border-radius:12px;
  display:flex; align-items:center; justify-content:center; color:#fff; flex-shrink:0;
}
.mc-blue .mc-icon { background:linear-gradient(135deg,#3b82f6,#2563eb); }
.mc-green .mc-icon { background:linear-gradient(135deg,#10b981,#059669); }
.mc-purple .mc-icon { background:linear-gradient(135deg,#8b5cf6,#7c3aed); }
.mc-orange .mc-icon { background:linear-gradient(135deg,#f59e0b,#d97706); }
.mc-red .mc-icon { background:linear-gradient(135deg,#ef4444,#dc2626); }
.mc-cyan .mc-icon { background:linear-gradient(135deg,#06b6d4,#0891b2); }
.mc-value { font-size:1.3rem; font-weight:700; color:var(--admin-text); }
.mc-label { font-size:0.78rem; color:var(--admin-text-light); margin-top:2px; }

.chart-card { margin-bottom:16px; border-radius:var(--admin-radius-lg); }
.card-header { display:flex; justify-content:space-between; align-items:center; font-weight:600; }
.chart-container { position:relative; }
.chart-container canvas { width:100%; height:300px; display:block; }
.user-distribution { padding:16px 0; }
.dist-item { margin-bottom:16px; }
.dist-bar-bg { height:10px; background:#334155; border-radius:5px; overflow:hidden; margin-bottom:6px; }
.dist-bar { height:100%; border-radius:5px; transition:width 0.6s ease; }
.dist-label { font-size:0.85rem; color:var(--admin-text-light); float:left; }
.dist-value { font-size:0.85rem; font-weight:600; color:var(--admin-text); float:right; }

@media(max-width:768px){ .admin-main{margin-left:0} }
</style>
