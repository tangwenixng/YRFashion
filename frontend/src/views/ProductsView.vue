<script setup lang="ts">
import { CollectionTag, Delete, Download, EditPen, Plus, RefreshRight, Search, Upload } from '@element-plus/icons-vue'
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

const confirmBatchDelete = async () => {
  if (!selectedProductIds.value.length) {
    ElMessage.warning('请先选择商品')
    return
  }

  try {
    await ElMessageBox.confirm(
      `删除后将同时移除已选 ${selectedProductIds.value.length} 个商品的图片与关联留言，是否继续？`,
      '批量删除商品',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  await Promise.all(selectedProductIds.value.map((productId) => deleteProduct(productId)))
  ElMessage.success('已批量删除商品')

  if (selectedProductIds.value.length >= products.value.length && page.value > 1) {
    page.value -= 1
  }
  selectedProductIds.value = []
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
    <section class="content-card control-panel">
      <div class="control-panel-top">
        <div class="control-panel-overview">
          <div class="control-panel-icon">
            <el-icon><CollectionTag /></el-icon>
          </div>
          <div class="control-panel-copy">
            <strong>商品控制中心</strong>
            <p>当前共 <span class="control-panel-count">{{ total }}</span> 条商品</p>
          </div>
        </div>

        <el-button type="primary" class="create-product-button" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增商品
        </el-button>
      </div>

      <div class="control-panel-middle" :class="{ 'is-selection-mode': selectedProductIds.length }">
        <p v-if="!selectedProductIds.length" class="control-panel-helper">先筛选或选择商品，再进行批量处理或新增。</p>
        <div class="control-panel-middle-actions" :class="{ 'is-selection-mode': selectedProductIds.length }">
          <div v-if="selectedProductIds.length" class="selection-toolbar">
            <span class="selection-pill">已选择 {{ selectedProductIds.length }} 项</span>
            <el-button plain class="selection-action-button" @click="batchSetStatus('published')">
              <el-icon><Upload /></el-icon>
              批量上架
            </el-button>
            <el-button plain class="selection-action-button" @click="batchSetStatus('archived')">
              <el-icon><Download /></el-icon>
              批量下架
            </el-button>
            <el-button plain class="selection-action-button selection-action-button-danger" @click="confirmBatchDelete">
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
          </div>

          <el-button plain circle class="refresh-circle-button" @click="loadProducts">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="control-panel-bottom">
        <div class="filter-grid">
          <el-input
            class="keyword-input"
            v-model="filters.keyword"
            placeholder="搜名称、标签或描述搜索"
            clearable
            @keyup.enter="applyFilters"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
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
          <span class="muted">共 {{ total }} 条结果 · 当前筛选：{{ activeFilterSummary }}</span>
          <span v-if="hasActiveFilters" class="filter-summary-indicator">已启用筛选</span>
        </div>
      </div>
    </section>

    <section class="content-card table-card">
      <el-table
        ref="productsTableRef"
        :data="products"
        v-loading="loading"
        table-layout="fixed"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="商品信息" min-width="360">
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
        <el-table-column label="分类" width="104">
          <template #default="{ row }">
            <span class="category-text" :class="{ muted: !row.category_name }">{{ row.category_name || '未分类' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="112">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : row.status === 'draft' ? 'warning' : 'info'">
              {{ formatStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="176">
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
        <el-table-column label="图片" width="136">
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
                  <div class="cover-fallback" />
                </template>
              </el-image>
              <div class="image-summary-meta" :title="row.images[0]?.original_name || ''">
                <strong>{{ row.images.length ? `${row.images.length} 张` : '暂无图片' }}</strong>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="196" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button text class="action-icon-button" @click="openEdit(row)">
                <el-icon><EditPen /></el-icon>
              </el-button>
              <el-button
                text
                class="action-status-button"
                :loading="actionLoadingProductId === row.id"
                @click="toggleProductPublish(row)"
              >
                {{ row.status === 'published' ? '下架' : '上架' }}
              </el-button>
              <el-button text class="action-icon-button action-icon-button-danger" @click="confirmDeleteProduct(row)">
                <el-icon><Delete /></el-icon>
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

.control-panel {
  padding: 0;
  overflow: hidden;
  border-color: rgba(194, 204, 219, 0.76);
  box-shadow: 0 18px 45px rgba(145, 154, 168, 0.12);
}

.control-panel-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 28px 18px;
  background:
    radial-gradient(circle at 22% 10%, rgba(74, 144, 226, 0.12), transparent 30%),
    linear-gradient(180deg, rgba(246, 249, 255, 0.96), rgba(255, 255, 255, 0.92));
}

.control-panel-overview {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 18px;
}

.control-panel-icon {
  width: 58px;
  height: 58px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: linear-gradient(180deg, #3e8cff, #2f73f6);
  color: #fff;
  box-shadow: 0 12px 24px rgba(48, 115, 246, 0.24);
}

.control-panel-icon :deep(.el-icon) {
  font-size: 26px;
}

.control-panel-copy {
  min-width: 0;
}

.control-panel-copy strong {
  display: block;
  color: #1f2f46;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.control-panel-copy p {
  margin: 4px 0 0;
  color: #70809a;
  font-size: 14px;
  line-height: 1.5;
}

.control-panel-count {
  color: #2f73f6;
  font-weight: 700;
}

.create-product-button {
  min-width: 164px;
  height: 52px;
  padding: 0 22px;
  border: 0;
  border-radius: 18px;
  background: linear-gradient(180deg, #3e8cff, #2f73f6);
  box-shadow: 0 10px 24px rgba(48, 115, 246, 0.24);
  font-size: 15px;
  font-weight: 600;
}

.create-product-button:hover,
.create-product-button:focus {
  background: linear-gradient(180deg, #4b95ff, #397cf8);
}

.control-panel-middle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 28px;
  border-top: 1px solid rgba(207, 215, 228, 0.78);
  background: linear-gradient(180deg, rgba(248, 250, 254, 0.98), rgba(245, 248, 252, 0.94));
}

.control-panel-helper {
  margin: 0;
  color: #6f7f98;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
}

.control-panel-middle-actions {
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.selection-toolbar,
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

.selection-toolbar {
  gap: 14px;
  padding: 0;
  border: 0;
  background: transparent;
}

.selection-pill {
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  background: rgba(47, 115, 246, 0.12);
  color: #2f73f6;
  font-weight: 700;
  white-space: nowrap;
}

.selection-action-button {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border-color: rgba(207, 215, 228, 0.96);
  color: #2d3950;
  font-weight: 600;
}

.selection-action-button :deep(.el-icon) {
  margin-right: 6px;
  font-size: 15px;
}

.selection-action-button-danger {
  color: #f04438;
  border-color: rgba(251, 189, 180, 0.96);
  background: rgba(255, 246, 245, 0.98);
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
  color: #2f73f6;
}

.table-card,
.control-panel-bottom {
  padding: 16px 28px;
}

.table-card {
  overflow: hidden;
  border-color: rgba(194, 204, 219, 0.76);
  box-shadow: 0 18px 45px rgba(145, 154, 168, 0.1);
  background:
    radial-gradient(circle at 18% 0%, rgba(74, 144, 226, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(246, 249, 255, 0.95), rgba(255, 255, 255, 0.92));
}

.control-panel-bottom {
  border-top: 1px solid rgba(207, 215, 228, 0.78);
  background: rgba(255, 255, 255, 0.9);
}

.filter-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(360px, 2.6fr) minmax(180px, 0.95fr) minmax(180px, 0.95fr) auto;
}

.keyword-input {
  min-width: 0;
}

.keyword-input :deep(.el-input__wrapper),
.filter-grid :deep(.el-select__wrapper) {
  min-height: 52px;
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px rgba(199, 208, 222, 0.92);
}

.filter-actions {
  justify-content: flex-end;
  flex-wrap: nowrap;
}

.filter-actions :deep(.el-button) {
  min-width: 100px;
  height: 52px;
  border-radius: 16px;
  font-weight: 600;
}

.filter-summary {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(215, 222, 233, 0.82);
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
  margin-top: 14px;
  padding-top: 8px;
}

:deep(.el-table) {
  background: transparent;
  color: #2d3950;
}

:deep(.el-table th.el-table__cell) {
  background: transparent;
  padding: 16px 0;
  border-bottom: 1px solid rgba(221, 227, 236, 0.96);
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table td.el-table__cell) {
  padding: 18px 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.92);
}

:deep(.el-table .cell) {
  color: inherit;
}

:deep(.el-table th.el-table__cell .cell) {
  color: #44556d;
  font-size: 13px;
  font-weight: 700;
}

:deep(.el-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background: rgba(247, 250, 255, 0.9);
}

:deep(.el-tag) {
  border-radius: 9px;
  font-weight: 600;
}

:deep(.el-tag--success) {
  background: rgba(223, 247, 229, 0.98);
  border-color: transparent;
  color: #169b5f;
}

:deep(.tag-list-compact .el-tag--info),
:deep(.tag-list-compact .el-tag--primary),
:deep(.tag-list-compact .el-tag) {
  background: rgba(241, 246, 255, 0.98);
  border-color: rgba(181, 203, 255, 0.96);
  color: #2d72f4;
}

:deep(.el-pagination.is-background .btn-next),
:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .el-pager li) {
  min-width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(245, 248, 252, 0.98);
  color: #6f8199;
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(180deg, #3e8cff, #2f73f6);
  color: #fff;
  box-shadow: 0 8px 16px rgba(48, 115, 246, 0.2);
}

:deep(.el-pagination .el-select .el-select__wrapper) {
  min-height: 42px;
  border-radius: 14px;
  background: rgba(248, 250, 253, 0.98);
  box-shadow: inset 0 0 0 1px rgba(199, 208, 222, 0.92);
}

.muted {
  color: #64758e;
  font-size: 13px;
}

.product-main-cell {
  display: flex;
  flex-direction: column;
  gap: 5px;
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
  color: #1f2f46;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
}

.product-main-subtitle {
  color: #6d7d96;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.category-text {
  display: inline-block;
  line-height: 1.5;
  color: #44556d;
}

.refresh-circle-button {
  width: 42px;
  height: 42px;
  margin-left: auto;
  border: 0;
  background: rgba(250, 252, 255, 0.98);
  color: #556781;
  box-shadow: none;
}

.control-panel-middle.is-selection-mode .control-panel-middle-actions {
  justify-content: flex-start;
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

.image-summary-meta strong {
  display: block;
  color: #4d5e77;
  font-size: 16px;
  font-weight: 600;
  line-height: 1;
}

.cover-thumb {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(217, 222, 229, 0.92);
  background: #f5f7fa;
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  background:
    linear-gradient(135deg, rgba(229, 233, 240, 0.92), rgba(244, 246, 249, 0.98)),
    #f5f7fa;
}

.image-summary {
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
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
  gap: 8px;
  flex-wrap: nowrap;
}

.action-icon-button,
.action-status-button {
  margin: 0;
  min-width: 0;
  padding: 0;
}

.action-icon-button {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  color: #2f73f6;
}

.action-icon-button-danger {
  color: #ff4d4f;
}

.action-status-button {
  padding: 0 16px;
  height: 36px;
  border-radius: 14px;
  background: rgba(244, 246, 249, 0.98);
  color: #2d3950;
  font-weight: 500;
}

:deep(.action-status-button.is-loading) {
  background: rgba(236, 242, 250, 0.98);
}

:deep(.el-table__body tr.is-row-dragging) .product-main-cell {
  cursor: grabbing;
}

.action-icon-button :deep(span),
.action-status-button :deep(span) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.action-icon-button :deep(.el-icon) {
  font-size: 16px;
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
  .control-panel-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .create-product-button {
    width: 100%;
  }

  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .image-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .control-panel-middle {
    flex-direction: column;
    align-items: stretch;
  }

  .control-panel-middle-actions {
    width: 100%;
    justify-content: space-between;
  }

  .selection-toolbar {
    width: 100%;
    justify-content: space-between;
  }

  .create-product-button,
  .control-panel-top,
  .control-panel-middle,
  .control-panel-bottom {
    padding: 16px;
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
