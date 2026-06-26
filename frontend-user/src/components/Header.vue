<template>
  <header class="site-header" :class="{ 'header-scrolled': scrolled }">
    <div class="header-inner">
      <router-link to="/dashboard" class="logo">
        <div class="logo-icon-wrap">
          <svg viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#logoGrad)"/>
            <defs><linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
            <path d="M12 10l10 6-10 6V10z" fill="#fff"/>
          </svg>
        </div>
        <span class="logo-text">短视频复刻</span>
      </router-link>
      <nav class="desktop-nav">
        <router-link to="/dashboard" class="nav-link" active-class="active" v-for="item in navItems" :key="item.to" :to="item.to">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown @command="handleCommand" placement="bottom-end">
            <div class="user-avatar">
              <el-avatar :size="36" :src="userStore.userInfo?.avatar || ''" class="avatar-ring">{{ userStore.userInfo?.nickname?.charAt(0) || userStore.userInfo?.phone?.slice(-2) || 'U' }}</el-avatar>
              <span class="user-name">{{ userStore.userInfo?.nickname || '用户' }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown-menu">
                <el-dropdown-item command="profile"><el-icon><User /></el-icon> 个人中心</el-dropdown-item>
                <el-dropdown-item command="orders"><el-icon><Document /></el-icon> 我的订单</el-dropdown-item>
                <el-dropdown-item command="membership"><el-icon><CreditCard /></el-icon> 会员权益</el-dropdown-item>
                <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <router-link to="/login" class="login-btn-wrap">
            <el-button type="primary" round class="login-btn">登录</el-button>
          </router-link>
        </template>
        <el-button class="mobile-menu-btn" link @click="menuOpen = !menuOpen"><el-icon><Menu /></el-icon></el-button>
      </div>
    </div>
    <transition name="slide-down">
      <div v-if="menuOpen" class="mobile-menu">
        <router-link to="/dashboard" class="mobile-nav-link" @click="menuOpen = false">工作台</router-link>
        <router-link to="/video/create" class="mobile-nav-link" @click="menuOpen = false">创作视频</router-link>
        <router-link to="/video/list" class="mobile-nav-link" @click="menuOpen = false">我的视频</router-link>
        <router-link to="/watermark" class="mobile-nav-link" @click="menuOpen = false">去水印</router-link>
        <router-link to="/membership" class="mobile-nav-link mobile-highlight" @click="menuOpen = false"><el-icon><Star /></el-icon> 会员中心</router-link>
        <div class="mobile-divider" />
        <router-link to="/profile" class="mobile-nav-link" @click="menuOpen = false">个人中心</router-link>
        <router-link to="/orders" class="mobile-nav-link" @click="menuOpen = false">我的订单</router-link>
        <el-button v-if="!userStore.isLoggedIn" type="primary" round class="mobile-login-btn" @click="menuOpen = false">登录 / 注册</el-button>
      </div>
    </transition>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue"
import { useRouter, useRoute } from "vue-router"
import { ElMessage } from "element-plus"
import { User, Document, CreditCard, SwitchButton, Menu, ArrowDown, Star, VideoCamera, MagicStick, CircleCloseFilled } from "@element-plus/icons-vue"
import { useUserStore } from "@/stores/user"

const router = useRouter()
const userStore = useUserStore()
const menuOpen = ref(false)
const scrolled = ref(false)

const navItems = computed(() => [
  { label: "工作台", to: "/dashboard", icon: "VideoCamera" },
  { label: "创作视频", to: "/video/create", icon: "MagicStick" },
  { label: "我的视频", to: "/video/list", icon: "Document" },
  { label: "去水印", to: "/watermark", icon: "CircleCloseFilled" },
])

function handleCommand(cmd) {
  if (cmd === "profile") router.push("/profile")
  else if (cmd === "orders") router.push("/orders")
  else if (cmd === "membership") router.push("/membership")
  else if (cmd === "logout") { userStore.logout(); ElMessage.success("已退出登录"); router.push("/login") }
}

function onScroll() { scrolled.value = window.scrollY > 10 }
onMounted(() => window.addEventListener("scroll", onScroll))
onUnmounted(() => window.removeEventListener("scroll", onScroll))
</script>

<style scoped>
.site-header {
  position: sticky; top: 0; z-index: 1000;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.header-scrolled {
  background: rgba(15, 23, 42, 0.95);
  box-shadow: 0 1px 12px rgba(0, 0, 0, 0.3);
}
.header-inner {
  max-width: 1280px; margin: 0 auto;
  display: flex; align-items: center;
  height: 68px; padding: 0 24px;
}
.logo {
  display: flex; align-items: center; gap: 10px;
  font-weight: 700; font-size: 1.2rem; color: var(--primary);
  transition: all 0.2s;
}
.logo:hover { transform: scale(1.02); }
.logo-icon-wrap {
  width: 36px; height: 36px; border-radius: 10px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}
.logo-text {
  white-space: nowrap;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.desktop-nav {
  flex: 1; display: flex; align-items: center;
  gap: 4px; margin-left: 40px;
}
.nav-link {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: var(--radius);
  font-size: 0.9rem; color: var(--text-secondary);
  transition: all 0.2s; font-weight: 500;
}
.nav-link:hover { color: var(--primary); background: var(--accent-glow); }
.nav-link.active {
  color: var(--accent); background: var(--accent-glow); font-weight: 600;
}
.header-right { display: flex; align-items: center; gap: 12px; }
.login-btn-wrap { display: inline-block; }
.login-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25) !important;
  font-weight: 600; padding: 8px 24px !important;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35) !important; }
.user-avatar {
  display: flex; align-items: center; gap: 8px;
  cursor: pointer; padding: 4px 10px 4px 4px;
  border-radius: var(--radius-full); transition: all 0.2s;
}
.user-avatar:hover { background: var(--bg-light); }
.avatar-ring { box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15); }
.user-name { font-size: 0.9rem; color: var(--text); font-weight: 500; }
.arrow-icon { font-size: 0.7rem; color: var(--text-light); transition: all 0.2s; }
.user-avatar:hover .arrow-icon { color: var(--accent); }
.mobile-menu-btn { display: none; }
.user-dropdown-menu {
  border-radius: var(--radius-lg) !important; border: 1px solid var(--border-light) !important;
  box-shadow: var(--shadow-lg) !important; padding: 8px !important; min-width: 180px !important;
}
.mobile-menu {
  position: absolute; top: 68px; left: 0; right: 0;
  background: rgba(30, 41, 59, 0.98);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-lg); padding: 8px 0; z-index: 999;
}
.mobile-nav-link {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 24px; font-size: 1rem; color: var(--text);
  transition: all 0.2s; font-weight: 500;
}
.mobile-nav-link:hover { background: var(--accent-glow); color: var(--accent); }
.mobile-highlight { color: var(--accent); font-weight: 600; }
.mobile-divider { height: 1px; background: var(--border); margin: 4px 0; }
.mobile-login-btn { margin: 8px 24px; width: calc(100% - 48px); font-weight: 600; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.25s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
@media (max-width: 1024px) {
  .desktop-nav { display: none; }
  .user-name { display: none; }
  .mobile-menu-btn { display: inline-flex; }
  .header-inner { padding: 0 16px; }
}
</style>