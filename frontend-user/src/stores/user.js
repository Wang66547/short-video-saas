import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { login as loginApi, getMe } from "@/api/auth"

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "")
  const refreshToken = ref(localStorage.getItem("refresh_token") || "")
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const membershipType = computed(() => userInfo.value?.membership_level || "free")
  const isMember = computed(() => {
    if (!userInfo.value) return false
    return userInfo.value.membership_level !== "free"
  })
  const remainingCredits = computed(() => userInfo.value?.remaining_credits ?? 0)

  async function login(credentials) {
    const res = await loginApi(credentials)
    const data = res.data || res
    const accessToken = data.access_token || data.token
    const refresh = data.refresh_token || data.refreshToken
    if (accessToken) {
      token.value = accessToken
      refreshToken.value = refresh || ""
      localStorage.setItem("token", accessToken)
      localStorage.setItem("refresh_token", refresh || "")
      await fetchUserInfo()
    }
    return res
  }

  async function fetchUserInfo() {
    try {
      const res = await getMe()
      userInfo.value = res.data || res
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ""
    refreshToken.value = ""
    userInfo.value = null
    localStorage.removeItem("token")
    localStorage.removeItem("refresh_token")
  }

  return {
    token, refreshToken, userInfo,
    isLoggedIn, membershipType, isMember, remainingCredits,
    login, fetchUserInfo, logout,
  }
})