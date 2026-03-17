import { http } from '../http'

export interface ShopSettings {
  shop_name: string
  shop_intro: string
  contact_phone: string
  wechat_id: string
  address: string
  business_hours: string
  homepage_banner_urls: string[]
  has_unpublished_changes: boolean
  draft_updated_at: string | null
  published_at: string | null
}

export const fetchSettings = async () => {
  const { data } = await http.get<ShopSettings>('/admin/settings')
  return data
}

export interface ShopSettingsPayload {
  shop_name: string
  shop_intro: string
  contact_phone: string
  wechat_id: string
  address: string
  business_hours: string
  homepage_banner_urls: string[]
}

export const updateSettings = async (payload: ShopSettingsPayload) => {
  const { data } = await http.put<ShopSettings>('/admin/settings', payload)
  return data
}

export const publishSettings = async () => {
  const { data } = await http.post<ShopSettings>('/admin/settings/publish')
  return data
}
