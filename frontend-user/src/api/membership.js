import api from "./index"

// 获取套餐列表
export function getPlans() {
  return api.get("/membership/plans")
}

// 卡密兑换
export function redeem(key_code) {
  return api.post("/membership/redeem", { key_code })
}

// 获取会员状态
export function getStatus() {
  return api.get("/membership/status")
}
