<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-particles">
        <div class="particle p1"></div>
        <div class="particle p2"></div>
        <div class="particle p3"></div>
      </div>
      <div class="hero-inner">
        <div class="hero-content animate-fade-in-up">
          <div class="hero-badge">
            <el-icon><Star /></el-icon> AI 驱动的智能创作平台
          </div>
          <h1 class="hero-title">一键复刻<br/><span class="hero-title-accent">爆款短视频</span></h1>
          <p class="hero-desc">AI 智能解析 · 精准拆解脚本分镜 · 一键生成同款视频</p>
          <div class="hero-actions">
            <router-link to="/video/create" v-if="userStore.isLoggedIn">
              <el-button type="primary" size="large" class="hero-btn hero-btn-primary">
                <el-icon><VideoCamera /></el-icon> 立即创作
              </el-button>
            </router-link>
            <router-link to="/register" v-else>
              <el-button type="primary" size="large" class="hero-btn hero-btn-primary">
                <el-icon><VideoCamera /></el-icon> 免费开始
              </el-button>
            </router-link>
            <el-button size="large" class="hero-btn hero-btn-secondary" @click="scrollToPlans">
              查看套餐
            </el-button>
          </div>
          <div class="hero-stats">
            <div class="stat-item" v-for="s in stats" :key="s.label">
              <span class="stat-num gradient-text">{{ s.value }}</span>
              <span class="stat-label">{{ s.label }}</span>
            </div>
          </div>
        </div>
        <div class="hero-visual animate-scale-in">
          <div class="visual-card">
            <div class="visual-screen">
              <div class="screen-glow"></div>
              <div class="screen-content">
                <div class="mock-play"><el-icon :size="40"><VideoPlay /></el-icon></div>
                <p class="mock-text">AI 智能解析中...</p>
              </div>
            </div>
            <div class="visual-tags">
              <span class="tag" v-for="t in ['语音转写','分镜拆解','字幕识别','BGM 提取']" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Feature Cards -->
    <section class="features">
      <div class="container">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">全方位 AI 赋能，让创作更高效</p>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :lg="6" v-for="(f, i) in features" :key="i">
            <div class="feature-card" :style="{ animationDelay: i * 0.1 + 's' }">
              <div class="feature-icon" :style="{ background: f.color }">
                <el-icon :size="28"><component :is="f.icon" /></el-icon>
              </div>
              <h3>{{ f.title }}</h3>
              <p>{{ f.desc }}</p>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- Tool Entry -->
    <section class="tools">
      <div class="container">
        <h2 class="section-title">快捷入口</h2>
        <p class="section-subtitle">选择你想要使用的功能</p>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :lg="8">
            <router-link to="/video/create" class="tool-card tool-card-blue">
              <div class="tool-icon-wrap" style="background: linear-gradient(135deg, #dbeafe, #bfdbfe);">
                <el-icon :size="40" color="#3b82f6"><Upload /></el-icon>
              </div>
              <h3>视频解析</h3>
              <p>上传或粘贴链接，智能拆解文案、分镜、BGM</p>
              <el-button type="primary" round size="small" class="tool-btn">去解析</el-button>
            </router-link>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <router-link to="/video/create" class="tool-card tool-card-purple">
              <div class="tool-icon-wrap" style="background: linear-gradient(135deg, #ede9fe, #ddd6fe);">
                <el-icon :size="40" color="#8b5cf6"><MagicStick /></el-icon>
              </div>
              <h3>AI 创作</h3>
              <p>基于解析结果，AI 一键生成同款视频</p>
              <el-button type="primary" round size="small" class="tool-btn tool-btn-purple">去创作</el-button>
            </router-link>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <router-link to="/watermark" class="tool-card tool-card-green">
              <div class="tool-icon-wrap" style="background: linear-gradient(135deg, #dcfce7, #bbf7d0);">
                <el-icon :size="40" color="#10b981"><CircleCloseFilled /></el-icon>
              </div>
              <h3>去水印</h3>
              <p>智能识别并去除视频角落水印</p>
              <el-button type="primary" round size="small" class="tool-btn tool-btn-green">去处理</el-button>
            </router-link>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- Pricing -->
    <section class="pricing" id="plans">
      <div class="container">
        <h2 class="section-title">选择你的套餐</h2>
        <p class="section-subtitle">免费试用，随时升级</p>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :lg="6" v-for="plan in plans" :key="plan.id">
            <div class="price-card" :class="{ popular: plan.plan_type === 'premium' }">
              <div class="price-header">
                <h3>{{ plan.name }}</h3>
                <p class="price-type">{{ planTypePeriod(plan.plan_type) }}有效</p>
              </div>
              <div class="price-amount">
                <span class="price-currency">￥</span>
                <span class="price-value">{{ plan.price }}</span>
              </div>
              <ul class="price-features">
                <li v-for="(feat, fi) in plan.features" :key="fi">
                  <el-icon color="#10b981"><Check /></el-icon> {{ feat }}
                </li>
              </ul>
              <el-button :type="plan.plan_type === 'premium' ? 'primary' : 'default'" round class="price-btn"
                :disabled="plan.price === 0" @click="plan.price > 0 ? router.push('/membership') : null">
                {{ plan.price === 0 ? '当前套餐' : '立即开通' }}
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="container">
        <h2>准备好开始创作了吗？</h2>
        <p>加入万千创作者，一起打造爆款短视频</p>
        <router-link to="/register">
          <el-button type="primary" size="large" class="cta-btn">
            免费注册，立即体验
          </el-button>
        </router-link>
      </div>
    </section>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useUserStore } from "@/stores/user"
