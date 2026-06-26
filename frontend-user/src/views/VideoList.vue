<template>
  <div class="workbench-page">
    <Header />
    <div class="page-container">
      <div class="page-header">
        <div>
          <h2 class="page-title">复刻工作台</h2>
          <p class="page-subtitle">管理你的解析和生成记录</p>
        </div>
        <router-link to="/video/create">
          <el-button type="primary" round class="new-btn">
            <el-icon><Plus /></el-icon> 新建解析
          </el-button>
        </router-link>
      </div>

      <el-tabs v-model="activeTab" class="workbench-tabs" tab-class="workbench-tab">
        <el-tab-pane label="解析记录" name="parse">
          <div class="tab-toolbar">
            <el-input v-model="parseSearch" placeholder="搜索视频链接..." clearable style="width: 300px" prefix-icon="Search" @input="loadParseRecords" class="search-input" />
          </div>
          <el-table :data="parseRecords" stripe v-loading="parseLoading" border class="workbench-table">
            <el-table-column prop="id" label="ID" width="70" align="center" />
            <el-table-column label="视频地址" min-width="250">
              <template #default="{row}"><el-tooltip :content="row.video_url" placement="top"><span class="truncate">{{ row.video_url }}</span></el-tooltip></template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{row}"><el-tag :type="parseStatusType(row.status)" size="small" effect="light">{{ parseStatusLabel(row.status) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="进度" width="180">
              <template #default="{row}"><el-progress :percentage="Math.round((row.progress||0)*100)" :status="row.status==='success'?'success':row.status==='failed'?'exception':undefined" :stroke-width="6" /></template>
            </el-table-column>
            <el-table-column label="耗时" width="100" align="center">
              <template #default="{row}">{{ row.duration ? row.duration+'s' : '-' }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="200" fixed="right" align="center">
              <template #default="{row}">
                <el-button link type="primary" size="small" @click="viewParseDetail(row)">查看</el-button>
                <el-button link type="primary" size="small" @click="replicateFromParse(row)">复刻</el-button>
                <el-button link type="danger" size="small" @click="deleteParseItem(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination v-model:current-page="parsePage" :page-size="20" :total="parseTotal" layout="total, prev, pager, next" class="pagination" @current-change="loadParseRecords" />
        </el-tab-pane>

        <el-tab-pane label="生成记录" name="generate">
          <div class="tab-toolbar">
            <el-radio-group v-model="genStatusFilter" size="small" @change="loadGenerateRecords">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="success">成功</el-radio-button>
              <el-radio-button value="processing">生成中</el-radio-button>
              <el-radio-button value="failed">失败</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="generateRecords" stripe v-loading="genLoading" border class="workbench-table">
            <el-table-column prop="id" label="ID" width="70" align="center" />
            <el-table-column label="模式" width="100" align="center">
              <template #default="{row}"><el-tag :type="row.generate_mode==='ai_generate'?'primary':'success'" size="small" effect="light">{{ row.generate_mode==='ai_generate'?'AI生成':'本地合成' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="状态" width="120" align="center">
              <template #default="{row}"><el-tag :type="genStatusType(row.status)" size="small" effect="light">{{ genStatusLabel(row.status) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="进度" width="180">
              <template #default="{row}"><el-progress :percentage="Math.round((row.progress||0)*100)" :status="row.status==='success'?'success':row.status==='failed'?'exception':undefined" :stroke-width="6" /></template>
            </el-table-column>
            <el-table-column prop="output_video_url" label="视频" width="100" align="center">
              <template #default="{row}"><el-button v-if="row.output_video_url" link type="primary" size="small" @click="window.open(row.output_video_url,'_blank')"><el-icon><VideoPlay /></el-icon></el-button></template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template #default="{row}">
                <el-button link type="primary" size="small" @click="playVideo(row)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-button link type="primary" size="small" @click="downloadVideo(row)"><el-icon><Download /></el-icon></el-button>
                <el-button link type="danger" size="small" @click="deleteGenItem(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination v-model:current-page="genPage" :page-size="20" :total="genTotal" layout="total, prev, pager, next" class="pagination" @current-change="loadGenerateRecords" />
        </el-tab-pane>
      </el-tabs>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus, VideoPlay, Download } from "@element-plus/icons-vue"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"
