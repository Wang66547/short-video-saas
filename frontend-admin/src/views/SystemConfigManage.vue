<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar"><h2>系统配置</h2></div>
      <el-card shadow="never">
        <el-form :model="configForm" label-width="160px" style="max-width:600px;" label-position="top">
          <el-form-item label="Agnes AI API Base URL">
            <el-input v-model="configForm.agnes_base_url" placeholder="https://api.agnes.ai" size="large" />
          </el-form-item>
          <el-form-item label="Agnes AI API Key">
            <el-input v-model="configForm.agnes_api_key" type="password" show-placeholder placeholder="sk-xxx" size="large" />
          </el-form-item>
          <el-form-item label="Whisper 语音模型">
            <el-select v-model="configForm.whisper_model" style="width:100%;" size="large">
              <el-option label="faster-whisper-small" value="small" />
              <el-option label="faster-whisper-medium" value="medium" />
              <el-option label="faster-whisper-large" value="large" />
            </el-select>
          </el-form-item>
          <el-form-item label="PaddleOCR 启用">
            <el-switch v-model="configForm.ocr_enabled" />
          </el-form-item>
          <el-form-item label="TTS 语音">
            <el-select v-model="configForm.tts_voice" style="width:100%;" size="large">
              <el-option label="温暖女声" value="female_warm" />
              <el-option label="活力男声" value="male_lively" />
              <el-option label="专业播音" value="professional" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :loading="saving" @click="saveConfig">保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>
<script setup>
import { reactive, ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import Sidebar from "@/components/Sidebar.vue"
import { getConfig, updateConfig } from "@/api/admin"

const saving = ref(false)
const configForm = reactive({
  agnes_base_url: "", agnes_api_key: "", whisper_model: "small",
  ocr_enabled: true, tts_voice: "female_warm",
})

async function fetchConfig(){
  try{const res=await getConfig();if(res.code===200){const d=res.data||{};Object.assign(configForm,d)}}catch(e){}
}

async function saveConfig(){
  saving.value=true;try{await updateConfig(configForm);ElMessage.success("保存成功");await fetchConfig()}catch(e){ElMessage.error("保存失败")}finally{saving.value=false}
}

onMounted(fetchConfig)
</script>
<style scoped>
.admin-layout{display:flex;min-height:100vh}.admin-main{flex:1;margin-left:240px;padding:24px;background:var(--admin-bg);min-height:100vh}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.topbar h2{font-size:1.3rem;font-weight:700;color:var(--admin-primary);margin:0}
@media(max-width:768px){.admin-main{margin-left:0}}
</style>
