import api from "./index"

// 更新个人资料
export function updateProfile(data) {
  return api.put("/auth/profile", data)
}

// 修改密码
export function changePassword(data) {
  return api.put("/users/password", null, { params: data })
}
