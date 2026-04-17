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
    <article class="mobile-card mobile-panel">
      <div class="card-title-row">
        <h2 class="mobile-section-title">商品管理</h2>
        <el-button type="primary" @click="router.push('/m/products/create')">新增</el-button>
      </div>
      <div class="filter-stack">
        <el-input v-model="filters.keyword" clearable placeholder="搜索商品名称" @keyup.enter="applyFilters" />
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
          <img v-if="product.images[0]?.thumbnail_url || product.images[0]?.image_url" class="product-cover" :src="product.images[0]?.thumbnail_url || product.images[0]?.image_url || ''" alt="" />
          <div v-else class="product-cover product-cover-fallback">暂无封面</div>
          <div class="product-copy">
            <div class="product-head-row">
              <strong>{{ product.name }}</strong>
              <el-tag size="small" :type="product.status === 'published' ? 'success' : product.status === 'draft' ? 'warning' : 'info'">
                {{ product.status }}
              </el-tag>
            </div>
            <p class="mobile-muted">分类：{{ product.category_name || '未分类' }}</p>
            <p class="mobile-muted">{{ product.description || '暂未填写描述' }}</p>
          </div>
        </div>
        <div class="product-actions">
          <el-button plain @click="openProductEdit(product.id)">编辑</el-button>
          <el-button plain @click="openProductImages(product.id)">图片</el-button>
          <el-button plain @click="togglePublish(product)">
            {{ product.status === 'published' ? '撤回' : '发布' }}
          </el-button>
          <el-button plain type="danger" @click="removeProduct(product)">删除</el-button>
        </div>
      </article>
      <el-empty v-if="!loading && !products.length" description="暂无商品" />
    </section>

    <article v-if="products.length" class="mobile-card mobile-panel pagination-card">
      <span class="mobile-muted">共 {{ total }} 条 · 当前第 {{ page }} 页</span>
      <div class="pagination-actions">
        <el-button :disabled="page <= 1" @click="page -= 1; loadProducts()">上一页</el-button>
        <el-button :disabled="!hasMore" @click="page += 1; loadProducts()">下一页</el-button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.mobile-panel,
.pagination-card {
  padding: 16px;
}

.filter-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink-soft);
}

.status-chip.active {
  border-color: rgba(47, 106, 88, 0.3);
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.product-card-main {
  display: flex;
  gap: 14px;
}

.product-cover {
  width: 88px;
  height: 110px;
  border-radius: 18px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
}

.product-cover-fallback {
  display: grid;
  place-items: center;
  color: var(--ink-soft);
  font-size: 12px;
}

.product-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.product-copy strong {
  font-size: 16px;
}

.product-copy p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}

.product-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.product-actions,
.pagination-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
