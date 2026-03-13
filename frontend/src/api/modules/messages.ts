import { http } from '../http'

export interface MessageItem {
  id: number
  product_id: number
  product_name: string
  miniapp_user_id: number
  miniapp_user_openid: string
  miniapp_user_nickname: string | null
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
  return data.items
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
