import { defineStore } from "pinia"
import { ref } from "vue"
import { getPlans, getStatus } from "@/api/membership"

export const useMembershipStore = defineStore("membership", () => {
  const plans = ref([])
  const status = ref(null)
  
  async function loadPlans() {
    const res = await getPlans()
    if (res.code === 200) plans.value = res.data || []
    return res
  }
  
  async function loadStatus() {
    const res = await getStatus()
    if (res.code === 200) status.value = res.data
    return res
  }
  
  return { plans, status, loadPlans, loadStatus }
})
