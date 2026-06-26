import api from "./index"

// 创建订单
export function createOrder(data) {
  return api.post("/payments/create-order", data)
}

// 微信支付预下单
export function wechatPrepay(order_no) {
  return api.post("/payments/wechat/prepay", null, { params: { order_no } })
}

// 支付宝预下单
export function alipayPrepay(order_no) {
  return api.post("/payments/alipay/prepay", null, { params: { order_no } })
}

// 获取订单列表
export function listOrders(page = 1) {
  return api.get("/payments/orders", { params: { page } })
}

// 获取订单详情
export function getOrderDetail(order_no) {
  return api.get("/payments/detail", { params: { order_no } })
}

// 卡密兑换
export function redeemCardKey(key_code) {
  return api.post("/card-keys/redeem", { key_code })
}

// 获取套餐列表
export function getPlans() {
  return api.get("/membership/plans")
}

// 获取会员状态
export function getMembershipStatus() {
  return api.get("/membership/status")
}
