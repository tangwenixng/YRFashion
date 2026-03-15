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

export interface MiniappUserListParams {
  page?: number
  page_size?: number
  keyword?: string
  sort?: 'last_visit_desc' | 'first_visit_desc'
}

export interface MiniappUserListResult {
  items: MiniappUserItem[]
  page: number
  page_size: number
  total: number
}

export const fetchMiniappUsers = async (params: MiniappUserListParams = {}) => {
  const { data } = await http.get<MiniappUserListResult>('/admin/users', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      keyword: params.keyword || undefined,
      sort: params.sort ?? 'last_visit_desc',
    },
  })
  return data
}
