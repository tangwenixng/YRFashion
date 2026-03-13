import { http } from '../http'

export interface DashboardSummary {
  unread_message_count: number
  product_count: number
  miniapp_user_count: number
}

export const fetchDashboardSummary = async () => {
  const { data } = await http.get<DashboardSummary>('/admin/dashboard/summary')
  return data
}
