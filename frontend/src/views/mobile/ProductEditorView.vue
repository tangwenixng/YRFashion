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
  <section class="mobile-page" v-loading="loading">
    <article class="mobile-card mobile-panel editor-panel">
      <div class="card-title-row">
        <h2 class="mobile-section-title">{{ isEditing ? '编辑商品' : '新增商品' }}</h2>
        <el-button plain @click="router.back()">返回</el-button>
      </div>

      <el-form label-position="top">
        <el-form-item label="商品名称">
          <el-input v-model="form.name" maxlength="60" placeholder="请输入商品名称" />
        </el-form-item>

        <el-form-item label="商品分类">
          <el-select v-model="form.category_id" clearable placeholder="选择分类">
            <el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-segmented v-model="form.status" :options="statusOptions" />
        </el-form-item>

        <el-form-item label="排序值">
          <el-input-number v-model="form.sort_order" :min="0" :step="10" />
        </el-form-item>

        <el-form-item label="标签">
          <el-input v-model="form.tags_text" placeholder="用逗号分隔多个标签" />
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input v-model="form.description" type="textarea" :rows="7" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
    </article>

    <article v-if="productId" class="mobile-card mobile-panel helper-panel">
      <div class="card-title-row">
        <h3 class="mobile-section-title">图片管理</h3>
        <el-button plain @click="router.push(`/m/products/${productId}/images`)">进入图片页</el-button>
      </div>
      <p class="mobile-muted">手机编辑页只保留基础信息，图片上传、封面设置和排序放到单独页面处理。</p>
    </article>

    <el-button class="save-button" type="primary" :loading="saving" @click="saveProduct">
      {{ isEditing ? '保存修改' : '创建商品' }}
    </el-button>
  </section>
</template>

<style scoped>
.mobile-panel {
  padding: 16px;
}

.helper-panel p {
  margin: 0;
  line-height: 1.7;
}

.save-button {
  height: 48px;
  border-radius: 18px;
}
</style>
