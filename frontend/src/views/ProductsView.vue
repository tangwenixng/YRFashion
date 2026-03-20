<script setup lang="ts">
import { Delete, EditPen, Picture, Plus, RefreshRight, Sort, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, reactive, ref } from 'vue'

import { fetchCategories, type CategoryItem } from '../api/modules/categories'
import {
  batchUpdateProductSort,
  batchUpdateProductStatus,
  createProduct,
  deleteProduct,
  deleteProductImage,
  fetchProducts,
  updateProduct,
  updateProductImageCover,
  updateProductImagesSort,
  type ProductImage,
  type ProductItem,
  uploadProductImage,
} from '../api/modules/products'

type ProductFormState = {
  name: string
  category_id: number | null
  description: string
  tagsText: string
  status: 'draft' | 'published' | 'archived'
  sort_order: number
}

type EditorImageItem = {
  key: string
  id: number | null
  image_url: string
  original_name: string
  sort_order: number
  is_cover: boolean
  source: 'existing' | 'new'
  file: File | null
  object_url: string | null
}

const PAGE_SORT_STEP = 10
const PAGE_SORT_GROUP = 1000
const PRODUCT_TAG_PREVIEW_LIMIT = 2

const loading = ref(false)
const saving = ref(false)
const actionLoadingProductId = ref<number | null>(null)
const products = ref<ProductItem[]>([])
const categories = ref<CategoryItem[]>([])
const productsTableRef = ref<{ $el: HTMLElement } | null>(null)
const editorUploadRef = ref<{ clearFiles: () => void } | null>(null)
const editorVisible = ref(false)
const editingProductId = ref<number | null>(null)
const editorImages = ref<EditorImageItem[]>([])
const removedImageIds = ref<number[]>([])
const imageUploadKey = ref(0)
const selectedProductIds = ref<number[]>([])
const dragProductId = ref<number | null>(null)
const dragImageKey = ref('')
const dragOverImageKey = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filters = reactive({
  keyword: '',
  status: '' as '' | 'draft' | 'published' | 'archived',
  category_id: null as number | null,
})

const hasActiveFilters = computed(() =>
  Boolean(filters.keyword.trim() || filters.status || filters.category_id),
)

const activeFilterSummary = computed(() => {
  const summary: string[] = []

  if (filters.keyword.trim()) {
    summary.push(`关键词：${filters.keyword.trim()}`)
  }

  if (filters.status) {
    summary.push(`状态：${formatStatusLabel(filters.status)}`)
  }

  if (filters.category_id) {
    const currentCategory = categories.value.find((category) => category.id === filters.category_id)
    if (currentCategory) {
      summary.push(`分类：${currentCategory.name}`)
    }
  }

  return summary.length ? summary.join(' / ') : '全部商品'
})

const statusLabelMap: Record<ProductItem['status'], string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

const tagLabelMap: Record<string, string> = {
  featured: '精选',
  spring: '春季',
  daily: '日常',
  winter: '冬季',
  coat: '大衣',
  dress: '连衣裙',
  hidden: '隐藏',
  draft: '草稿',
  mvp: '演示',
  bag: '包袋',
  new: '新品',
  commute: '通勤',
  knitwear: '针织',
  outerwear: '外套',
  set: '套装',
  skirt: '半裙',
}

const form = reactive<ProductFormState>({
  name: '',
  category_id: null,
  description: '',
  tagsText: '',
  status: 'draft',
  sort_order: 0,
})

const buildPageSortOrder = (index: number) => (page.value - 1) * PAGE_SORT_GROUP + index * PAGE_SORT_STEP

const normalizeEditorImages = (nextImages: EditorImageItem[], preferredCoverKey = '') => {
  const fallbackCoverKey =
    nextImages.find((item) => item.key === preferredCoverKey)?.key ||
    nextImages.find((item) => item.is_cover)?.key ||
    nextImages[0]?.key ||
    ''

  editorImages.value = nextImages.map((item, index) => ({
    ...item,
    sort_order: index,
    is_cover: item.key === fallbackCoverKey,
  }))
}

