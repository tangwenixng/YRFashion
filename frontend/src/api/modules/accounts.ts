import { http } from '../http'

export interface AdminAccountItem {
  id: number
  username: string
  display_name: string
  status: 'active' | 'disabled'
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface AdminAccountPayload {
  username: string
  display_name: string
  password: string
  status?: 'active' | 'disabled'
}

export interface AdminAccountUpdatePayload {
  display_name?: string
  status?: 'active' | 'disabled'
}

export const fetchAdminAccounts = async () => {
  const { data } = await http.get<{ items: AdminAccountItem[] }>('/admin/accounts')
  return data.items
}

export const createAdminAccount = async (payload: AdminAccountPayload) => {
  const { data } = await http.post<AdminAccountItem>('/admin/accounts', payload)
  return data
}

export const updateAdminAccount = async (id: number, payload: AdminAccountUpdatePayload) => {
  const { data } = await http.patch<AdminAccountItem>(`/admin/accounts/${id}`, payload)
  return data
}

export const resetAdminAccountPassword = async (id: number, newPassword: string) => {
  const { data } = await http.post<AdminAccountItem>(`/admin/accounts/${id}/reset-password`, {
    new_password: newPassword,
  })
  return data
}
