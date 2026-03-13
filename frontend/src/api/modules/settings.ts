import { http } from '../http'

export interface ShopSettings {
  shop_name: string
  shop_intro: string
  contact_phone: string
  wechat_id: string
  address: string
  business_hours: string
  homepage_banner_urls: string[]
}

export const fetchSettings = async () => {
  const { data } = await http.get<ShopSettings>('/admin/settings')
  return data
}

export const updateSettings = async (payload: ShopSettings) => {
  const { data } = await http.put<ShopSettings>('/admin/settings', payload)
  return data
}
