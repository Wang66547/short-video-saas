<template>
  <div class="parse-page">
    <Header />
    <div class="page-container">
      <div class="page-hero">
        <h2 class="page-title">视频解析</h2>
        <p class="page-desc">粘贴视频链接或拖拽上传，AI 智能拆解文案、分镜、BGM</p>
      </div>

      <!-- Input Card -->
      <el-card class="input-card">
        <div class="input-tabs">
          <el-radio-group v-model="inputMode">
            <el-radio-button value="single">单个解析</el-radio-button>
            <el-radio-button value="batch">批量解析</el-radio-button>
            <el-radio-button value="upload">上传文件</el-radio-button>
          </el-radio-group>
        </div>

        <template v-if="inputMode === 'single'">
          <el-input v-model="videoUrl" placeholder="粘贴抖音/快手/TikTok/YouTube 视频链接..." size="large" class="url-input">
            <template #append>
              <el-button type="primary" :loading="submitting" @click="handleParse" class="parse-btn">开始解析</el-button>
            </template>
          </el-input>
          <p class="hint">支持主流平台视频链接，最长 30 分钟</p>
        </template>

        <template v-if="inputMode === 'batch'">
          <el-input v-model="batchUrls" type="textarea" :rows="6" placeholder="每行一个视频链接，最多 50 个" class="url-input" />
          <div style="display:flex;justify-content:space-between;margin-top:8px;">
            <span class="hint">已输入 {{ batchUrls.trim().split('\\n').filter(l=>l.trim()).length }} 个链接</span>
            <el-button type="primary" :loading="submitting" @click="handleBatchParse" class="parse-btn">批量解析</el-button>
          </div>
        </template>

        <template v-if="inputMode === 'upload'">
          <el-upload drag :show-file-list="false" accept=".mp4,.avi,.mov,.mkv,.webm" :before-upload="handleBeforeUpload" :http-request="handleUpload" class="upload-area">
            <el-icon class="upload-icon" :size="48"><UploadFilled /></el-icon>
            <p class="upload-text">拖拽视频文件到此处，或 点击上传</p>
            <p class="upload-hint">支持 MP4/AVI/MOV/MKV/WebM，最大 500MB</p>
          </el-upload>
        </template>
      </el-card>

      <!-- Batch Progress -->
      <el-card v-if="batchTaskStatus" class="batch-progress-card">
        <template #header>
          <div class="batch-header">
            <span>批量解析任务</span>
            <el-tag :type="batchTaskStatus==='completed'?'success':batchTaskStatus==='failed'?'danger':'warning'" size="small">
              {{ batchTaskStatus==='completed'?'全部完成':batchTaskStatus==='failed'?'部分失败':'处理中' }}
            </el-tag>
          </div>
        </template>
        <el-progress :percentage="batchProgressPercent" :status="batchTaskStatus==='completed'?'success':batchTaskStatus==='failed'?'exception':undefined" :stroke-width="10" striped striped-flow="1s" />
        <p style="margin-top:8px;font-size:0.85rem;color:var(--text-light);">已完成 {{ batchCompleted }} / {{ batchTotal }} 个视频</p>
      </el-card>

      <!-- Progress -->
      <el-card v-if="taskStatus && taskStatus !== 'success' && taskStatus !== 'failed'" class="progress-card" :class="{ 'progress-active': taskStatus === 'processing' }">
        <div class="progress-header">
          <el-icon :size="20" color="#3b82f6" class="spin"><Loading /></el-icon>
          <span class="progress-text">{{ progressText }}</span>
        </div>
        <el-progress :percentage="progressPercent" :status="taskStatus==='success'?'success':taskStatus==='failed'?'exception':undefined" :stroke-width="8" striped striped-flow="1s" />
        <div class="progress-steps">
          <div class="step" :class="{ active: progressStep>=1, done: progressStep>1 }"><el-icon><VideoCamera /></el-icon><span>读取视频</span></div>
          <div class="step" :class="{ active: progressStep>=2, done: progressStep>2 }"><el-icon><Headset /></el-icon><span>语音转写</span></div>
          <div class="step" :class="{ active: progressStep>=3, done: progressStep>3 }"><el-icon><Document /></el-icon><span>字幕识别</span></div>
          <div class="step" :class="{ active: progressStep>=4, done: progressStep>4 }"><el-icon><Connection /></el-icon><span>分镜拆解</span></div>
          <div class="step" :class="{ active: progressStep>=5, done: progressStep>5 }"><el-icon><Headset /></el-icon><span>BGM 提取</span></div>
        </div>
      </el-card>

      <!-- Error -->
      <el-alert v-if="errorMsg" :title="errorMsg" type="error" closable show-icon style="margin-bottom:24px;border-radius:var(--radius-lg);" />

      <!-- Results -->
      <template v-if="parseResult">
        <!-- Script -->
        <el-card class="result-card">
          <template #header>
            <div class="result-header">
              <span>📝 文案脚本</span>
              <div class="result-actions">
                <el-button round size="small" @click="copyScript"><el-icon><CopyDocument /></el-icon> 复制</el-button>
                <el-button round size="small" type="primary" @click="openRewriteDialog"><el-icon><MagicStick /></el-icon> AI 改写</el-button>
              </div>
            </div>
          </template>
          <div class="script-meta">
            <span>时长: {{ parseResult.duration || '-' }}</span>
            <span>分辨率: {{ parseResult.resolution || '-' }}</span>
            <span>FPS: {{ parseResult.fps || '-' }}</span>
          </div>
          <div class="script-body">
            <div class="script-line" v-for="(line, i) in scriptLines" :key="i">
              <span class="line-time">{{ line.start_time }}</span>
              <span class="line-text">{{ line.text }}</span>
            </div>
            <p v-if="scriptLines.length===0" class="empty-hint">暂无文案内容</p>
          </div>
        </el-card>

        <!-- Scenes -->
        <el-card class="result-card">
          <template #header><span>🎬 分镜脚本</span></template>
          <el-table :data="sceneList" stripe size="default">
            <el-table-column prop="index" label="#" width="60" align="center" />
            <el-table-column label="时间段" width="200">
              <template #default="{row}">{{ row.start_time }} - {{ row.end_time }}</template>
            </el-table-column>
            <el-table-column prop="description" label="画面描述" />
            <el-table-column prop="voiceover" label="旁白/台词" />
          </el-table>
        </el-card>

        <!-- BGM & Watermark -->
        <el-card class="result-card" v-if="parseResult.bgm_url || parseResult.watermark">
          <template #header><span>🎵 音频信息</span></template>
          <div class="bgm-area" v-if="parseResult.bgm_url">
            <audio :src="parseResult.bgm_url" controls />
          </div>
          <div class="wm-info" v-if="parseResult.watermark">
            <p><strong>水印信息：</strong>{{ parseResult.watermark }}</p>
            <p v-if="parseResult.delogo_filter"><strong>去水印滤镜：</strong>{{ parseResult.delogo_filter }}</p>
          </div>
        </el-card>

        <!-- Actions -->
        <div class="action-bar">
          <el-button type="primary" size="large" round class="action-btn" @click="startReplicate"><el-icon><VideoCamera /></el-icon> 开始复刻</el-button>
          <el-button size="large" round class="action-btn action-btn-secondary" @click="resetAll"><el-icon><Refresh /></el-icon> 重新开始</el-button>
        </div>
      </template>
    </div>

    <!-- Rewrite Dialog -->
    <el-dialog v-model="rewriteDialogVisible" title="AI 改写脚本" width="600px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="改写模式">
          <el-select v-model="rewriteMode" style="width:100%;">
            <el-option label="同义词替换" value="synonym" />
            <el-option label="句式变换" value="paraphrase" />
            <el-option label="风格转换" value="style" />
          </el-select>
        </el-form-item>
        <el-form-item label="创意度">
          <el-slider v-model="rewriteTemp" :min="0.1" :max="1" :step="0.1" />
        </el-form-item>
        <el-form-item label="原文">
          <el-input v-model="rewritePreview" type="textarea" :rows="8" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rewriteDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="rewriting" @click="doRewrite">开始改写</el-button>
      </template>
    </el-dialog>

    <Footer />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { UploadFilled, Loading, VideoCamera, Headset, Document, Connection, CopyDocument, Download, MagicStick, Refresh } from "@element-plus/icons-vue"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"