import { listParseRecords, listGenerateRecords, deleteParse as delParse, deleteGenerate as delGen } from "@/api/video"

const router = useRouter()
const activeTab = ref("parse")
const parseRecords = ref([]); const parsePage = ref(1); const parseTotal = ref(0); const parseLoading = ref(false); const parseSearch = ref("")
const generateRecords = ref([]); const genPage = ref(1); const genTotal = ref(0); const genLoading = ref(false); const genStatusFilter = ref("")

function parseStatusType(s){const m={success:"success",processing:"warning",pending:"info",failed:"danger"};return m[s]||"info"}
function parseStatusLabel(s){const m={success:"完成",processing:"处理中",pending:"排队中",failed:"失败"};return m[s]||s}
function genStatusType(s){const m={success:"success",processing:"warning",pending:"info",failed:"danger",editing:"info",ai_generating:"warning"};return m[s]||"info"}
function genStatusLabel(s){const m={success:"完成",processing:"处理中",pending:"排队中",failed:"失败",editing:"编辑中",ai_generating:"生成中"};return m[s]||s}

async function loadParseRecords(){parseLoading.value=true;try{const res=await listParseRecords(parsePage.value)
  if(res.code===200){parseRecords.value=res.data?.records||res.data?.items||[];parseTotal.value=res.data?.total||0}}catch(e){ElMessage.error("加载解析记录失败")}finally{parseLoading.value=false}}
async function loadGenerateRecords(){genLoading.value=true;try{const res=await listGenerateRecords(genPage.value)
  if(res.code===200){generateRecords.value=res.data?.records||res.data?.items||[];genTotal.value=res.data?.total||0}}catch(e){ElMessage.error("加载生成记录失败")}finally{genLoading.value=false}}

function viewParseDetail(row){ElMessage.info("解析详情查看功能")}
function replicateFromParse(row){if(!row.status==="success"){ElMessage.warning("解析完成后才能复刻");return} router.push({path:"/video/create",query:{parse_id:row.id}})}
function playVideo(row){if(row.output_video_url)window.open(row.output_video_url,"_blank")}
function downloadVideo(row){if(row.output_video_url){const a=document.createElement("a");a.href=row.output_video_url;a.download="replicated_video.mp4";a.click()}}

async function deleteParseItem(id){try{await ElMessageBox.confirm("确定删除此解析记录？","提示",{type:"warning"});const res=await delParse(id)
  if(res.code===200){ElMessage.success("删除成功");loadParseRecords()}}catch(e){}}
async function deleteGenItem(id){try{await ElMessageBox.confirm("确定删除此生成记录？","提示",{type:"warning"});const res=await delGen(id)
  if(res.code===200){ElMessage.success("删除成功");loadGenerateRecords()}}catch(e){}}

onMounted(()=>{loadParseRecords();loadGenerateRecords()})
</script>

<style scoped>
.workbench-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 1280px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
.page-title { font-size: 1.8rem; font-weight: 800; color: var(--primary); margin: 0 0 4px; }
.page-subtitle { color: var(--text-light); font-size: 0.95rem; margin: 0; }
.new-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  box-shadow: 0 4px 12px rgba(59,130,246,0.3) !important;
  font-weight: 600; padding: 0 24px !important;
}
.workbench-tabs { margin-top: 8px; }
.workbench-tabs :deep(.el-tabs__header) { margin-bottom: 24px; }
.workbench-tabs :deep(.el-tabs__item) { font-weight: 600; padding: 0 24px; height: 48px; line-height: 48px; font-size: 0.95rem; }
.workbench-tabs :deep(.el-tabs__active-bar) { background: linear-gradient(90deg, #3b82f6, #8b5cf6); height: 3px; }
.tab-toolbar { display: flex; justify-content: space-between; margin-bottom: 20px; }
.search-input :deep(.el-input__wrapper) { border-radius: var(--radius-full); }
.workbench-table { border-radius: var(--radius-lg); overflow: hidden; }
.pagination { margin-top: 24px; justify-content: center; }
.truncate { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px; }
</style>
