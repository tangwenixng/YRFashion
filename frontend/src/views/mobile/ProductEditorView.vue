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
    <article class="editor-toolbar">
      <div>
        <h2>{{ isEditing ? '编辑商品' : '新增商品' }}</h2>
        <p>{{ productId ? `ID ${productId}` : '新建内容' }}</p>
      </div>
      <button v-if="productId" class="ghost-action" type="button" @click="router.push(`/m/products/${productId}/images`)">图片</button>
    </article>

    <article class="editor-shell">
      <el-form label-position="top">
        <el-form-item label="商品名称">
          <el-input v-model="form.name" maxlength="60" placeholder="请输入商品名称" inputmode="text" />
        </el-form-item>

        <div class="editor-grid two-up">
          <el-form-item label="商品分类">
            <el-select v-model="form.category_id" clearable placeholder="选择分类">
              <el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="排序值">
            <el-input-number v-model="form.sort_order" :min="0" :step="10" />
          </el-form-item>
        </div>

        <el-form-item label="状态">
          <el-segmented v-model="form.status" :options="statusOptions" />
        </el-form-item>

        <el-form-item label="标签">
          <el-input v-model="form.tags_text" placeholder="用逗号分隔多个标签" inputmode="text" />
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input v-model="form.description" type="textarea" :rows="7" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
    </article>

    <div class="sticky-submit-bar">
      <button class="ghost-action" type="button" @click="router.back()">返回</button>
      <button class="mobile-action-button" type="button" :disabled="saving" @click="saveProduct">
        {{ saving ? '保存中…' : isEditing ? '保存修改' : '创建商品' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.editor-page {
  gap: 12px;
}

.editor-toolbar,
.editor-shell,
.sticky-submit-bar {
  border: 1px solid rgba(40, 55, 49, 0.08);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 28px rgba(20, 29, 25, 0.05);
}

.editor-toolbar {
  padding: 14px;
  border-radius: 18px 12px 18px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.editor-toolbar h2,
.editor-toolbar p {
  margin: 0;
}

.editor-toolbar h2 {
  font-size: 22px;
  color: #20231f;
}

.editor-toolbar p {
  margin-top: 6px;
  color: #68716b;
  font-size: 13px;
}

.editor-shell {
  padding: 14px;
  border-radius: 12px 22px 12px 22px;
}

.editor-shell :deep(.el-form-item) {
  margin-bottom: 16px;
}

.editor-shell :deep(.el-form-item__label) {
  color: #49584f;
  font-weight: 600;
}

.editor-shell :deep(.el-input__wrapper),
.editor-shell :deep(.el-textarea__inner),
.editor-shell :deep(.el-select__wrapper) {
  border-radius: 12px;
  background: rgba(248, 248, 245, 0.96);
}

.editor-shell :deep(.el-input-number) {
  width: 100%;
}

.editor-grid.two-up {
  display: grid;
  grid-template-columns: 1fr 112px;
  gap: 12px;
}

.sticky-submit-bar {
  position: sticky;
  bottom: calc(90px + env(safe-area-inset-bottom));
  padding: 10px;
  border-radius: 12px 18px 18px 12px;
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 10px;
}

.ghost-action {
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 12px;
  background: rgba(249, 249, 247, 0.96);
  color: #334039;
  font-weight: 600;
}
</style>
