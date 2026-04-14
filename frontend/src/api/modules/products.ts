import { resolveMediaUrl } from '../base'
import { http } from '../http'

export interface ProductImage {
  id: number
  image_url: string
  thumbnail_url?: string | null
  raw_image_url?: string
  raw_thumbnail_url?: string | null
  original_name: string
  sort_order: number
  is_cover: boolean
  created_at: string
}

export interface ProductItem {
  id: number
  name: string
  category_id: number | null
  category_name: string | null
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

export interface ProductImageSortPayload {
  items: Array<{
    id: number
    sort_order: number
  }>
}

export interface ProductBatchStatusPayload {
  ids: number[]
  status: 'draft' | 'published' | 'archived'
}

export interface ProductBatchSortPayload {
  items: Array<{
    id: number
    sort_order: number
  }>
}

export interface ProductListParams {
  page?: number
  page_size?: number
  keyword?: string
  status?: 'draft' | 'published' | 'archived' | ''
  category_id?: number | null
}

export interface ProductListResult {
  items: ProductItem[]
  page: number
  page_size: number
  total: number
}

const normalizeProductImage = (image: ProductImage): ProductImage => ({
  ...image,
  raw_image_url: image.raw_image_url ?? image.image_url,
  raw_thumbnail_url: image.raw_thumbnail_url ?? image.thumbnail_url ?? null,
  image_url: resolveMediaUrl(image.image_url) || image.image_url,
  thumbnail_url: resolveMediaUrl(image.thumbnail_url ?? null),
})

const normalizeProduct = (product: ProductItem): ProductItem => ({
  ...product,
  images: product.images.map(normalizeProductImage),
})

export const fetchProducts = async (params: ProductListParams = {}) => {
  const { data } = await http.get<ProductListResult>('/admin/products', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      keyword: params.keyword || undefined,
      status: params.status || undefined,
      category_id: params.category_id || undefined,
    },
  })
  return {
    ...data,
    items: data.items.map(normalizeProduct),
  }
}

export const fetchProduct = async (id: number) => {
  const { data } = await http.get<ProductItem>(`/admin/products/${id}`)
  return normalizeProduct(data)
}

export const createProduct = async (payload: ProductPayload) => {
  const { data } = await http.post<ProductItem>('/admin/products', payload)
  return normalizeProduct(data)
}

export const updateProduct = async (id: number, payload: ProductPayload) => {
  const { data } = await http.put<ProductItem>(`/admin/products/${id}`, payload)
  return normalizeProduct(data)
}

export const deleteProduct = async (id: number) => {
  await http.delete(`/admin/products/${id}`)
}

export const batchUpdateProductStatus = async (payload: ProductBatchStatusPayload) => {
  const { data } = await http.post<ProductListResult>('/admin/products/batch-status', payload)
  return {
    ...data,
    items: data.items.map(normalizeProduct),
  }
}

export const batchUpdateProductSort = async (payload: ProductBatchSortPayload) => {
  const { data } = await http.put<ProductListResult>('/admin/products/batch-sort', payload)
  return {
    ...data,
    items: data.items.map(normalizeProduct),
  }
}

export const updateProductSort = async (id: number, sortOrder: number) => {
  const { data } = await http.put<ProductItem>(`/admin/products/${id}/sort`, {
    sort_order: sortOrder,
  })
  return normalizeProduct(data)
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
  return normalizeProductImage(data)
}

export const updateProductImageCover = async (productId: number, imageId: number) => {
  const { data } = await http.post<ProductItem>(`/admin/products/${productId}/images/${imageId}/cover`)
  return normalizeProduct(data)
}

export const updateProductImagesSort = async (
  productId: number,
  payload: ProductImageSortPayload,
) => {
  const { data } = await http.put<ProductItem>(`/admin/products/${productId}/images/sort`, payload)
  return normalizeProduct(data)
}

export const deleteProductImage = async (productId: number, imageId: number) => {
  const { data } = await http.delete<ProductItem>(`/admin/products/${productId}/images/${imageId}`)
  return normalizeProduct(data)
}
