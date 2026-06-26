<template>
  <div class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-icon">
        <svg viewBox="0 0 32 32" width="32" height="32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#sLogo)"/>
          <defs><linearGradient id="sLogo" x1="0" y1="0" x2="32" y2="32"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
          <path d="M11 10l12 6-12 6V10z" fill="#fff"/>
        </svg>
      </div>
      <span class="logo-text">管理后台</span>
    </div>

    <el-menu :default-active="activeMenu" router text-color="#94a3b8" active-text-color="#fff" background-color="#0f172a" class="sidebar-menu">
      <el-menu-item index="/admin/dashboard">
        <el-icon><DataAnalysis /></el-icon><span>数据概览</span>
      </el-menu-item>
      <el-sub-menu index="_user">
        <template #title><el-icon><User /></el-icon><span>用户管理</span></template>
        <el-menu-item index="/admin/users">用户列表</el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="_order">
        <template #title><el-icon><Document /></el-icon><span>订单管理</span></template>
        <el-menu-item index="/admin/orders">订单列表</el-menu-item>
      </el-sub-menu>
      <el-menu-item index="/admin/plans">
        <el-icon><CreditCard /></el-icon><span>套餐管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/cards">
        <el-icon><Key /></el-icon><span>卡密管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/videos">
        <el-icon><Monitor /></el-icon><span>视频任务</span>
      </el-menu-item>
      <el-menu-item index="/admin/configs">
        <el-icon><Setting /></el-icon><span>系统配置</span>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <el-avatar :size="32" style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);">A</el-avatar>
        <span class="sidebar-user-name">Admin</span>
      </div>
      <el-button link type="danger" size="small" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon> 退出
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAdminStore } from "@/stores/admin"
import { DataAnalysis, User, Document, CreditCard, Key, Monitor, Setting, SwitchButton } from "@element-plus/icons-vue"

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()
const activeMenu = computed(() => route.path)

function handleLogout() { adminStore.clear(); router.push("/login") }
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #071526 100%);
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 12px rgba(0,0,0,0.15);
}
.sidebar-logo {
  display: flex; align-items: center; gap: 12px;
  padding: 22px 22px 18px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3);
  overflow: hidden; flex-shrink: 0;
}
.logo-text { color: #fff; font-size: 1.15rem; font-weight: 700; letter-spacing: 1px; }
.sidebar-menu { border-right: none; flex: 1; padding: 10px 0; }
.sidebar-menu:not(.el-menu--collapse) { width: 240px; }
.sidebar-menu .el-menu-item,
.sidebar-menu .el-sub-menu__title {
  border-radius: 8px; margin: 3px 10px; height: 44px; line-height: 44px; font-size: 0.9rem;
}
.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover { background: rgba(255,255,255,0.06); }
.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3);
}
.sidebar-footer {
  padding: 16px; border-top: 1px solid rgba(255,255,255,0.06);
  display: flex; align-items: center; justify-content: space-between;
}
.sidebar-user { display: flex; align-items: center; gap: 8px; }
.sidebar-user-name { color: #94a3b8; font-size: 0.85rem; }
</style>
