import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", redirect: "/admin/dashboard" },
  { path: "/login", name: "AdminLogin", component: () => import("@/views/Login.vue") },
  { path: "/admin/dashboard", name: "AdminDashboard", component: () => import("@/views/Dashboard.vue"), meta: { requiresAuth: true } },
  { path: "/admin/users", name: "UserManage", component: () => import("@/views/UserManage.vue"), meta: { requiresAuth: true } },
  { path: "/admin/orders", name: "OrderManage", component: () => import("@/views/OrderManage.vue"), meta: { requiresAuth: true } },
  { path: "/admin/plans", name: "MembershipManage", component: () => import("@/views/MembershipManage.vue"), meta: { requiresAuth: true } },
  { path: "/admin/cards", name: "CardKeyManage", component: () => import("@/views/CardKeyManage.vue"), meta: { requiresAuth: true } },
  { path: "/admin/videos", name: "VideoManage", component: () => import("@/views/VideoManage.vue"), meta: { requiresAuth: true } },
  { path: "/admin/configs", name: "SystemConfigManage", component: () => import("@/views/SystemConfigManage.vue"), meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", redirect: "/admin/dashboard" },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("admin_token")
  if (to.meta.requiresAuth && !token) {
    next({ path: "/login", query: { redirect: to.fullPath } })
  } else if (to.name === "AdminLogin" && token) {
    next("/admin/dashboard")
  } else {
    next()
  }
})

export default router