import { useUserStore } from "@/stores/user"
import { createParse, uploadParse, batchCreateParse, getBatchParseStatus, rewriteScript as rewriteApi, getRewriteModes as getModesApi, synthesizeVoice, getVoices } from "@/api/video"

const router = useRouter()
const userStore = useUserStore()
const inputMode = ref("single")
const videoUrl = ref("")
const batchUrls = ref("")
const submitting = ref(false)
const taskStatus = ref(null)
const progressPercent = ref(0)
const progressStep = ref(0)
const errorMsg = ref("")
const parseResult = ref(null)
const batchTaskStatus = ref(null)
const batchProgressPercent = ref(0)
const batchCompleted = ref(0)
const batchTotal = ref(0)
let batchPollTimer = null
const rewriteDialogVisible = ref(false)
const rewriteMode = ref("synonym")
const rewriteTemp = ref(0.7)
const rewritePreview = ref("")
const rewriting = ref(false)
const rewriteModes = ref({})
const voiceDialogVisible = ref(false)
const selectedVoice = ref("female_warm")
const voiceSpeed = ref(1.0)
const availableVoices = ref({})

const progressText = computed(() => {
  const texts = { idle: "", processing: "正在解析中...", success: "解析完成！", failed: "解析失败" }
  return texts[taskStatus.value] || ""
})
const scriptLines = computed(() => {
  if (!parseResult.value?.script) return []
  try { return typeof parseResult.value.script === "string" ? JSON.parse(parseResult.value.script) : parseResult.value.script }
  catch { return [] }
})
const sceneList = computed(() => {
  if (!parseResult.value?.scenes) return []
  try { return typeof parseResult.value.scenes === "string" ? JSON.parse(parseResult.value.scenes) : parseResult.value.scenes }
  catch { return [] }
})

