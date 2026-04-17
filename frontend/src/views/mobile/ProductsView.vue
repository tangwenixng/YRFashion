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
  <section class="mobile-page products-page">
    <section class="products-toolbar">
      <div class="filter-head">
        <p class="toolbar-summary">{{ filters.status ? statusTabs.find((tab) => tab.value === filters.status)?.label : '全部' }} · {{ total }} 条结果</p>
        <button class="mobile-action-button toolbar-add" type="button" @click="router.push('/m/products/create')">新增</button>
      </div>

      <div class="search-row search-strip">
        <el-input v-model="filters.keyword" clearable placeholder="搜索名称或标签" @keyup.enter="applyFilters" />
      </div>

      <div class="segment-wrap">
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
    </section>

    <section class="product-list" v-loading="loading">
      <article v-for="product in products" :key="product.id" class="product-card">
        <div class="product-main">
          <div class="cover-wrap">
            <img
              v-if="product.images[0]?.thumbnail_url || product.images[0]?.image_url"
              class="product-cover"
              :src="product.images[0]?.thumbnail_url || product.images[0]?.image_url || ''"
              alt=""
            />
            <div v-else class="product-cover product-cover-fallback">暂无封面</div>
          </div>

          <div class="product-copy">
            <strong>{{ product.name }}</strong>
            <div class="product-meta-row">
              <span class="product-category">{{ product.category_name || '未分类' }}</span>
              <span class="product-status-pill">{{ formatStatusLabel(product.status) }}</span>
            </div>
            <p class="product-desc">{{ product.description || '暂无描述' }}</p>
          </div>
        </div>

        <div class="product-actions">
          <button class="action-chip primary" type="button" @click="openProductEdit(product.id)">编辑</button>
          <button class="action-chip" type="button" @click="openProductImages(product.id)">图片</button>
          <button class="action-chip" type="button" @click="togglePublish(product)">{{ product.status === 'published' ? '撤回' : '发布' }}</button>
          <button class="action-chip danger" type="button" @click="removeProduct(product)">删除</button>
        </div>
      </article>
      <div v-if="!loading && !products.length" class="compact-empty">暂无商品</div>
    </section>

    <article v-if="products.length" class="pager-shell">
      <span>{{ total }} 条</span>
      <div class="pager-actions">
        <button class="ghost-action" type="button" :disabled="page <= 1" @click="page -= 1; loadProducts()">上一页</button>
        <button class="ghost-action" type="button" :disabled="!hasMore" @click="page += 1; loadProducts()">下一页</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.products-page {
  gap: 12px;
}

.product-card,
.pager-shell {
  border: 1px solid rgba(40, 55, 49, 0.08);
  background: rgba(255, 255, 255, 0.96);
}

.products-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 2px;
}

.toolbar-summary {
  margin: 0;
  color: #727973;
  font-size: 12px;
  letter-spacing: 0.01em;
}

.toolbar-add {
  min-width: 58px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 14px;
  font-size: 13px;
  box-shadow: 0 8px 14px rgba(35, 86, 71, 0.12);
}

.search-row {
  margin: 0;
}

.search-strip {
  padding: 4px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(40, 55, 49, 0.06);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.search-row :deep(.el-input__wrapper) {
  min-height: 38px;
  border-radius: 12px;
  background: rgba(247, 248, 244, 0.92);
  box-shadow: inset 0 0 0 1px rgba(57, 76, 64, 0.06);
}

.segment-wrap {
  padding: 4px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(40, 55, 49, 0.06);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.status-chips {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
}

.status-chip {
  min-height: 30px;
  padding: 0 8px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: #66706a;
  font-size: 12px;
  font-weight: 600;
}

.status-chip.active {
  background: rgba(255, 255, 255, 0.96);
  color: var(--brand-deep);
  box-shadow: 0 4px 10px rgba(34, 52, 45, 0.08);
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.product-card {
  padding: 14px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(250, 250, 247, 0.94));
  box-shadow: 0 10px 24px rgba(28, 40, 34, 0.06);
}

.product-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.cover-wrap {
  position: relative;
  flex-shrink: 0;
}

.product-cover {
  width: 92px;
  height: 118px;
  border-radius: 18px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
}

.product-cover-fallback {
  display: grid;
  place-items: center;
  color: #727b75;
  font-size: 12px;
}

.product-copy {
  flex: 1;
  min-width: 0;
}

.product-copy strong {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 17px;
  color: #242622;
  line-height: 1.35;
}

.product-meta-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.product-category {
  min-width: 0;
  color: #6f7771;
  font-size: 13px;
}

.product-status-pill {
  flex-shrink: 0;
  min-height: 24px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(43, 83, 69, 0.1);
  color: #315347;
  font-size: 11px;
  font-weight: 700;
}

.product-copy p {
  margin: 6px 0 0;
  color: #68716b;
  font-size: 13px;
}

.product-desc {
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #7a827c;
}

.product-actions {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.action-chip,
.ghost-action {
  min-height: 38px;
  padding: 0 10px;
  border: 1px solid rgba(57, 76, 64, 0.08);
  border-radius: 14px;
  background: rgba(247, 248, 244, 0.94);
  color: #334039;
  font-weight: 600;
}

.action-chip.primary {
  background: rgba(47, 106, 88, 0.1);
  color: var(--brand-deep);
}

.action-chip.danger {
  color: #b54d38;
  background: rgba(214, 92, 70, 0.08);
}

.compact-empty {
  padding: 24px 16px;
  border: 1px dashed rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  color: #717972;
  text-align: center;
  background: rgba(255, 255, 255, 0.66);
}

.pager-shell {
  padding: 12px 14px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #6d756e;
  font-size: 13px;
}

.pager-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
