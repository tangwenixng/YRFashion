import { http } from '../http'

export interface DashboardSummary {
  unread_message_count: number
  product_count: number
  miniapp_user_count: number
  notification_enabled: boolean
  notification_channel: string | null
}

export const fetchDashboardSummary = async () => {
  const { data } = await http.get<DashboardSummary>('/admin/dashboard/summary')
  return data
}
