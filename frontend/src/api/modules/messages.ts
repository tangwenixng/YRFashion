import { http } from '../http'

const configuredBaseURL = (import.meta.env.VITE_API_BASE_URL || '/api').trim()
const mediaBaseURL = configuredBaseURL.replace(/\/$/, '').replace(/\/api$/, '')

const normalizeMediaUrl = (url: string | null) => {
  if (!url) {
    return null
  }
  if (/^https?:\/\//.test(url)) {
    return url
  }
  if (url.startsWith('/')) {
    return `${mediaBaseURL}${url}`
  }
  return `${mediaBaseURL}/${url}`
}

export interface MessageItem {
  id: number
  product_id: number
  product_name: string
  miniapp_user_id: number
  miniapp_user_openid: string
  miniapp_user_nickname: string | null
  miniapp_user_avatar_url: string | null
  content: string
  status: 'unread' | 'read' | 'replied'
  reply_content: string | null
  reply_at: string | null
  read_at: string | null
  created_at: string
}

export const fetchMessages = async (status?: string) => {
  const { data } = await http.get<{ items: MessageItem[] }>('/admin/messages', {
    params: status ? { status } : undefined,
  })
  return data.items.map((item) => ({
    ...item,
    miniapp_user_avatar_url: normalizeMediaUrl(item.miniapp_user_avatar_url),
  }))
}

export const markMessageRead = async (id: number) => {
  const { data } = await http.post<MessageItem>(`/admin/messages/${id}/read`)
  return data
}

export const markMessageUnread = async (id: number) => {
  const { data } = await http.post<MessageItem>(`/admin/messages/${id}/unread`)
  return data
}

export const replyMessage = async (id: number, replyContent: string) => {
  const { data } = await http.post<MessageItem>(`/admin/messages/${id}/reply`, {
    reply_content: replyContent,
  })
  return data
}
