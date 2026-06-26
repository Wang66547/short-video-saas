<template>
  <div class="order-page">
    <Header />
    <div class="page-container">
      <h2 class="page-title">订单记录</h2>
      <el-card class="filter-card" shadow="never" style="margin-bottom:20px;">
        <el-form :inline="true">
          <el-form-item label="支付状态">
            <el-select v-model="statusFilter" placeholder="全部" clearable style="width:150px;" @change="loadOrders" class="filter-select">
              <el-option label="待支付" value="pending" />
              <el-option label="已支付" value="paid" />
              <el-option label="已退款" value="refunded" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item><el-button @click="handleReset">重置</el-button></el-form-item>
        </el-form>
      </el-card>
      <el-card shadow="never">
        <el-table :data="orders" stripe v-loading="loading" border class="order-table">
          <el-table-column prop="order_no" label="订单号" min-width="220" />
          <el-table-column label="套餐" min-width="120"><template #default="{row}">{{ row.plan_name||'-' }}</template></el-table-column>
          <el-table-column label="金额" width="100" align="center">
            <template #default="{row}"><span style="color:#ef4444;font-weight:700;font-size:1.05rem;">￥{{ row.paid_amount??row.amount }}</span></template>
          </el-table-column>
          <el-table-column label="支付方式" width="110" align="center">
            <template #default="{row}">{{ paymentLabel(row.payment_method) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{row}"><el-tag :type="orderType(row.payment_status)" size="small" effect="light">{{ orderLabel(row.payment_status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column prop="paid_at" label="支付时间" width="180" />
          <el-table-column label="操作" width="100" align="center">
            <template #default="{row}">
              <el-button v-if="row.payment_status==='pending'" link type="primary" size="small" @click="retryPay(row)">去支付</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" class="pagination" @current-change="loadOrders" />
      </el-card>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"
import { listOrders } from "@/api/payment"

const orders = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0); const statusFilter = ref("")

function orderType(s){const m={paid:"success",pending:"warning",refunded:"info",cancelled:"danger"};return m[s]||"info"}
function orderLabel(s){const m={paid:"已支付",pending:"待支付",refunded:"已退款",cancelled:"已取消"};return m[s]||s}
function paymentLabel(m){const map={wechat:"微信",alipay:"支付宝",card_key:"卡密"};return map[m]||m||'-'}

async function loadOrders(){ loading.value=true; try{ const res=await listOrders(page.value)
  if(res.code===200){const data=res.data||{}; orders.value=data.records||data.items||data.orders||[]; total.value=data.total||data.count||0}
}catch(e){ElMessage.error("加载订单失败")} finally{loading.value=false} }

function handleReset(){ statusFilter.value=""; loadOrders() }
function retryPay(row){ ElMessage.info("请回到会员中心重新下单支付") }
onMounted(loadOrders)
</script>

<style scoped>
.order-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 1100px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-title { font-size: 1.8rem; font-weight: 800; color: var(--primary); margin-bottom: 28px; }
.filter-card { border-radius: var(--radius-lg); }
.filter-select :deep(.el-input__wrapper) { border-radius: var(--radius-full); }
.order-table { border-radius: var(--radius-lg); overflow: hidden; }
.pagination { margin-top: 24px; justify-content: center; }
</style>
