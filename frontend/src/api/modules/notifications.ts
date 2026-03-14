import { http } from '../http'

export interface NotificationSettings {
  enabled: boolean
  channel: 'wecom' | 'feishu' | 'generic'
  webhook_url: string
  message_prefix: string
  updated_at: string
}

export interface NotificationSendResult {
  success: boolean
  message: string
}

export const fetchNotificationSettings = async () => {
  const { data } = await http.get<NotificationSettings>('/admin/notifications/settings')
  return data
}

export const updateNotificationSettings = async (
  payload: Omit<NotificationSettings, 'updated_at'>,
) => {
  const { data } = await http.put<NotificationSettings>('/admin/notifications/settings', payload)
  return data
}

export const sendTestNotification = async () => {
  const { data } = await http.post<NotificationSendResult>('/admin/notifications/test')
  return data
}

export const sendUnreadSummaryNotification = async () => {
  const { data } = await http.post<NotificationSendResult>('/admin/notifications/unread-summary')
  return data
}
