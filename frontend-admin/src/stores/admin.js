import { defineStore } from "pinia"
import { ref, computed } from "vue"

export const useAdminStore = defineStore("admin", () => {
  const token = ref(localStorage.getItem("admin_token") || "")
  const stats = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t) {
    token.value = t
    if (t) localStorage.setItem("admin_token", t)
    else localStorage.removeItem("admin_token")
  }

  function clear() {
    token.value = ""
    stats.value = null
    localStorage.removeItem("admin_token")
  }

  return { token, stats, isLoggedIn, setToken, clear }
})