import { getPlans } from "@/api/membership"
import Footer from "@/components/Footer.vue"
import {
  VideoCamera, Upload, MagicStick, CircleCloseFilled,
  Headset, Connection, DataAnalysis, Brush, Check, VideoPlay, Star
} from "@element-plus/icons-vue"

const router = useRouter()
const userStore = useUserStore()
const plans = ref([])

const features = [
  { icon: "Headset", title: "语音转写", desc: "faster-whisper 高精度语音识别，带时间戳完整文案", color: "linear-gradient(135deg, #3b82f6, #2563eb)" },
  { icon: "Connection", title: "分镜拆解", desc: "帧差法精准定位镜头切换，自动输出分镜脚本", color: "linear-gradient(135deg, #8b5cf6, #7c3aed)" },
  { icon: "DataAnalysis", title: "OCR 字幕", desc: "PaddleOCR 识别画面内嵌字幕，智能合并到文案", color: "linear-gradient(135deg, #10b981, #059669)" },
  { icon: "Brush", title: "BGM 提取", desc: "人声分离技术，一键提取背景音乐", color: "linear-gradient(135deg, #f59e0b, #d97706)" },
]

const stats = [
  { value: "10万+", label: "用户信赖" },
  { value: "50万+", label: "视频解析" },
  { value: "99.9%", label: "成功率" },
]

function planTypePeriod(type) {
  const map = { monthly: "月", quarterly: "季", yearly: "年", lifetime: "终身" }
  return map[type] || ""
}

async function loadPlans() {
  try {
    const res = await getPlans()
    if (res.code === 200) {
      const raw = res.data || []
      plans.value = raw.map((p, i) => ({
        ...p,
        features: [
          `每日 ${p.daily_parse_count} 次解析`,
          `每日 ${p.daily_generate_count} 次生成`,
          p.support_hd_export ? "支持高清导出" : "标准画质",
          p.plan_type === 'lifetime' ? '永久有效' : `${planTypePeriod(p.plan_type)}有效`,
        ],
      }))
    }
  } catch (e) {}
}

function scrollToPlans() {
  document.getElementById("plans")?.scrollIntoView({ behavior: "smooth" })
}

