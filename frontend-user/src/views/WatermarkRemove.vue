<template>
  <div class="watermark-page">
    <Header />
    <div class="page-container">
      <div class="page-hero">
        <h2 class="page-title">去水印工具</h2>
        <p class="page-desc">上传带水印的视频，AI 自动识别并去除水印区域</p>
      </div>

      <el-card class="upload-card" shadow="hover">
        <el-upload drag :show-file-list="false" accept=".mp4,.avi,.mov,.mkv,.webm" :before-upload="handleBeforeUpload" :http-request="handleUpload" class="watermark-upload">
          <el-icon class="upload-icon" :size="56"><UploadFilled /></el-icon>
          <p class="upload-text">拖拽视频文件到此处，或 点击上传</p>
          <p class="upload-hint">支持 MP4/AVI/MOV/MKV，最大 500MB</p>
        </el-upload>
        <div class="or-divider"><span>或者粘贴链接</span></div>
        <div class="url-input-area">
          <el-input v-model="videoUrl" placeholder="粘贴视频链接..." size="large">
            <template #append><el-button type="primary" :loading="submitting" @click="handleUrlProcess">处理</el-button></template>
          </el-input>
        </div>
      </el-card>

      <el-card v-if="processing && processing !== 'done' && processing !== 'error'" class="progress-card" shadow="hover">
        <div class="progress-header">
          <el-icon :size="20" color="#3b82f6" class="spin"><Loading /></el-icon>
          <span>{{ progressText }}</span>
        </div>
        <el-progress :percentage="progressPercent" :status="processing==='done'?'success':processing==='error'?'exception':undefined" :stroke-width="8" />
      </el-card>

      <el-alert v-if="errorMsg" :title="errorMsg" type="error" closable show-icon style="margin-bottom:24px;border-radius:var(--radius-lg);" />

      <el-card v-if="resultReady" class="result-card" shadow="hover">
        <template #header>
          <div class="result-header">
            <span>处理完成</span>
            <div class="result-actions">
              <el-button type="success" round @click="downloadResult"><el-icon><Download /></el-icon> 下载成品</el-button>
              <el-button round @click="reset">重新处理</el-button>
            </div>
          </div>
        </template>
        <div class="compare-area">
          <div class="compare-side">
            <p class="compare-label">处理前</p>
            <div class="video-preview"><video :src="originalUrl" controls style="width:100%;border-radius:var(--radius);" /></div>
          </div>
          <div class="compare-arrow"><el-icon :size="28"><ArrowRight /></el-icon></div>
          <div class="compare-side">
            <p class="compare-label">处理后</p>
            <div class="video-preview"><video :src="resultUrl" controls style="width:100%;border-radius:var(--radius);" /></div>
          </div>
        </div>
      </el-card>

      <div class="features-grid">
        <div class="feat-item" v-for="f in feats" :key="f.title">
          <div class="feat-icon" :style="{background:f.bg}"><el-icon :size="24" :color="f.color"><component :is="f.icon" /></el-icon></div>
          <h4>{{ f.title }}</h4>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref } from "vue"
import { ElMessage } from "element-plus"
import { UploadFilled, Loading, Download, ArrowRight, MagicStick, Check, Timer } from "@element-plus/icons-vue"
import Header from "@/components/Header.vue"
import Footer from "@/components/Footer.vue"

const videoUrl = ref("")
const submitting = ref(false)
const processing = ref(null)
const progressPercent = ref(0)
const progressText = ref("")
const errorMsg = ref("")
const resultReady = ref(false)
const originalUrl = ref("")
const resultUrl = ref("")

const progressSteps = [
  { pct: 15, text: "正在分析视频..." },
  { pct: 35, text: "识别水印位置..." },
  { pct: 60, text: "生成处理参数..." },
  { pct: 85, text: "执行去水印处理..." },
  { pct: 100, text: "处理完成！" },
]

const feats = [
  { title: "智能识别", desc: "AI 自动检测视频角落水印位置", icon: "MagicStick", bg: "linear-gradient(135deg,#dbeafe,#bfdbfe)", color: "#3b82f6" },
  { title: "无损处理", desc: "去除水印的同时保持画质清晰", icon: "Check", bg: "linear-gradient(135deg,#dcfce7,#bbf7d0)", color: "#10b981" },
  { title: "快速处理", desc: "分钟级处理速度，支持批量", icon: "Timer", bg: "linear-gradient(135deg,#fef3c7,#fde68a)", color: "#f59e0b" },
]