const revokeEditorObjectUrls = () => {
  editorImages.value.forEach((image) => {
    if (image.object_url) {
      URL.revokeObjectURL(image.object_url)
    }
  })
}

const resetEditorImages = () => {
  revokeEditorObjectUrls()
  editorImages.value = []
  removedImageIds.value = []
  dragImageKey.value = ''
  dragOverImageKey.value = ''
  imageUploadKey.value += 1
  editorUploadRef.value?.clearFiles?.()
}

const resetForm = () => {
  editingProductId.value = null
  form.name = ''
  form.category_id = null
  form.description = ''
  form.tagsText = ''
  form.status = 'draft'
  form.sort_order = 0
  resetEditorImages()
}

const toEditorImage = (image: ProductImage): EditorImageItem => ({
  key: `existing-${image.id}`,
  id: image.id,
  image_url: image.image_url,
  original_name: image.original_name,
  sort_order: image.sort_order,
  is_cover: image.is_cover,
  source: 'existing',
  file: null,
  object_url: null,
})

const formatStatusLabel = (status: ProductItem['status']) => statusLabelMap[status] ?? status

const formatTagLabel = (tag: string) => tagLabelMap[tag] ?? tag

const getProductSummary = (product: ProductItem) => {
  const description = product.description.trim().replace(/\s+/g, ' ')
  if (description) {
    return description
  }

  if (product.tags.length) {
    return product.tags.map((tag) => formatTagLabel(tag)).join(' / ')
  }

  return '暂未补充描述'
}

const getVisibleTags = (tags: string[]) => tags.slice(0, PRODUCT_TAG_PREVIEW_LIMIT)

const getHiddenTagCount = (tags: string[]) => Math.max(tags.length - PRODUCT_TAG_PREVIEW_LIMIT, 0)

