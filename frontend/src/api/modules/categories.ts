import { http } from '../http'

export interface CategoryItem {
  id: number
  name: string
  sort_order: number
  status: 'active' | 'disabled'
  product_count: number
  created_at: string
  updated_at: string
}

export interface CategoryPayload {
  name: string
  sort_order?: number
  status?: 'active' | 'disabled'
}

export const fetchCategories = async () => {
  const { data } = await http.get<{ items: CategoryItem[] }>('/admin/categories')
  return data.items
}

export const createCategory = async (payload: CategoryPayload) => {
  const { data } = await http.post<CategoryItem>('/admin/categories', payload)
  return data
}

export const updateCategory = async (id: number, payload: CategoryPayload) => {
  const { data } = await http.put<CategoryItem>(`/admin/categories/${id}`, payload)
  return data
}

export const updateCategorySort = async (id: number, sortOrder: number) => {
  const { data } = await http.put<CategoryItem>(`/admin/categories/${id}/sort`, {
    sort_order: sortOrder,
  })
  return data
}

export const updateCategoryStatus = async (id: number, status: 'active' | 'disabled') => {
  const { data } = await http.put<CategoryItem>(`/admin/categories/${id}/status`, {
    status,
  })
  return data
}
