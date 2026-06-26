<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar"><h2>套餐管理</h2></div>
      <el-card shadow="never">
        <el-table :data="plans" stripe v-loading="loading" border class="manage-table">
          <el-table-column prop="name" label="套餐名称" min-width="120" />
          <el-table-column label="类型" width="100">
            <template #default="{row}"><el-tag :type="row.plan_type==='premium'?'danger':row.plan_type==='basic'?'warning':'info'" size="small" effect="light">{{ row.plan_type }}</el-tag></template>
          </el-table-column>
          <el-table-column label="价格" width="100">
            <template #default="{row}"><span style="color:#ef4444;font-weight:700;">￥{{ row.price }}</span></template>
          </el-table-column>
          <el-table-column label="每日解析" width="100" align="center">
            <template #default="{row}">{{ row.daily_parse_count }}</template>
          </el-table-column>
          <el-table-column label="每日生成" width="100" align="center">
            <template #default="{row}">{{ row.daily_generate_count }}</template>
          </el-table-column>
          <el-table-column label="高清导出" width="100" align="center">
            <template #default="{row}"><el-tag v-if="row.support_hd_export" type="success" size="small" effect="light">支持</el-tag><el-tag v-else size="small">不支持</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import Sidebar from "@/components/Sidebar.vue"
import { listPlans } from "@/api/admin"

const plans=ref([]); const loading=ref(false)

async function fetchPlans(){loading.value=true;try{const res=await listPlans()
  if(res.code===200)plans.value=res.data?.records||res.data||[]}catch(e){ElMessage.error("加载失败")}finally{loading.value=false}}

onMounted(fetchPlans)
</script>
<style scoped>
.admin-layout{display:flex;min-height:100vh}.admin-main{flex:1;margin-left:240px;padding:24px;background:var(--admin-bg);min-height:100vh}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.topbar h2{font-size:1.3rem;font-weight:700;color:var(--admin-primary);margin:0}
.manage-table{border-radius:var(--admin-radius);overflow:hidden}
@media(max-width:768px){.admin-main{margin-left:0}}
</style>
