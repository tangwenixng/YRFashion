import { resolveMediaUrl } from '../base'
import { http } from '../http'

const isTemporaryMiniappFilePath = (url: string) => /^wxfile:\/\//i.test(url) || /^https?:\/\/(tmp|usr)\//i.test(url)

const normalizeMediaUrl = (url: string | null) => {
  if (!url) {
    return null
  }
  if (isTemporaryMiniappFilePath(url)) {
    return null
  }
  return resolveMediaUrl(url)
}

export interface MiniappUserItem {
  id: number
  openid: string
  unionid: string | null
  nickname: string | null
  avatar_url: string | null
  pending_avatar_url: string | null
  avatar_review_status: 'pending' | 'approved' | 'rejected'
  avatar_reject_reason: string | null
  first_visit_at: string
  last_visit_at: string
  created_at: string
}

export interface MiniappUserListParams {
  page?: number
  page_size?: number
  keyword?: string
  avatar_review_status?: 'pending' | 'approved' | 'rejected' | ''
  sort?: 'last_visit_desc' | 'first_visit_desc'
}

export interface MiniappUserListResult {
  items: MiniappUserItem[]
  page: number
  page_size: number
  total: number
}

const normalizeUser = (item: MiniappUserItem) => ({
  ...item,
  avatar_url: normalizeMediaUrl(item.avatar_url),
  pending_avatar_url: normalizeMediaUrl(item.pending_avatar_url),
})

export const fetchMiniappUsers = async (params: MiniappUserListParams = {}) => {
  const { data } = await http.get<MiniappUserListResult>('/admin/users', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      keyword: params.keyword || undefined,
      avatar_review_status: params.avatar_review_status || undefined,
      sort: params.sort ?? 'last_visit_desc',
    },
  })
  return {
    ...data,
    items: data.items.map(normalizeUser),
  }
}

export const approveMiniappUserAvatar = async (id: number) => {
  const { data } = await http.post<MiniappUserItem>(`/admin/users/${id}/avatar/approve`)
  return normalizeUser(data)
}

export const rejectMiniappUserAvatar = async (id: number, reason: string) => {
  const { data } = await http.post<MiniappUserItem>(`/admin/users/${id}/avatar/reject`, {
    reason,
  })
  return normalizeUser(data)
}