const loadProducts = async () => {
  loading.value = true
  try {
    const result = await fetchProducts({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword.trim(),
      status: filters.status,
      category_id: filters.category_id,
    })
    products.value = result.items
    total.value = result.total
    await nextTick()
    bindProductRowDrag()
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  categories.value = await fetchCategories()
}

const applyFilters = async () => {
  page.value = 1
  await loadProducts()
}

const resetFilters = async () => {
  filters.keyword = ''
  filters.status = ''
  filters.category_id = null
  page.value = 1
  await loadProducts()
}

const handlePageChange = async (nextPage: number) => {
  page.value = nextPage
  await loadProducts()
}

const handlePageSizeChange = async (nextPageSize: number) => {
  pageSize.value = nextPageSize
  page.value = 1
  await loadProducts()
}

const handleSelectionChange = (selection: ProductItem[]) => {
  selectedProductIds.value = selection.map((item) => item.id)
}

const openCreate = () => {
  resetForm()
  editorVisible.value = true
}

const openEdit = (product: ProductItem) => {
  resetForm()
  editingProductId.value = product.id
  form.name = product.name
  form.category_id = product.category_id
  form.description = product.description
  form.tagsText = product.tags.join(', ')
  form.status = product.status
  form.sort_order = product.sort_order
  normalizeEditorImages(product.images.map(toEditorImage))
  editorVisible.value = true
}

const buildPayload = () => ({
  name: form.name.trim(),
  category_id: form.category_id,
  description: form.description.trim(),
  tags: form.tagsText
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
  status: form.status,
  sort_order: form.sort_order,
})

const handleEditorFileChange = (uploadFile: { raw?: File }) => {
  const rawFile = uploadFile.raw
  if (!rawFile) {
    return
  }

  const objectUrl = URL.createObjectURL(rawFile)
  const nextImages = editorImages.value.concat({
    key: `new-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    id: null,
    image_url: objectUrl,
    original_name: rawFile.name,
    sort_order: editorImages.value.length,
    is_cover: editorImages.value.length === 0,
    source: 'new',
    file: rawFile,
    object_url: objectUrl,
  })
  normalizeEditorImages(nextImages)
}

const setEditorCover = (imageKey: string) => {
  normalizeEditorImages(editorImages.value, imageKey)
}

const removeEditorImage = (imageKey: string) => {
  const target = editorImages.value.find((item) => item.key === imageKey)
  if (!target) {
    return
  }

  if (target.source === 'existing' && target.id) {
    removedImageIds.value.push(target.id)
  }
  if (target.object_url) {
    URL.revokeObjectURL(target.object_url)
  }

  const nextImages = editorImages.value.filter((item) => item.key !== imageKey)
  normalizeEditorImages(nextImages)
}

const handleImageDragStart = (imageKey: string) => {
  dragImageKey.value = imageKey
}

const handleImageDragEnter = (imageKey: string) => {
  if (dragImageKey.value && dragImageKey.value !== imageKey) {
    dragOverImageKey.value = imageKey
  }
}

const handleImageDragEnd = () => {
  dragImageKey.value = ''
  dragOverImageKey.value = ''
}

const handleImageDrop = (targetKey: string) => {
  const sourceKey = dragImageKey.value
  dragImageKey.value = ''
  dragOverImageKey.value = ''

  if (!sourceKey || sourceKey === targetKey) {
    return
  }

  const nextImages = [...editorImages.value]
  const sourceIndex = nextImages.findIndex((item) => item.key === sourceKey)
  const targetIndex = nextImages.findIndex((item) => item.key === targetKey)
  if (sourceIndex === -1 || targetIndex === -1) {
    return
  }

  const [movedImage] = nextImages.splice(sourceIndex, 1)
  nextImages.splice(targetIndex, 0, movedImage)
  normalizeEditorImages(nextImages, movedImage.is_cover ? movedImage.key : '')
}

const saveProduct = async () => {
  if (saving.value) {
    return
  }

  const payload = buildPayload()
  if (!payload.name) {
    ElMessage.warning('商品名称不能为空')
    return
  }

  saving.value = true
  try {
    const savedProduct = editingProductId.value
      ? await updateProduct(editingProductId.value, payload)
      : await createProduct(payload)
    const productId = savedProduct.id

    for (const imageId of removedImageIds.value) {
      await deleteProductImage(productId, imageId)
    }

    const uploadedImageMap = new Map<string, ProductImage>()
    for (const image of editorImages.value) {
      if (image.source !== 'new' || !image.file) {
        continue
      }

      const uploadedImage = await uploadProductImage(productId, image.file, image.sort_order, false)
      uploadedImageMap.set(image.key, uploadedImage)
    }

    const finalSortItems = editorImages.value
      .map((image, index) => {
        const imageId = image.source === 'existing' ? image.id : uploadedImageMap.get(image.key)?.id
        if (!imageId) {
          return null
        }
        return {
          id: imageId,
          sort_order: index,
        }
      })
      .filter((item): item is { id: number; sort_order: number } => item !== null)

    if (finalSortItems.length) {
      await updateProductImagesSort(productId, { items: finalSortItems })
      const coverImage = editorImages.value.find((image) => image.is_cover)
      const coverImageId = coverImage
        ? (coverImage.source === 'existing' ? coverImage.id : uploadedImageMap.get(coverImage.key)?.id) || null
        : null
      if (coverImageId) {
        await updateProductImageCover(productId, coverImageId)
      }
    }

    ElMessage.success(editingProductId.value ? '商品已更新' : '商品已创建')
    editorVisible.value = false
    await loadProducts()
  } finally {
    saving.value = false
  }
}

const toggleProductPublish = async (product: ProductItem) => {
  const nextStatus = product.status === 'published' ? 'draft' : 'published'
  actionLoadingProductId.value = product.id
  try {
    await batchUpdateProductStatus({
      ids: [product.id],
      status: nextStatus,
    })
    ElMessage.success(nextStatus === 'published' ? '商品已发布' : '商品已撤回')
    await loadProducts()
  } finally {
    actionLoadingProductId.value = null
  }
}

const batchSetStatus = async (status: 'published' | 'archived') => {
  if (!selectedProductIds.value.length) {
    ElMessage.warning('请先选择商品')
    return
  }

  await batchUpdateProductStatus({
    ids: selectedProductIds.value,
    status,
  })
  ElMessage.success(status === 'published' ? '已批量发布商品' : '已批量归档商品')
  await loadProducts()
}

const confirmDeleteProduct = async (product: ProductItem) => {
  try {
    await ElMessageBox.confirm(`删除后将同时移除商品图片与关联留言：${product.name}`, '删除商品', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  await deleteProduct(product.id)
  ElMessage.success('商品已删除')

  if (products.value.length === 1 && page.value > 1) {
    page.value -= 1
  }
  await loadProducts()
}

const persistDraggedSort = async (sourceId: number, targetId: number) => {
  if (sourceId === targetId || loading.value) {
    return
  }

  const nextProducts = [...products.value]
  const sourceIndex = nextProducts.findIndex((item) => item.id === sourceId)
  const targetIndex = nextProducts.findIndex((item) => item.id === targetId)
  if (sourceIndex === -1 || targetIndex === -1) {
    return
  }

  const [movedProduct] = nextProducts.splice(sourceIndex, 1)
  nextProducts.splice(targetIndex, 0, movedProduct)

  const sortPayload = {
    items: nextProducts.map((item, index) => ({
      id: item.id,
      sort_order: buildPageSortOrder(index),
    })),
  }

  products.value = nextProducts.map((item, index) => ({
    ...item,
    sort_order: sortPayload.items[index].sort_order,
  }))

  await batchUpdateProductSort(sortPayload)
  ElMessage.success('商品排序已更新')
  await loadProducts()
}

const bindProductRowDrag = () => {
  const tableElement = productsTableRef.value?.$el
  if (!tableElement) {
    return
  }

  const rows = Array.from(tableElement.querySelectorAll('.el-table__body-wrapper tbody tr'))
  rows.forEach((row, index) => {
    const product = products.value[index]
    if (!product) {
      return
    }

    row.setAttribute('draggable', 'true')
    row.ondragstart = (event) => {
      const target = event.target as HTMLElement | null
      if (!target?.closest('.drag-handle')) {
        event.preventDefault()
        return
      }

      dragProductId.value = product.id
      event.dataTransfer?.setData('text/plain', String(product.id))
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move'
      }
      row.classList.add('is-row-dragging')
    }
    row.ondragover = (event) => {
      if (!dragProductId.value || dragProductId.value === product.id) {
        return
      }
      event.preventDefault()
      row.classList.add('is-row-drag-over')
    }
    row.ondragleave = () => {
      row.classList.remove('is-row-drag-over')
    }
    row.ondragend = () => {
      dragProductId.value = null
      rows.forEach((item) => item.classList.remove('is-row-dragging', 'is-row-drag-over'))
    }
    row.ondrop = async (event) => {
      event.preventDefault()
      rows.forEach((item) => item.classList.remove('is-row-drag-over'))
      const sourceId = Number(event.dataTransfer?.getData('text/plain') || dragProductId.value || 0)
      dragProductId.value = null
      row.classList.remove('is-row-dragging')
      if (!sourceId || sourceId === product.id) {
        return
      }
      await persistDraggedSort(sourceId, product.id)
    }
  })
}

const handleEditorClosed = () => {
  resetForm()
}

onBeforeUnmount(() => {
  revokeEditorObjectUrls()
})

void loadProducts()
void loadCategories()
</script>

<template>
  <section class="products-page">
    <div class="page-header">
      <div class="page-heading">
        <h1 class="page-title">商品管理</h1>
        <p class="page-subtitle">商品文案、图片、发布状态和展示顺序都在这里一次性完成。</p>
      </div>

      <div class="header-actions">
        <div class="header-batch-actions">
          <span class="header-selection muted">
            {{ selectedProductIds.length ? `已选 ${selectedProductIds.length} 项` : '未选择商品' }}
          </span>
          <el-button plain :disabled="!selectedProductIds.length" @click="batchSetStatus('published')">
            批量发布
          </el-button>
          <el-button plain :disabled="!selectedProductIds.length" @click="batchSetStatus('archived')">
            批量归档
          </el-button>
        </div>

        <div class="header-main-actions">
          <el-button plain @click="loadProducts">
            <el-icon><RefreshRight /></el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon>
            新增商品
          </el-button>
        </div>
      </div>
    </div>

    <section class="content-card filter-card">
      <div class="filter-grid">
        <el-input
          class="keyword-input"
          v-model="filters.keyword"
          placeholder="按名称、标签或描述搜索"
          clearable
          @keyup.enter="applyFilters"
        />
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-select v-model="filters.category_id" clearable placeholder="全部分类">
          <el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.id" />
        </el-select>
        <div class="filter-actions">
          <el-button type="primary" @click="applyFilters">筛选</el-button>
          <el-button plain @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-summary">
        <span class="muted">共 {{ total }} 条</span>
        <span class="muted">当前筛选：{{ activeFilterSummary }}</span>
        <span v-if="hasActiveFilters" class="filter-summary-indicator">已启用筛选</span>
      </div>
    </section>

    <section class="content-card table-card">
      <div class="table-tip">拖住排序手柄可直接调整当前页商品顺序。</div>
      <el-table
        ref="productsTableRef"
        :data="products"
        v-loading="loading"
        table-layout="fixed"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="排序" width="72">
          <template #default="{ row }">
            <div class="drag-cell">
              <span class="drag-handle" :data-product-id="row.id" title="拖动排序">
                <el-icon><Sort /></el-icon>
              </span>
              <span class="drag-order">{{ row.sort_order }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="商品信息" min-width="300">
          <template #default="{ row }">
            <div class="product-main-cell">
              <strong class="product-main-title">{{ row.name }}</strong>
              <span class="product-main-subtitle" :title="getProductSummary(row)">
                {{ getProductSummary(row) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="112">
          <template #default="{ row }">
            <span class="category-text" :class="{ muted: !row.category_name }">{{ row.category_name || '未分类' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : row.status === 'draft' ? 'warning' : 'info'">
              {{ formatStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="188">
          <template #default="{ row }">
            <div class="tag-list tag-list-compact">
              <el-tag v-for="tag in getVisibleTags(row.tags)" :key="tag" effect="plain" size="small">
                {{ formatTagLabel(tag) }}
              </el-tag>
              <el-tag v-if="getHiddenTagCount(row.tags)" effect="plain" size="small" class="tag-overflow">
                +{{ getHiddenTagCount(row.tags) }}
              </el-tag>
              <span v-if="row.tags.length === 0" class="muted">未设置</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="图片" width="152">
          <template #default="{ row }">
            <div class="image-summary">
              <el-image
                v-if="row.images[0]"
                :src="row.images[0].image_url"
                fit="cover"
                class="cover-thumb"
                :preview-src-list="row.images.map((item: ProductItem['images'][number]) => item.image_url)"
                preview-teleported
              >
                <template #error>
                  <div class="cover-fallback">IMG</div>
                </template>
              </el-image>
              <div class="image-summary-meta" :title="row.images[0]?.original_name || ''">
                <strong>{{ row.images.length ? `${row.images.length} 张` : '暂无图片' }}</strong>
                <span>{{ row.images[0] ? '封面预览' : '进入编辑后上传' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="208" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button text class="action-link" @click="openEdit(row)">
                <el-icon><EditPen /></el-icon>
                编辑
              </el-button>
              <el-button
                text
                class="action-link"
                :loading="actionLoadingProductId === row.id"
                @click="toggleProductPublish(row)"
              >
                {{ row.status === 'published' ? '撤回' : '发布' }}
              </el-button>
              <el-button text class="action-link danger-link" @click="confirmDeleteProduct(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <span class="muted">共 {{ total }} 条</span>
        <el-pagination
          background
          layout="prev, pager, next, sizes"
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </section>

    <el-dialog
      v-model="editorVisible"
      :title="editingProductId ? '编辑商品' : '新增商品'"
      width="980px"
      destroy-on-close
      @closed="handleEditorClosed"
    >
      <div class="editor-grid">
        <el-form label-position="top">
          <section class="editor-section">
            <div class="editor-section-header">
              <div>
                <h3>基础信息</h3>
                <p>先确认标题、描述和分类信息，再继续处理图片与展示顺序。</p>
              </div>
            </div>

            <el-form-item label="商品名称">
              <el-input v-model="form.name" placeholder="例如：羊毛大衣" />
            </el-form-item>

            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入商品描述" />
            </el-form-item>

            <div class="inline-grid">
              <el-form-item label="分类">
                <el-select v-model="form.category_id" clearable placeholder="请选择分类">
                  <el-option
                    v-for="category in categories"
                    :key="category.id"
                    :label="category.status === 'active' ? category.name : `${category.name}（已停用）`"
                    :value="category.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="标签">
                <el-input v-model="form.tagsText" placeholder="用英文逗号分隔，如：通勤, 春季" />
              </el-form-item>
            </div>

            <div class="inline-grid inline-grid-compact">
              <el-form-item label="状态">
                <el-select v-model="form.status">
                  <el-option label="草稿" value="draft" />
                  <el-option label="已发布" value="published" />
                  <el-option label="已归档" value="archived" />
                </el-select>
              </el-form-item>

              <el-form-item label="排序值">
                <div class="sort-field">
                  <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
                  <span class="field-tip">值越小越靠前显示</span>
                </div>
              </el-form-item>
            </div>
          </section>

          <section class="editor-section editor-media-panel">
            <div class="editor-section-header">
              <div>
                <h3>图片管理</h3>
                <p>先上传需要展示的图片，再整理顺序与封面，列表和首页会优先使用封面图。</p>
              </div>
            </div>

            <div class="media-subsection">
              <div class="editor-media-header">
                <div>
                  <h4>上传图片</h4>
                  <p>支持 JPG / PNG / WEBP，单张不超过 5MB。</p>
                </div>
              </div>

              <el-upload
                ref="editorUploadRef"
                :key="imageUploadKey"
                drag
                multiple
                :auto-upload="false"
                :show-file-list="false"
                accept=".jpg,.jpeg,.png,.webp"
                :on-change="handleEditorFileChange"
              >
                <el-icon class="upload-icon"><Picture /></el-icon>
                <div class="el-upload__text">拖拽图片到这里，或点击一次选择多张图片</div>
              </el-upload>
            </div>

            <div v-if="editorImages.length" class="media-subsection image-manager">
              <div class="image-manager-header">
                <div>
                  <h4>图片顺序与封面</h4>
                  <p>拖动卡片调整顺序，封面将用于列表和首页预览。</p>
                </div>
              </div>

              <div class="image-grid">
                <article
                  v-for="image in editorImages"
                  :key="image.key"
                  class="image-card"
                  :class="{
                    cover: image.is_cover,
                    dragging: dragImageKey === image.key,
                    'drag-over': dragOverImageKey === image.key,
                  }"
                  draggable="true"
                  @dragstart="handleImageDragStart(image.key)"
                  @dragenter.prevent="handleImageDragEnter(image.key)"
                  @dragover.prevent
                  @dragend="handleImageDragEnd"
                  @drop.prevent="handleImageDrop(image.key)"
                >
                  <div class="image-card-handle">
                    <el-icon><Sort /></el-icon>
                    <span>{{ image.source === 'new' ? '待上传' : '已上传' }}</span>
                  </div>

                  <el-image
                    :src="image.image_url"
                    fit="cover"
                    class="managed-image"
                    :preview-src-list="editorImages.map((item) => item.image_url)"
                    preview-teleported
                  >
                    <template #error>
                      <div class="cover-fallback">IMG</div>
                    </template>
                  </el-image>

                  <div class="image-card-body">
                    <div class="image-card-status">
                      <strong>{{ image.is_cover ? '当前封面' : `第 ${image.sort_order + 1} 张` }}</strong>
                      <div class="image-card-tags">
                        <el-tag v-if="image.is_cover" type="warning" effect="plain">封面</el-tag>
                        <el-tag v-if="image.source === 'new'" effect="plain">待上传</el-tag>
                      </div>
                    </div>

                    <div class="image-card-meta">
                      <span class="image-file-name" :title="image.original_name">{{ image.original_name }}</span>
                    </div>

                    <div class="image-card-actions">
                      <el-button plain :disabled="image.is_cover" @click="setEditorCover(image.key)">
                        <el-icon><Star /></el-icon>
                        {{ image.is_cover ? '当前封面' : '设为封面' }}
                      </el-button>
                      <el-button plain type="danger" @click="removeEditorImage(image.key)">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-button>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </section>
        </el-form>
      </div>

      <template #footer>
        <div class="editor-footer">
          <span class="muted editor-footer-tip">保存后将同步更新列表展示与封面预览。</span>
          <div class="editor-footer-actions">
            <el-button @click="editorVisible = false">取消</el-button>
            <el-button type="primary" :loading="saving" @click="saveProduct">保存商品</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.products-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-heading {
  min-width: 0;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.header-actions,
.header-batch-actions,
.header-main-actions,
.tag-list,
.image-summary,
.filter-actions,
.pagination-bar,
.row-actions,
.image-card-tags {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.header-actions {
  align-items: flex-start;
  justify-content: flex-end;
  gap: 12px;
}

.header-batch-actions,
.header-main-actions {
  padding: 10px 12px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 16px;
  background: rgba(255, 252, 247, 0.78);
}

.header-selection {
  padding-right: 2px;
  line-height: 32px;
  white-space: nowrap;
}

.tag-list {
  gap: 6px;
}

.tag-list-compact {
  align-items: center;
}

.tag-list :deep(.el-tag) {
  margin: 0;
}

.tag-overflow {
  color: #7d5535;
}

.table-card,
.filter-card {
  padding: 16px;
}

.table-tip {
  margin-bottom: 12px;
  color: #907e6a;
  font-size: 13px;
}

.filter-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(320px, 2.2fr) minmax(160px, 0.9fr) minmax(180px, 1fr) auto;
}

.keyword-input {
  min-width: 0;
}

.filter-actions {
  justify-content: flex-end;
}

.filter-summary {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(122, 92, 65, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-summary-indicator {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(118, 174, 80, 0.14);
  color: #679343;
  font-size: 12px;
  font-weight: 600;
}

.pagination-bar {
  justify-content: space-between;
  margin-top: 16px;
}

.muted {
  color: #907e6a;
  font-size: 13px;
}

.product-main-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.product-main-title,
.product-main-subtitle {
  display: block;
}

.product-main-title {
  color: #3a291d;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.5;
}

.product-main-subtitle {
  color: #8a755d;
  font-size: 13px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-text {
  display: inline-block;
  line-height: 1.5;
}

.editor-grid {
  padding-top: 8px;
}

.editor-section {
  padding: 18px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 20px;
  background: rgba(255, 252, 247, 0.82);
}

.editor-section-header,
.inline-grid {
  display: grid;
}

.editor-section-header {
  gap: 6px;
  margin-bottom: 18px;
}

.editor-section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #3d2b1f;
}

.editor-section-header p {
  margin: 0;
  color: #8a755d;
  font-size: 13px;
  line-height: 1.6;
}

.editor-grid :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.inline-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.inline-grid-compact {
  align-items: start;
}

.sort-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.field-tip {
  color: #907e6a;
  font-size: 12px;
  line-height: 1.5;
}

.editor-media-panel {
  margin-top: 16px;
}

.media-subsection {
  padding: 16px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 18px;
  background: rgba(255, 254, 250, 0.86);
}

.media-subsection + .media-subsection {
  margin-top: 16px;
}

.editor-media-header,
.image-manager-header,
.image-card-status,
.image-card-actions,
.drag-cell,
.image-summary-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.editor-media-header {
  margin-bottom: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.editor-media-header h4,
.image-manager-header h4 {
  margin: 0;
  font-size: 15px;
  color: #3d2b1f;
}

.editor-media-header p,
.image-manager-header p {
  margin: 6px 0 0;
  color: #8a755d;
  font-size: 13px;
  line-height: 1.6;
}

.upload-icon {
  font-size: 28px;
  color: #7d5535;
}

.image-manager-header {
  margin-bottom: 14px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.image-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}

.image-card {
  position: relative;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 252, 247, 0.96);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.image-card.cover {
  border-color: rgba(169, 127, 78, 0.42);
  box-shadow: 0 12px 24px rgba(117, 86, 53, 0.08);
}

.image-card.dragging {
  opacity: 0.72;
  transform: scale(0.98);
}

.image-card.drag-over {
  border-color: rgba(92, 61, 37, 0.34);
  box-shadow: 0 14px 28px rgba(90, 60, 47, 0.12);
}

.image-card-handle {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(50, 33, 22, 0.68);
  color: #fffaf6;
  font-size: 12px;
  cursor: grab;
}

.managed-image {
  width: 100%;
  height: 220px;
  display: block;
}

.image-card-body {
  padding: 14px;
}

.image-card-status strong,
.image-card-meta span,
.image-summary-meta strong,
.image-summary-meta span {
  display: block;
}

.image-card-status strong,
.image-summary-meta strong {
  color: #3a291d;
}

.image-card-meta span,
.image-summary-meta span {
  margin-top: 6px;
  color: #8a755d;
  font-size: 13px;
}

.image-card-status {
  align-items: flex-start;
}

.image-card-meta {
  min-width: 0;
}

.image-file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-card-tags {
  gap: 8px;
  justify-content: flex-end;
}

.image-card-actions {
  margin-top: 14px;
  justify-content: space-between;
  flex-wrap: nowrap;
}

.cover-thumb {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(122, 92, 65, 0.12);
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(164, 124, 89, 0.18), rgba(107, 73, 45, 0.24));
  color: #5c3d25;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.image-summary {
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
}

.image-summary :deep(.el-image) {
  flex-shrink: 0;
}

.image-summary-meta {
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  min-width: 0;
}

.drag-cell {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(122, 92, 65, 0.1);
  color: #6f5240;
  cursor: grab;
}

.drag-order {
  font-size: 12px;
  color: #907e6a;
}

.row-actions {
  justify-content: flex-end;
  gap: 14px;
  flex-wrap: nowrap;
}

.action-link {
  margin: 0;
  min-width: 0;
  padding: 6px;
  border-radius: 8px;
  font-weight: 500;
}

.action-link :deep(span) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.action-link :deep(.el-icon) {
  font-size: 16px;
}

.danger-link {
  color: var(--el-color-danger);
}

.editor-footer,
.editor-footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-footer {
  width: 100%;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid rgba(122, 92, 65, 0.12);
}

.editor-footer-tip {
  line-height: 1.5;
}

:deep(.el-table__body-wrapper tbody tr.is-row-dragging td) {
  background: rgba(247, 239, 231, 0.92);
}

:deep(.el-table__body-wrapper tbody tr.is-row-drag-over td) {
  background: rgba(242, 230, 217, 0.72);
}

@media (max-width: 1100px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .image-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    justify-content: stretch;
  }

  .header-batch-actions,
  .header-main-actions {
    width: 100%;
    justify-content: space-between;
  }

  .inline-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .editor-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-footer-actions {
    justify-content: flex-end;
  }

  .pagination-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