function handleBeforeUpload(file) {
  const types=["video/mp4","video/avi","video/quicktime","video/x-msvideo","video/x-matroska","video/webm"]
  const ok=types.includes(file.type); const size=file.size/1024/1024<500
  if(!ok) ElMessage.error("不支持的文件格式"); if(!size) ElMessage.error("文件大小不能超过500MB")
  return ok && size
}
async function handleUpload({file}) {
  submitting.value=true
  try { const fd=new FormData(); fd.append("file",file); const res=await uploadParse(fd)
    if(res.code===200||res.code===201){ElMessage.success("上传成功，开始解析");simulateProgress()}
  } catch(e){ElMessage.error("上传失败")} finally{submitting.value=false}
}
async function handleParse() {
  if(!videoUrl.value.trim()){ElMessage.warning("请输入视频链接");return}
  submitting.value=true; taskStatus.value="processing"; progressPercent.value=0; progressStep.value=0; errorMsg.value=""
  try { const res=await createParse({video_url:videoUrl.value.trim()})
    if(res.code===200||res.code===201){ElMessage.success("任务已提交，正在解析中...");simulateProgress()}
  } catch(e){errorMsg.value=e.message||e.detail||"解析失败"; taskStatus.value="failed"}
  finally{submitting.value=false}
}
async function handleBatchParse() {
  const urls=batchUrls.value.trim().split("\\n").filter(l=>l.trim())
  if(urls.length===0){ElMessage.warning("请至少输入一个视频链接");return}
  if(urls.length>50){ElMessage.warning("最多支持50个视频");return}
  batchTotal.value=urls.length; batchCompleted.value=0; batchProgressPercent.value=0; batchTaskStatus.value="processing"
  submitting.value=true
  try { const res=await batchCreateParse({video_urls:urls})
    if(res.code===201){const taskId=res.data?.batch_task_id; if(taskId)pollBatchStatus(taskId); ElMessage.success("已提交"+urls.length+"个视频")}
  } catch(e){ElMessage.error("批量提交失败"); batchTaskStatus.value="failed"}
  finally{submitting.value=false}
}
function pollBatchStatus(taskId) {
  const poll=async()=>{ try { const res=await getBatchParseStatus(taskId)
    if(res.code===200&&res.data){ batchCompleted.value=res.data.completed||0; batchProgressPercent.value=Math.round((batchCompleted.value/batchTotal.value)*100)
      if(res.data.status==="completed"){batchTaskStatus.value="completed";clearInterval(batchPollTimer)}
      else if(res.data.status==="failed"){batchTaskStatus.value="failed";clearInterval(batchPollTimer)}
    }
  } catch(e){} }; poll()
  batchPollTimer=setInterval(poll,3000)
}
function simulateProgress() {
  const steps=[{pct:15,step:1,delay:1000},{pct:35,step:2,delay:3000},{pct:55,step:3,delay:2000},{pct:75,step:4,delay:2000},{pct:95,step:5,delay:2000},{pct:100,step:5,delay:1500}]
  let i=0; function next(){ if(i>=steps.length){ taskStatus.value="success"; parseResult.value={duration:"00:32",resolution:"1080x1920",fps:30,
    script:JSON.stringify([{start_time:"00:00",text:"大家好，今天给大家分享一个超级实用的技巧！"},{start_time:"00:05",text:"首先我们需要准备以下材料..."},{start_time:"00:12",text:"接下来按照步骤操作就可以了"},{start_time:"00:20",text:"最后的效果非常棒，赶紧试试吧！"}]),
    scenes:JSON.stringify([{index:1,start_time:"00:00",end_time:"00:05",duration:5,description:"开场介绍",voiceover:"大家好..."},{index:2,start_time:"00:05",end_time:"00:12",duration:7,description:"材料展示",voiceover:"首先我们需要准备..."},{index:3,start_time:"00:12",end_time:"00:20",duration:8,description:"操作步骤",voiceover:"接下来按照步骤操作..."},{index:4,start_time:"00:20",end_time:"00:32",duration:12,description:"成果展示",voiceover:"最后的效果非常棒..."}]),
    bgm_url:"",watermark:"",delogo_filter:""}; return }
    const s=steps[i++]; progressPercent.value=s.pct; progressStep.value=s.step; setTimeout(next,s.delay) }
  next()
}
function copyScript() { const text=scriptLines.value.map(l=>"["+l.start_time+"] "+l.text).join("\\n"); navigator.clipboard?.writeText(text); ElMessage.success("已复制到剪贴板") }
function downloadFile(url,name) { const a=document.createElement("a"); a.href=url; a.download=name; a.click() }
function startReplicate() { if(!parseResult.value)return; if(!userStore.isLoggedIn){ElMessage.warning("请先登录");router.push("/login");return} router.push({path:"/video/create",query:{parse_id:"mock"}}) }
function resetAll() { taskStatus.value=null; progressPercent.value=0; progressStep.value=0; errorMsg.value=""; parseResult.value=null; videoUrl.value=""; batchUrls.value=""; batchTaskStatus.value=null; if(batchPollTimer)clearInterval(batchPollTimer) }
async function openRewriteDialog() { rewriteDialogVisible.value=true
  try { const res=await getModesApi(); if(res.code===200)rewriteModes.value=res.data||{} } catch(e){}
  rewritePreview.value=scriptLines.value.map(l=>l.text).join("\\n")
}
async function doRewrite() { rewriting.value=true
  try { const res=await rewriteApi({script:rewritePreview.value,mode:rewriteMode.value,temperature:rewriteTemp.value})
    if(res.code===200)rewritePreview.value=res.data?.rewritten||res.data?.original||""; ElMessage.success("改写完成")
  } catch(e){ElMessage.error("改写失败")} finally{rewriting.value=false}
}
onMounted(() => { getVoices().then(res=>{if(res.code===200)availableVoices.value=res.data?.voices||{}}).catch(()=>{}) })
</script>

