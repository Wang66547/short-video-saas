<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar"><h2>视频任务管理</h2></div>
      <el-card shadow="never">
        <el-table :data="videos" stripe v-loading="loading" border class="manage-table">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column label="类型" width="100">
            <template #default="{row}"><el-tag :type="row.type==='parse'?'primary':'success'" size="small" effect="light">{{ row.type==='parse'?'解析':'生成' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{row}"><el-tag :type="statusType(row.status)" size="small" effect="light">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="进度" width="180">
            <template #default="{row}"><el-progress :percentage="Math.round((row.progress||0)*100)" :status="row.status==='success'?'success':row.status==='failed'?'exception':undefined" :stroke-width="6" /></template>
          </el-table-column>
          <el-table-column prop="video_url" label="视频链接" min-width="200">
            <template #default="{row}"><el-tooltip :content="row.video_url" placement="top"><span class="truncate">{{ row.video_url }}</span></el-tooltip></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next, jumper" style="margin-top:20px;justify-content:center;" @current-change="fetchVideos" />
      </el-card>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import Sidebar from "@/components/Sidebar.vue"
import { listParseRecords } from "@/api/admin"

const videos=ref([]); const loading=ref(false); const page=ref(1); const pageSize=ref(20); const total=ref(0)

function statusType(s){const m={success:"success",processing:"warning",pending:"info",failed:"danger"};return m[s]||"info"}
function statusLabel(s){const m={success:"完成",processing:"处理中",pending:"排队中",failed:"失败"};return m[s]||s}

async function fetchVideos(){loading.value=true;try{const res=await listParseRecords(page.value,pageSize.value)
  if(res.code===200){const d=res.data||{};videos.value=d.records||d.items||[];total.value=d.total||d.count||0}}catch(e){ElMessage.error("加载失败")}finally{loading.value=false}}

onMounted(fetchVideos)
</script>
<style scoped>
.admin-layout{display:flex;min-height:100vh}.admin-main{flex:1;margin-left:240px;padding:24px;background:var(--admin-bg);min-height:100vh}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.topbar h2{font-size:1.3rem;font-weight:700;color:var(--admin-primary);margin:0}
.manage-table{border-radius:var(--admin-radius);overflow:hidden}.truncate{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:300px}
@media(max-width:768px){.admin-main{margin-left:0}}
</style>
