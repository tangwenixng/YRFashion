import { http } from '../http'

export interface MiniappUserItem {
  id: number
  openid: string
  unionid: string | null
  nickname: string | null
  avatar_url: string | null
  first_visit_at: string
  last_visit_at: string
  created_at: string
}

export const fetchMiniappUsers = async () => {
  const { data } = await http.get<{ items: MiniappUserItem[] }>('/admin/users')
  return data.items
}