onMounted(loadPlans)
</script>

<style scoped>
.home-page { min-height: 100vh; display: flex; flex-direction: column; }

/* Hero */
.hero {
  background: var(--gradient-hero);
  background-size: 200% 200%;
  animation: gradientShift 12s ease infinite;
  padding: 80px 0 70px;
  color: #fff;
  position: relative;
  overflow: hidden;
}
.hero-particles { position: absolute; inset: 0; overflow: hidden; }
.particle {
  position: absolute; border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  animation: float 6s ease-in-out infinite;
}
.p1 { width: 400px; height: 400px; top: -100px; right: -80px; animation-delay: 0s; }
.p2 { width: 250px; height: 250px; bottom: -60px; left: -60px; animation-delay: 2s; }
.p3 { width: 180px; height: 180px; top: 40%; left: 55%; animation-delay: 4s; }
.hero-inner {
  max-width: 1200px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; gap: 60px;
  position: relative; z-index: 1;
}
.hero-content { flex: 1; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 0.8rem; color: rgba(255, 255, 255, 0.8);
  margin-bottom: 20px;
}
.hero-title {
  font-size: 3rem; font-weight: 800; line-height: 1.15;
  margin-bottom: 16px;
}
.hero-title-accent {
  background: linear-gradient(90deg, #60a5fa, #a78bfa, #60a5fa);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradientShift 4s linear infinite;
}
.hero-desc {
  font-size: 1.1rem; color: rgba(255,255,255,0.6);
  margin-bottom: 36px; line-height: 1.7;
}
.hero-actions { display: flex; gap: 16px; margin-bottom: 48px; flex-wrap: wrap; }
.hero-btn {
  min-width: 150px; height: 50px; font-size: 1rem; font-weight: 600;
}
.hero-btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important;
}
.hero-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.5) !important;
}
.hero-btn-secondary {
  border-color: rgba(255,255,255,0.25) !important;
  color: #fff !important;
  background: transparent !important;
}
.hero-btn-secondary:hover {
  border-color: #fff !important;
  background: rgba(255,255,255,0.08) !important;
}
.hero-stats { display: flex; gap: 48px; }
.stat-item { text-align: center; }
.stat-num { display: block; font-size: 1.6rem; font-weight: 700; }
.stat-label { font-size: 0.85rem; color: rgba(255,255,255,0.45); }

/* Hero Visual */
.hero-visual { flex-shrink: 0; }
.visual-card {
  background: rgba(255,255,255,0.06);
  border-radius: 24px;
  padding: 28px;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.visual-screen {
  background: rgba(0,0,0,0.25);
  border-radius: 16px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.screen-glow {
  position: absolute; width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(59,130,246,0.3), transparent 70%);
  filter: blur(20px);
}
.screen-content { position: relative; z-index: 1; text-align: center; }
.mock-play { color: rgba(255,255,255,0.7); margin-bottom: 12px; }
.mock-text { color: rgba(255,255,255,0.4); font-size: 0.9rem; }
.visual-tags { display: flex; gap: 8px; margin-top: 18px; flex-wrap: wrap; }
.tag {
  padding: 5px 14px;
  background: rgba(59,130,246,0.2);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: var(--radius-full);
  font-size: 0.78rem; color: #93c5fd;
}

/* Sections */
.features, .tools, .pricing { padding: 88px 0; }
.features { background: var(--bg); }
.tools { background: var(--bg-light); }
.pricing { background: var(--bg); }
.section-title {
  font-size: 2rem; font-weight: 800; color: var(--primary);
  text-align: center; margin-bottom: 8px;
}
.section-subtitle {
  text-align: center; color: var(--text-light);
  font-size: 1rem; margin-bottom: 48px;
}

/* Feature Cards */
.feature-card {
  text-align: center; padding: 36px 20px;
  border-radius: var(--radius-lg);
  background: var(--bg-light);
  border: 1px solid var(--border);
  transition: all 0.3s;
}
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: transparent;
}
.feature-icon {
  width: 64px; height: 64px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px; color: #fff;
}
.feature-card h3 { font-size: 1.05rem; color: var(--primary); margin-bottom: 8px; font-weight: 700; }
.feature-card p { font-size: 0.85rem; color: var(--text-light); line-height: 1.6; }

