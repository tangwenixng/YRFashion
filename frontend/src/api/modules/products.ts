import { http } from '../http'

export interface ProductImage {
  id: number
  image_url: string
  original_name: string
  sort_order: number
  is_cover: boolean
  created_at: string
}

export interface ProductItem {
  id: number
  name: string
  category_id: number | null
  description: string
  tags: string[]
  status: 'draft' | 'published' | 'archived'
  sort_order: number
  created_at: string
  updated_at: string
  images: ProductImage[]
}

export interface ProductPayload {
  name: string
  category_id: number | null
  description: string
  tags: string[]
  status: 'draft' | 'published' | 'archived'
  sort_order?: number
}

export const fetchProducts = async () => {
  const { data } = await http.get<{ items: ProductItem[] }>('/admin/products')
  return data.items
}

export const createProduct = async (payload: ProductPayload) => {
  const { data } = await http.post<ProductItem>('/admin/products', payload)
  return data
}

export const updateProduct = async (id: number, payload: ProductPayload) => {
  const { data } = await http.put<ProductItem>(`/admin/products/${id}`, payload)
  return data
}

export const updateProductSort = async (id: number, sortOrder: number) => {
  const { data } = await http.put<ProductItem>(`/admin/products/${id}/sort`, {
    sort_order: sortOrder,
  })
  return data
}

export const uploadProductImage = async (
  id: number,
  file: File,
  sortOrder = 0,
  isCover = false,
) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('sort_order', String(sortOrder))
  formData.append('is_cover', String(isCover))

  const { data } = await http.post<ProductImage>(`/admin/products/${id}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}