function handleBeforeUpload(file){
  const types=["video/mp4","video/avi","video/quicktime","video/x-msvideo","video/x-matroska","video/webm"]
  const ok=types.includes(file.type); const size=file.size/1024/1024<500
  if(!ok) ElMessage.error("不支持的文件格式"); if(!size) ElMessage.error("文件大小不能超过500MB")
  return ok && size
}
async function handleUpload({file}){ submitting.value=true; originalUrl.value=URL.createObjectURL(file); startProcessing() }
async function handleUrlProcess(){
  if(!videoUrl.value.trim()){ElMessage.warning("请输入视频链接");return}
  submitting.value=true; originalUrl.value=videoUrl.value; startProcessing()
}
function startProcessing(){
  processing.value="processing"; progressPercent.value=0; errorMsg.value=""; resultReady.value=false
  let i=0; function next(){
    if(i>=progressSteps.length){processing.value="done";resultReady.value=true;progressText.value="处理完成！";submitting.value=false;return}
    const s=progressSteps[i++]; progressPercent.value=s.pct; progressText.value=s.text; setTimeout(next,1500)
  }
  next()
}
function downloadResult(){ ElMessage.success("下载功能待接入实际视频处理服务") }
function reset(){ videoUrl.value=""; processing.value=null; progressPercent.value=0; errorMsg.value=""; resultReady.value=false; originalUrl.value=""; resultUrl.value=""; submitting.value=false }
</script>

<style scoped>
.watermark-page { min-height: 100vh; display: flex; flex-direction: column; }
.page-container { max-width: 1000px; margin: 0 auto; padding: 48px 24px; width: 100%; flex: 1; }
.page-hero { text-align: center; margin-bottom: 40px; }
.page-title { font-size: 2rem; font-weight: 800; color: var(--primary); margin-bottom: 8px; }
.page-desc { color: var(--text-light); font-size: 1rem; }
.upload-card { margin-bottom: 24px; border-radius: var(--radius-xl); }
.watermark-upload { padding: 48px 0; }
.upload-icon { color: var(--text-light); margin-bottom: 16px; }
.upload-text { color: var(--text); margin-bottom: 4px; font-size: 1.05rem; font-weight: 500; }
.upload-hint { font-size: 0.82rem; color: var(--text-light); }
.or-divider { display:flex; align-items:center; gap:16px; margin:28px 0; color:var(--text-light); font-size:0.85rem; }
.or-divider::before,.or-divider::after { content:''; flex:1; height:1px; background:var(--border); }
.url-input-area { max-width: 500px; margin: 0 auto; }
.progress-card { margin-bottom: 24px; border-radius: var(--radius-xl); }
.progress-header { display:flex; align-items:center; gap:8px; margin-bottom:12px; font-weight:600; }
.spin { animation: spin 1.5s linear infinite; }
.result-card { margin-bottom: 40px; border-radius: var(--radius-xl); }
.result-header { display:flex; justify-content:space-between; align-items:center; font-weight:600; }
.result-actions { display:flex; gap:10px; }
.compare-area { display:flex; align-items:stretch; gap:20px; }
.compare-side { flex:1; }
.compare-label { font-size:0.88rem; color:var(--text-light); margin-bottom:10px; text-align:center; font-weight:500; }
.video-preview { background:var(--bg-dark); border-radius:var(--radius); overflow:hidden; min-height:200px; display:flex; align-items:center; justify-content:center; }
.compare-arrow { display:flex; align-items:center; color:var(--accent); flex-shrink:0; padding:0 4px; }
.features-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; margin-top:48px; }
.feat-item { text-align:center; padding:28px 16px; background:var(--bg-light); border-radius:var(--radius-lg); border:1px solid var(--border); transition:all 0.3s; }
.feat-item:hover { transform:translateY(-4px); box-shadow:var(--shadow-lg); border-color:transparent; }
.feat-icon { width:56px;height:56px;border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 14px; }
.feat-item h4 { font-size:1rem; color:var(--primary); margin-bottom:6px; font-weight:700; }
.feat-item p { font-size:0.82rem; color:var(--text-light); }
@keyframes spin { to { transform:rotate(360deg); } }
@media(max-width:768px){ .compare-area{flex-direction:column} .compare-arrow{justify-content:center;padding:12px 0} }
</style>
