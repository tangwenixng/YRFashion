import { http } from '../http'

const configuredBaseURL = (import.meta.env.VITE_API_BASE_URL || '/api').trim()
const mediaBaseURL = configuredBaseURL.replace(/\/$/, '').replace(/\/api$/, '')

const isTemporaryMiniappFilePath = (url: string) => /^wxfile:\/\//i.test(url) || /^https?:\/\/(tmp|usr)\//i.test(url)

const normalizeMediaUrl = (url: string | null) => {
  if (!url) {
    return null
  }
  if (isTemporaryMiniappFilePath(url)) {
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

export interface MessageListParams {
  page?: number
  page_size?: number
  status?: string
  product_id?: number | null
}

export interface MessageListResult {
  items: MessageItem[]
  page: number
  page_size: number
  total: number
}

const normalizeMessage = (item: MessageItem) => ({
  ...item,
  miniapp_user_avatar_url: normalizeMediaUrl(item.miniapp_user_avatar_url),
})

export const fetchMessages = async (params: MessageListParams = {}) => {
  const { data } = await http.get<MessageListResult>('/admin/messages', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      status: params.status || undefined,
      product_id: params.product_id || undefined,
    },
  })
  return {
    ...data,
    items: data.items.map(normalizeMessage),
  }
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
  return normalizeMessage(data)
}

export const batchMarkMessageRead = async (ids: number[]) => {
  const { data } = await http.post<MessageListResult>('/admin/messages/batch-read', { ids })
  return {
    ...data,
    items: data.items.map(normalizeMessage),
  }
}
