<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar"><h2>订单管理</h2></div>
      <el-card shadow="never">
        <el-table :data="orders" stripe v-loading="loading" border class="manage-table">
          <el-table-column prop="order_no" label="订单号" min-width="220" />
          <el-table-column label="套餐" min-width="120"><template #default="{row}">{{ row.plan_name||'-' }}</template></el-table-column>
          <el-table-column label="金额" width="100" align="center">
            <template #default="{row}"><span style="color:#ef4444;font-weight:700;">￥{{ row.paid_amount??row.amount }}</span></template>
          </el-table-column>
          <el-table-column label="支付方式" width="110" align="center">
            <template #default="{row}">{{ paymentLabel(row.payment_method) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{row}"><el-tag :type="orderType(row.payment_status)" size="small" effect="light">{{ orderLabel(row.payment_status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column prop="paid_at" label="支付时间" width="180" />
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next, jumper" style="margin-top:20px;justify-content:center;" @current-change="fetchOrders" />
      </el-card>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import Sidebar from "@/components/Sidebar.vue"
import { listOrders as apiListOrders } from "@/api/admin"

const orders=ref([]); const loading=ref(false); const page=ref(1); const pageSize=ref(20); const total=ref(0)

function orderType(s){const m={paid:"success",pending:"warning",refunded:"info",cancelled:"danger"};return m[s]||"info"}
function orderLabel(s){const m={paid:"已支付",pending:"待支付",refunded:"已退款",cancelled:"已取消"};return m[s]||s}
function paymentLabel(m){const map={wechat:"微信",alipay:"支付宝",card_key:"卡密"};return map[m]||m||'-'}

async function fetchOrders(){loading.value=true;try{const res=await apiListOrders(page.value,pageSize.value)
  if(res.code===200){const d=res.data||{};orders.value=d.records||d.items||[];total.value=d.total||d.count||0}}catch(e){ElMessage.error("加载失败")}finally{loading.value=false}}

onMounted(fetchOrders)
</script>
<style scoped>
.admin-layout{display:flex;min-height:100vh}.admin-main{flex:1;margin-left:240px;padding:24px;background:var(--admin-bg);min-height:100vh}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.topbar h2{font-size:1.3rem;font-weight:700;color:var(--admin-primary);margin:0}
.manage-table{border-radius:var(--admin-radius);overflow:hidden}
@media(max-width:768px){.admin-main{margin-left:0}}
</style>
