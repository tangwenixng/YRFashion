import { http } from '../http'

export interface AdminLoginPayload {
  username: string
  password: string
}

export interface AdminTokenResponse {
  access_token: string
  token_type: string
}

export interface AdminProfile {
  id: number
  username: string
  display_name: string
}

export interface AdminChangePasswordPayload {
  current_password: string
  new_password: string
}

export const loginAdmin = async (payload: AdminLoginPayload) => {
  const { data } = await http.post<AdminTokenResponse>('/admin/auth/login', payload)
  return data
}

export const fetchAdminProfile = async () => {
  const { data } = await http.get<AdminProfile>('/admin/auth/me')
  return data
}

export const changeAdminPassword = async (payload: AdminChangePasswordPayload) => {
  await http.post('/admin/auth/change-password', payload)
}
