import { createRouter, createWebHistory } from "vue-router"
import { useUserStore } from "@/stores/user"

const routes = [
  { path: "/", redirect: "/dashboard" },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { title: "登录", guest: true },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/Login.vue"),
    meta: { title: "注册", guest: true },
  },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("@/views/Dashboard.vue"),
    meta: { title: "工作台" },
  },
  {
    path: "/video/create",
    name: "VideoCreate",
    component: () => import("@/views/VideoCreate.vue"),
    meta: { title: "创作视频", requiresAuth: true },
  },
  {
    path: "/video/list",
    name: "VideoList",
    component: () => import("@/views/VideoList.vue"),
    meta: { title: "复刻工作台", requiresAuth: true },
  },
  {
    path: "/watermark",
    name: "WatermarkRemove",
    component: () => import("@/views/WatermarkRemove.vue"),
    meta: { title: "去水印工具" },
  },
  {
    path: "/membership",
    name: "Membership",
    component: () => import("@/views/Membership.vue"),
    meta: { title: "会员中心", requiresAuth: true },
  },
  {
    path: "/orders",
    name: "Orders",
    component: () => import("@/views/OrderHistory.vue"),
    meta: { title: "订单记录", requiresAuth: true },
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("@/views/Profile.vue"),
    meta: { title: "个人中心", requiresAuth: true },
  },
  { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 短视频复刻` : "短视频复刻平台"

  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ path: "/login", query: { redirect: to.fullPath } })
  } else if (to.meta.guest && userStore.isLoggedIn) {
    next("/dashboard")
  } else {
    next()
  }
})

export default router