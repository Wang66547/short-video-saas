<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar">
        <h2>卡密管理</h2>
        <el-button type="primary" round @click="showCreate=true"><el-icon><Plus /></el-icon> 生成卡密</el-button>
      </div>
      <el-card shadow="never">
        <el-table :data="cards" stripe v-loading="loading" border class="manage-table">
          <el-table-column prop="code" label="卡密" min-width="200" />
          <el-table-column label="套餐" width="120">
            <template #default="{row}">{{ row.plan_name||'-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{row}"><el-tag :type="row.used?'danger':'success'" size="small" effect="light">{{ row.used?'已使用':'未使用' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="used_by" label="使用者" width="120">
            <template #default="{row}">{{ row.used_by||'-' }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="100" align="center">
            <template #default="{row}"><el-button link type="danger" size="small" @click="deleteCard(row.id)">删除</el-button></template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next, jumper" style="margin-top:20px;justify-content:center;" @current-change="fetchCards" />
      </el-card>
    </div>

    <el-dialog v-model="showCreate" title="生成卡密" width="420px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="套餐"><el-select v-model="form.plan_id" style="width:100%"><el-option label="基础会员" value="basic" /><el-option label="高级会员" value="premium" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.count" :min="1" :max="100" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="generateCards">生成</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus } from "@element-plus/icons-vue"
import Sidebar from "@/components/Sidebar.vue"
import { listCardKeys, batchGenerateCardKeys, deleteCardKey } from "@/api/admin"

const cards=ref([]); const loading=ref(false); const page=ref(1); const pageSize=ref(20); const total=ref(0)
const showCreate=ref(false); const form=reactive({ plan_id:"basic", count:10 })

async function fetchCards(){loading.value=true;try{const res=await listCardKeys(page.value,pageSize.value)
  if(res.code===200){const d=res.data||{};cards.value=d.records||d.items||[];total.value=d.total||d.count||0}}catch(e){ElMessage.error("加载失败")}finally{loading.value=false}}

async function generateCards(){
  try{const res=await batchGenerateCardKeys(form);if(res.code===200){ElMessage.success("生成成功");showCreate.value=false;fetchCards()}}
  catch(e){ElMessage.error("生成失败")}
}

async function deleteCard(id){
  try{await ElMessageBox.confirm("确定删除此卡密？","提示",{type:"warning"});await deleteCardKey(id);ElMessage.success("已删除");fetchCards()}catch(e){if(e!=="cancel")ElMessage.error("删除失败")}
}

onMounted(fetchCards)
</script>
<style scoped>
.admin-layout{display:flex;min-height:100vh}.admin-main{flex:1;margin-left:240px;padding:24px;background:var(--admin-bg);min-height:100vh}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.topbar h2{font-size:1.3rem;font-weight:700;color:var(--admin-primary);margin:0}
.manage-table{border-radius:var(--admin-radius);overflow:hidden}
@media(max-width:768px){.admin-main{margin-left:0}}
</style>