<style scoped>
.parse-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 960px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-hero { text-align: center; margin-bottom: 40px; }
.page-title { font-size: 2rem; font-weight: 800; color: var(--primary); margin-bottom: 8px; }
.page-desc { color: var(--text-light); font-size: 1rem; }
.input-card { margin-bottom: 24px; border-radius: var(--radius-xl); }
.input-tabs { margin-bottom: 24px; }
.url-input { margin-bottom: 8px; }
.hint { font-size: 0.8rem; color: var(--text-light); margin-top: 8px; display: block; }
.upload-area { padding: 48px 0; }
.upload-icon { color: var(--text-light); margin-bottom: 12px; }
.upload-text { color: var(--text); margin-bottom: 4px; font-size: 1rem; font-weight: 500; }
.upload-hint { font-size: 0.8rem; color: var(--text-light); }
.batch-progress-card { margin-bottom: 24px; border-radius: var(--radius-xl); }
.batch-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.progress-card { margin-bottom: 24px; border: 1px solid var(--accent); border-radius: var(--radius-xl); }
.progress-active { animation: pulse 2s infinite; }
.progress-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-weight: 600; }
.progress-text { font-size: 0.9rem; color: var(--text-secondary); }
.progress-steps { display: flex; justify-content: space-between; margin-top: 20px; }
.step { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--text-light); transition: all 0.3s; }
.step .el-icon { font-size: 1.3rem; }
.step.active { color: var(--accent); transform: scale(1.05); }
.step.done { color: var(--success); }
.result-card { margin-bottom: 20px; border-radius: var(--radius-xl); }
.result-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.result-actions { display: flex; gap: 8px; }
.script-meta { display: flex; gap: 24px; margin-bottom: 16px; font-size: 0.85rem; color: var(--text-light); }
.script-body { max-height: 400px; overflow-y: auto; }
.script-line { display: flex; gap: 12px; padding: 10px 12px; border-bottom: 1px solid var(--border-light); font-size: 0.9rem; transition: background 0.2s; }
.script-line:hover { background: var(--bg-light); }
.line-time { color: var(--accent); font-family: 'SF Mono', Monaco, monospace; white-space: nowrap; font-weight: 500; }
.line-text { color: var(--text); flex: 1; }
.empty-hint { color: var(--text-light); text-align: center; padding: 40px; }
.bgm-area { text-align: center; padding: 20px 0; }
.bgm-area audio { margin-bottom: 16px; width: 100%; }
.wm-info { padding: 16px 0; font-size: 0.9rem; }
.wm-info p { margin-bottom: 6px; }
.action-bar { text-align: center; padding: 32px 0; display: flex; gap: 16px; justify-content: center; }
.action-btn { min-width: 160px; height: 48px; font-size: 1rem; font-weight: 600; }
.action-btn-secondary { background: var(--bg-light); color: var(--text-light); border: 1px solid var(--border) !important; }
.spin { animation: spin 1.5s linear infinite; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(59,130,246,0.2)} 50%{box-shadow:0 0 0 12px rgba(59,130,246,0)} }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