/* Tool Cards */
.tool-card {
  display: block; background: var(--bg);
  border-radius: var(--radius-xl);
  padding: 40px 28px; text-align: center;
  transition: all 0.35s;
  border: 1px solid var(--border);
  height: 100%; position: relative; overflow: hidden;
}
.tool-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  opacity: 0; transition: opacity 0.3s;
}
.tool-card:hover::before { opacity: 1; }
.tool-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-xl);
}
.tool-card-blue:hover { border-color: #3b82f6; }
.tool-card-purple:hover { border-color: #8b5cf6; }
.tool-card-green:hover { border-color: #10b981; }
.tool-icon-wrap {
  width: 72px; height: 72px; border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px;
}
.tool-card h3 { font-size: 1.2rem; color: var(--primary); margin: 16px 0 8px; font-weight: 700; }
.tool-card p { font-size: 0.85rem; color: var(--text-light); margin-bottom: 24px; }
.tool-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  box-shadow: 0 2px 8px rgba(59,130,246,0.25) !important;
}
.tool-btn-purple {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  box-shadow: 0 2px 8px rgba(139,92,246,0.25) !important;
}
.tool-btn-green {
  background: linear-gradient(135deg, #10b981, #059669) !important;
  box-shadow: 0 2px 8px rgba(16,185,129,0.25) !important;
}

/* Price Cards */
.price-card {
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 36px 24px;
  text-align: center;
  transition: all 0.3s;
  height: 100%;
  position: relative;
}
.price-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
.price-card.popular {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6, 0 8px 30px rgba(59,130,246,0.12);
}
.price-header { margin-bottom: 20px; }
.price-header h3 { font-size: 1.15rem; font-weight: 700; color: var(--primary); }
.price-type { font-size: 0.8rem; color: var(--text-light); margin-top: 2px; }
.price-amount { margin-bottom: 24px; }
.price-currency { font-size: 1.2rem; font-weight: 600; color: var(--text-secondary); }
.price-value { font-size: 2.4rem; font-weight: 800; color: var(--primary); }
.price-features { list-style: none; text-align: left; margin-bottom: 28px; }
.price-features li {
  padding: 8px 0; font-size: 0.88rem; color: var(--text);
  display: flex; align-items: center; gap: 8px;
}
.price-btn { width: 100%; height: 46px; font-size: 0.95rem; font-weight: 600; }

/* CTA */
.cta-section {
  background: var(--gradient-hero);
  background-size: 200% 200%;
  animation: gradientShift 8s ease infinite;
  color: #fff; text-align: center;
  padding: 80px 24px;
}
.cta-section h2 { font-size: 2.2rem; font-weight: 800; margin-bottom: 12px; }
.cta-section p { color: rgba(255,255,255,0.6); margin-bottom: 36px; font-size: 1.05rem; }
.cta-btn {
  background: rgba(255,255,255,0.1) !important; color: #fff !important;
  border: 1px solid rgba(255,255,255,0.2) !important;
  font-weight: 700; font-size: 1.05rem; height: 52px; padding: 0 40px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  &:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.3); background: rgba(255,255,255,0.15) !important; }
}

@media (max-width: 768px) {
  .hero-inner { flex-direction: column; text-align: center; gap: 32px; }
  .hero-title { font-size: 2rem; }
  .hero-actions { justify-content: center; }
  .hero-stats { justify-content: center; gap: 24px; }
  .hero-visual { width: 100%; }
  .section-title { font-size: 1.5rem; }
  .cta-section h2 { font-size: 1.5rem; }
}
</style>
