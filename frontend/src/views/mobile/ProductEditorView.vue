<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchCategories, type CategoryItem } from '../../api/modules/categories'
import { createProduct, fetchProduct, updateProduct } from '../../api/modules/products'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const saving = ref(false)
const categories = ref<CategoryItem[]>([])
const form = reactive({
  name: '',
  category_id: null as number | null,
  description: '',
  tags_text: '',
  status: 'draft' as 'draft' | 'published' | 'archived',
  sort_order: 0,
})

const productId = computed(() => {
  const rawId = Number(route.params.id)
  return Number.isFinite(rawId) && rawId > 0 ? rawId : null
})
const isEditing = computed(() => Boolean(productId.value))

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已归档', value: 'archived' },
] as const

const buildTags = () =>
  form.tags_text
    .split(/[，,\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 8)

const loadEditor = async () => {
  loading.value = true
  try {
    categories.value = await fetchCategories()
    if (productId.value) {
      const product = await fetchProduct(productId.value)
      form.name = product.name
      form.category_id = product.category_id
      form.description = product.description
      form.tags_text = product.tags.join('，')
      form.status = product.status
      form.sort_order = product.sort_order
    }
  } finally {
    loading.value = false
  }
}

const saveProduct = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请先填写商品名称')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      category_id: form.category_id,
      description: form.description.trim(),
      tags: buildTags(),
      status: form.status,
      sort_order: Number(form.sort_order) || 0,
    }
    const product = productId.value
      ? await updateProduct(productId.value, payload)
      : await createProduct(payload)
    ElMessage.success(productId.value ? '商品已更新' : '商品已创建')
    await router.replace(`/m/products/${product.id}/edit`)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void loadEditor()
})
</script>

<template>
  <section class="mobile-page editor-page" v-loading="loading">
    <article class="mobile-card intro-card">
      <span class="section-kicker">{{ isEditing ? '编辑商品' : '新增商品' }}</span>
      <h2 class="mobile-section-title">把基础信息整理干净，图片单独维护更省心</h2>
      <p class="mobile-muted">手机端优先保留高频编辑字段，避免把复杂操作全部堆进同一屏里。</p>
    </article>

    <article class="mobile-card mobile-panel editor-panel">
      <el-form label-position="top">
        <el-form-item label="商品名称">
          <el-input v-model="form.name" maxlength="60" placeholder="请输入商品名称" inputmode="text" />
        </el-form-item>

        <el-form-item label="商品分类">
          <el-select v-model="form.category_id" clearable placeholder="选择分类">
            <el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-segmented v-model="form.status" :options="statusOptions" />
        </el-form-item>

        <div class="inline-grid">
          <el-form-item label="排序值">
            <el-input-number v-model="form.sort_order" :min="0" :step="10" />
          </el-form-item>
          <article class="mobile-chip helper-chip">标签上限 8 个</article>
        </div>

        <el-form-item label="标签">
          <el-input v-model="form.tags_text" placeholder="用逗号分隔多个标签" inputmode="text" />
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input v-model="form.description" type="textarea" :rows="7" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
    </article>

    <article v-if="productId" class="mobile-card mobile-panel helper-panel">
      <div class="helper-row">
        <div>
          <h3 class="helper-title">图片管理</h3>
          <p class="mobile-muted">封面、上传和排序都拆到独立页面，避免编辑页过长。</p>
        </div>
        <button class="mobile-action-button secondary" type="button" @click="router.push(`/m/products/${productId}/images`)">
          进入图片页
        </button>
      </div>
    </article>

    <div class="sticky-submit-bar mobile-card">
      <button class="mobile-action-button secondary" type="button" @click="router.back()">返回上一页</button>
      <button class="mobile-action-button" type="button" :disabled="saving" @click="saveProduct">
        {{ saving ? '保存中…' : isEditing ? '保存修改' : '创建商品' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.editor-page {
  padding-bottom: 12px;
}

.intro-card,
.mobile-panel,
.sticky-submit-bar {
  padding: 18px;
}

.intro-card {
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 244, 238, 0.96));
}

.intro-card p {
  margin: 12px 0 0;
  line-height: 1.7;
}

.editor-panel :deep(.el-form-item) {
  margin-bottom: 18px;
}

.editor-panel :deep(.el-form-item__label) {
  color: #49584f;
  font-weight: 600;
}

.editor-panel :deep(.el-input__wrapper),
.editor-panel :deep(.el-textarea__inner),
.editor-panel :deep(.el-select__wrapper) {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
}

.editor-panel :deep(.el-input-number) {
  width: 100%;
}

.inline-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
}

.helper-chip {
  justify-content: center;
  background: rgba(192, 138, 54, 0.12);
  color: #805b2a;
}

.helper-row {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.helper-title {
  margin: 0;
  font-size: 18px;
}

.helper-row p {
  margin: 8px 0 0;
  line-height: 1.7;
}

.sticky-submit-bar {
  position: sticky;
  bottom: calc(90px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  box-shadow: 0 20px 36px rgba(18, 25, 22, 0.1);
}
</style>
