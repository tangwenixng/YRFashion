<script setup lang="ts">
import { Delete, EditPen, Plus, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchCategories, type CategoryItem } from '../api/modules/categories'
import {
  batchUpdateProductSort,
  batchUpdateProductStatus,
  deleteProduct,
  fetchProducts,
  type ProductItem,
} from '../api/modules/products'

const PAGE_SORT_STEP = 10
const PAGE_SORT_GROUP = 1000
const PRODUCT_TAG_PREVIEW_LIMIT = 2

const router = useRouter()
const loading = ref(false)
const actionLoadingProductId = ref<number | null>(null)
const products = ref<ProductItem[]>([])
const categories = ref<CategoryItem[]>([])
const productsTableRef = ref<{ $el: HTMLElement } | null>(null)
const selectedProductIds = ref<number[]>([])
const dragProductId = ref<number | null>(null)
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

const buildPageSortOrder = (index: number) => (page.value - 1) * PAGE_SORT_GROUP + index * PAGE_SORT_STEP

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
  void router.push('/products/create')
}

const openEdit = (product: ProductItem) => {
  void router.push(`/products/${product.id}/edit`)
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
    const dragTrigger = row.querySelector('.product-main-cell') as HTMLElement | null
    if (!product) {
      return
    }

    row.removeAttribute('draggable')
    if (!dragTrigger) {
      return
    }

    dragTrigger.setAttribute('draggable', 'true')
    dragTrigger.ondragstart = (event) => {
      dragProductId.value = product.id
      event.dataTransfer?.setData('text/plain', String(product.id))
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move'
      }
      row.classList.add('is-row-dragging')
    }
    dragTrigger.ondragend = () => {
      dragProductId.value = null
      rows.forEach((item) => item.classList.remove('is-row-dragging', 'is-row-drag-over'))
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
            批量上架
          </el-button>
          <el-button plain :disabled="!selectedProductIds.length" @click="batchSetStatus('archived')">
            批量下架
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
      <div class="table-tip">拖住商品信息区域可直接调整当前页商品顺序。</div>
      <el-table
        ref="productsTableRef"
        :data="products"
        v-loading="loading"
        table-layout="fixed"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="商品信息" min-width="300">
          <template #default="{ row }">
            <div class="product-main-cell">
              <div class="product-main-heading">
                <strong class="product-main-title">{{ row.name }}</strong>
              </div>
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
                {{ row.status === 'published' ? '下架' : '上架' }}
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
  cursor: grab;
}

.product-main-heading {
  display: flex;
  align-items: center;
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
  max-width: 800px;
  margin: 0 auto;
  padding: 8px 0 4px;
  background: #f7f4ef;
}

.editor-tabs :deep(.el-tabs__header) {
  margin: 0 0 18px;
}

.editor-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.editor-tabs :deep(.el-tabs__nav) {
  gap: 10px;
}

.editor-tabs :deep(.el-tabs__item) {
  height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  color: #8a755d;
  font-weight: 600;
}

.editor-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.editor-tabs :deep(.el-tabs__item.is-active) {
  color: #3d2b1f;
  background: #fff;
  box-shadow: 0 8px 18px rgba(99, 74, 53, 0.08);
}

.editor-section {
  padding: 20px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(99, 74, 53, 0.06);
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
  grid-template-columns: 1fr;
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
  margin-top: 0;
}

.media-subsection {
  padding: 16px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  border-radius: 18px;
  background: #fff;
}

.media-subsection + .media-subsection {
  margin-top: 16px;
}

.editor-media-header,
.image-manager-header,
.image-card-status,
.image-card-actions,
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
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.image-grid-editor {
  align-items: stretch;
}

.image-upload-tile,
.image-thumb-card {
  position: relative;
  min-height: 0;
}

.image-upload-tile :deep(.el-upload) {
  width: 100%;
  height: 100%;
  min-height: 148px;
}

.image-upload-tile-inner,
.image-thumb-card {
  border-radius: 16px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  background: #fffdfa;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.image-upload-tile-inner {
  height: 100%;
  min-height: 148px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #7d5535;
}

.image-upload-tile-inner strong,
.image-upload-tile-inner span {
  display: block;
}

.image-upload-tile-inner strong {
  font-size: 14px;
}

.image-upload-tile-inner span {
  font-size: 12px;
  color: #8a755d;
}

.image-thumb-card {
  overflow: hidden;
}

.image-thumb-card.cover {
  border-color: rgba(169, 127, 78, 0.42);
  box-shadow: 0 12px 24px rgba(117, 86, 53, 0.08);
}

.image-thumb-card.dragging {
  opacity: 0.72;
  transform: scale(0.98);
}

.image-thumb-card.drag-over {
  border-color: rgba(92, 61, 37, 0.34);
  box-shadow: 0 14px 28px rgba(90, 60, 47, 0.12);
}

.image-card-handle {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(50, 33, 22, 0.68);
  color: #fffaf6;
  font-size: 11px;
  cursor: grab;
}

.managed-image {
  width: 100%;
  aspect-ratio: 1 / 1;
  height: auto;
  display: block;
}

.managed-image-thumb {
  cursor: zoom-in;
}

.image-thumb-badges {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.thumb-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(50, 33, 22, 0.7);
  color: #fffaf6;
  font-size: 11px;
  line-height: 1;
}

.thumb-badge-cover {
  background: rgba(193, 137, 78, 0.88);
}

.thumb-badge-new {
  background: rgba(72, 118, 88, 0.84);
}

.image-thumb-toolbar {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.thumb-icon-button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(50, 33, 22, 0.72);
  color: #fffaf6;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.thumb-icon-button:hover {
  transform: translateY(-1px);
}

.thumb-icon-button.active {
  background: rgba(193, 137, 78, 0.92);
}

.thumb-icon-button.danger {
  background: rgba(172, 86, 76, 0.88);
}

.image-summary-meta strong,
.image-summary-meta span {
  display: block;
}

.image-summary-meta strong {
  color: #3a291d;
}

.image-summary-meta span {
  margin-top: 4px;
  color: #8a755d;
  font-size: 12px;
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

:deep(.el-table__body tr.is-row-dragging) .product-main-cell {
  cursor: grabbing;
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
  padding-top: 12px;
  border-top: 1px solid rgba(122, 92, 65, 0.12);
}

.editor-footer-tip {
  line-height: 1.5;
}

.editor-save-button {
  min-width: 128px;
  border: 0;
  background: linear-gradient(135deg, #c68457 0%, #9d5c38 100%);
  box-shadow: 0 12px 24px rgba(157, 92, 56, 0.24);
}

.editor-save-button:hover,
.editor-save-button:focus {
  background: linear-gradient(135deg, #d18f62 0%, #a76440 100%);
}

:deep(.product-editor-dialog) {
  border-radius: 24px;
  overflow: hidden;
}

:deep(.product-editor-dialog .el-dialog) {
  max-width: 800px;
  border-radius: 24px;
  background: #f7f4ef;
}

:deep(.product-editor-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 24px 24px 12px;
  background: #f7f4ef;
}

:deep(.product-editor-dialog .el-dialog__title) {
  font-size: 24px;
  font-weight: 700;
  color: #34241a;
}

:deep(.product-editor-dialog .el-dialog__body) {
  padding: 0 24px 18px;
  background: #f7f4ef;
}

:deep(.product-editor-dialog .el-dialog__footer) {
  padding: 0 24px 24px;
  background: #f7f4ef;
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
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
