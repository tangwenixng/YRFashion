<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { batchUpdateProductStatus, deleteProduct, fetchProducts, type ProductItem } from '../../api/modules/products'

const router = useRouter()
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const products = ref<ProductItem[]>([])
const filters = reactive({
  keyword: '',
  status: 'published' as '' | 'draft' | 'published' | 'archived',
})

const statusTabs = [
  { label: '已发布', value: 'published' },
  { label: '草稿', value: 'draft' },
  { label: '归档', value: 'archived' },
  { label: '全部', value: '' },
] as const

const hasMore = computed(() => page.value * pageSize.value < total.value)
const statusSummary = computed(() => {
  if (filters.status === 'draft') return '当前查看草稿商品'
  if (filters.status === 'archived') return '当前查看归档商品'
  if (filters.status === '') return '当前查看全部商品'
  return '当前查看已发布商品'
})

const loadProducts = async () => {
  loading.value = true
  try {
    const result = await fetchProducts({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword.trim(),
      status: filters.status,
    })
    products.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  page.value = 1
  await loadProducts()
}

const togglePublish = async (product: ProductItem) => {
  const nextStatus = product.status === 'published' ? 'draft' : 'published'
  await batchUpdateProductStatus({ ids: [product.id], status: nextStatus })
  ElMessage.success(nextStatus === 'published' ? '商品已发布' : '商品已撤回')
  await loadProducts()
}

const removeProduct = async (product: ProductItem) => {
  try {
    await ElMessageBox.confirm(`确认删除商品：${product.name}？`, '删除商品', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  await deleteProduct(product.id)
  ElMessage.success('商品已删除')
  await loadProducts()
}

const formatStatusLabel = (status: ProductItem['status']) => {
  if (status === 'draft') return '草稿'
  if (status === 'archived') return '归档'
  return '已发布'
}

const openProductEdit = (productId: number) => {
  void router.push(`/m/products/${productId}/edit`)
}

const openProductImages = (productId: number) => {
  void router.push(`/m/products/${productId}/images`)
}

onMounted(() => {
  void loadProducts()
})
</script>

<template>
  <section class="mobile-page">
    <article class="mobile-card mobile-panel hero-filter-card">
      <div class="hero-filter-head">
        <div>
          <span class="section-kicker">商品管理</span>
          <h2 class="mobile-section-title">筛选、编辑与发布都留在一屏内</h2>
          <p class="mobile-muted">{{ statusSummary }} · 共 {{ total }} 条</p>
        </div>
        <button class="mobile-action-button hero-create-button" type="button" @click="router.push('/m/products/create')">
          新增商品
        </button>
      </div>

      <div class="filter-stack">
        <el-input v-model="filters.keyword" clearable placeholder="搜索商品名称 / 标签" @keyup.enter="applyFilters" />
        <div class="status-chips">
          <button
            v-for="tab in statusTabs"
            :key="tab.value || 'all'"
            class="status-chip"
            :class="{ active: filters.status === tab.value }"
            type="button"
            @click="filters.status = tab.value; applyFilters()"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
    </article>

    <section class="product-list" v-loading="loading">
      <article v-for="product in products" :key="product.id" class="mobile-card product-card">
        <div class="product-card-main">
          <div class="cover-wrap">
            <img
              v-if="product.images[0]?.thumbnail_url || product.images[0]?.image_url"
              class="product-cover"
              :src="product.images[0]?.thumbnail_url || product.images[0]?.image_url || ''"
              alt=""
            />
            <div v-else class="product-cover product-cover-fallback">暂无封面</div>
            <span class="cover-status-badge">{{ formatStatusLabel(product.status) }}</span>
          </div>

          <div class="product-copy">
            <strong>{{ product.name }}</strong>
            <p class="product-meta">{{ product.category_name || '未分类' }} · 排序 {{ product.sort_order }}</p>
            <p class="product-summary">{{ product.description || '暂未填写描述，可进入编辑页完善。' }}</p>
            <div v-if="product.tags.length" class="tag-row">
              <span v-for="tag in product.tags.slice(0, 3)" :key="tag" class="tag-pill">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div class="product-actions-grid">
          <button class="mobile-action-button secondary" type="button" @click="openProductEdit(product.id)">编辑</button>
          <button class="mobile-action-button secondary" type="button" @click="openProductImages(product.id)">图片</button>
          <button class="mobile-action-button secondary" type="button" @click="togglePublish(product)">
            {{ product.status === 'published' ? '撤回' : '发布' }}
          </button>
          <button class="mobile-action-button danger-button" type="button" @click="removeProduct(product)">删除</button>
        </div>
      </article>
      <el-empty v-if="!loading && !products.length" description="暂无商品" />
    </section>

    <article v-if="products.length" class="mobile-card mobile-panel pagination-card">
      <span class="mobile-muted">第 {{ page }} 页 · 每页 {{ pageSize }} 条</span>
      <div class="pagination-actions">
        <button class="mobile-action-button secondary" type="button" :disabled="page <= 1" @click="page -= 1; loadProducts()">上一页</button>
        <button class="mobile-action-button secondary" type="button" :disabled="!hasMore" @click="page += 1; loadProducts()">下一页</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.mobile-panel,
.pagination-card {
  padding: 18px;
}

.hero-filter-card {
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 244, 238, 0.96));
}

.hero-filter-head {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-create-button {
  width: 100%;
}

.filter-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 18px;
}

.filter-stack :deep(.el-input__wrapper) {
  min-height: 52px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
}

.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--mobile-muted);
  font-weight: 600;
  transition: all 180ms ease;
}

.status-chip.active {
  border-color: rgba(47, 106, 88, 0.22);
  background: rgba(47, 106, 88, 0.1);
  color: var(--brand-deep);
  box-shadow: 0 10px 18px rgba(29, 67, 56, 0.08);
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.product-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-card-main {
  display: flex;
  gap: 14px;
}

.cover-wrap {
  position: relative;
  flex-shrink: 0;
}

.product-cover {
  width: 92px;
  height: 118px;
  border-radius: 22px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
}

.product-cover-fallback {
  display: grid;
  place-items: center;
  color: var(--mobile-muted);
  font-size: 12px;
}

.cover-status-badge {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  min-height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(21, 43, 37, 0.78);
  color: #f9f4ec;
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(10px);
}

.product-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-copy strong {
  font-size: 18px;
  line-height: 1.25;
  color: #242320;
}

.product-meta,
.product-summary {
  margin: 0;
}

.product-meta {
  color: var(--mobile-muted);
  font-size: 13px;
}

.product-summary {
  color: #545d56;
  line-height: 1.65;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(192, 138, 54, 0.1);
  color: #805b2a;
  font-size: 12px;
  font-weight: 600;
}

.product-actions-grid,
.pagination-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.danger-button {
  background: linear-gradient(145deg, #e88d73, #cf694c);
  color: #fff8f3;
}

.pagination-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
