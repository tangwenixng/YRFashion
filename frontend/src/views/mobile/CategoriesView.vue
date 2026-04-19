<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  createCategory,
  fetchCategories,
  updateCategory,
  updateCategorySort,
  updateCategoryStatus,
  type CategoryItem,
} from '../../api/modules/categories'

const loading = ref(false)
const saving = ref(false)
const movingCategoryId = ref<number | null>(null)
const editorVisible = ref(false)
const categories = ref<CategoryItem[]>([])
const editingCategoryId = ref<number | null>(null)
const form = reactive({
  name: '',
  sort_order: 0,
  status: 'active' as 'active' | 'disabled',
})

const resetForm = () => {
  editingCategoryId.value = null
  form.name = ''
  form.sort_order = 0
  form.status = 'active'
}

const loadCategories = async () => {
  loading.value = true
  try {
    categories.value = await fetchCategories()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  editorVisible.value = true
}

const openEdit = (category: CategoryItem) => {
  editingCategoryId.value = category.id
  form.name = category.name
  form.sort_order = category.sort_order
  form.status = category.status
  editorVisible.value = true
}

const saveCategory = async () => {
  const payload = {
    name: form.name.trim(),
    sort_order: form.sort_order,
    status: form.status,
  }

  if (!payload.name) {
    ElMessage.warning('分类名称不能为空')
    return
  }

  saving.value = true
  try {
    if (editingCategoryId.value) {
      await updateCategory(editingCategoryId.value, payload)
      ElMessage.success('分类已更新')
    } else {
      await createCategory(payload)
      ElMessage.success('分类已创建')
    }

    editorVisible.value = false
    resetForm()
    await loadCategories()
  } finally {
    saving.value = false
  }
}

const moveCategory = async (category: CategoryItem, direction: 'up' | 'down') => {
  const currentIndex = categories.value.findIndex((item) => item.id === category.id)
  if (currentIndex < 0) {
    return
  }

  const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1
  const targetCategory = categories.value[targetIndex]
  if (!targetCategory) {
    return
  }

  movingCategoryId.value = category.id
  const sameSortOrder = category.sort_order === targetCategory.sort_order
  const nextCategorySort = sameSortOrder
    ? targetCategory.sort_order + (direction === 'up' ? -1 : 1)
    : targetCategory.sort_order
  const nextTargetSort = sameSortOrder ? targetCategory.sort_order : category.sort_order

  try {
    await Promise.all([
      updateCategorySort(category.id, nextCategorySort),
      updateCategorySort(targetCategory.id, nextTargetSort),
    ])
    ElMessage.success(direction === 'up' ? '已上移分类' : '已下移分类')
    await loadCategories()
  } finally {
    movingCategoryId.value = null
  }
}

const toggleStatus = async (category: CategoryItem) => {
  const nextStatus = category.status === 'active' ? 'disabled' : 'active'
  await updateCategoryStatus(category.id, nextStatus)
  ElMessage.success(nextStatus === 'active' ? '分类已启用' : '分类已停用')
  await loadCategories()
}

void loadCategories()
</script>

<template>
  <section class="mobile-page categories-page">
    <article class="page-hero mobile-card">
      <div>
        <span class="mobile-overline hero-overline">Category board</span>
        <h2 class="mobile-section-title">分类管理</h2>
        <p class="hero-copy mobile-muted">在手机上快速维护分类名称、状态、排序和关联商品情况。</p>
      </div>
      <div class="hero-actions">
        <button class="mobile-action-button secondary" type="button" @click="loadCategories">刷新</button>
        <button class="mobile-action-button" type="button" @click="openCreate">新增分类</button>
      </div>
    </article>

    <section class="category-list" v-loading="loading">
      <article v-for="(category, index) in categories" :key="category.id" class="category-card mobile-card">
        <div class="category-head">
          <div>
            <strong>{{ category.name }}</strong>
            <p>#{{ category.sort_order }} · {{ category.product_count }} 个商品</p>
          </div>
          <span class="status-pill" :class="category.status">
            {{ category.status === 'active' ? '启用中' : '已停用' }}
          </span>
        </div>

        <div class="category-actions">
          <button class="action-chip primary" type="button" @click="openEdit(category)">编辑</button>
          <button class="action-chip" type="button" @click="toggleStatus(category)">
            {{ category.status === 'active' ? '停用' : '启用' }}
          </button>
          <button
            class="action-chip"
            type="button"
            :disabled="index === 0 || movingCategoryId === category.id"
            @click="moveCategory(category, 'up')"
          >
            上移
          </button>
          <button
            class="action-chip"
            type="button"
            :disabled="index === categories.length - 1 || movingCategoryId === category.id"
            @click="moveCategory(category, 'down')"
          >
            下移
          </button>
        </div>
      </article>

      <div v-if="!loading && !categories.length" class="compact-empty">暂时没有分类，先新增一个吧。</div>
    </section>

    <el-dialog
      v-model="editorVisible"
      :title="editingCategoryId ? '编辑分类' : '新增分类'"
      width="92%"
      destroy-on-close
      align-center
    >
      <el-form label-position="top" class="editor-form">
        <el-form-item label="分类名称">
          <el-input v-model="form.name" placeholder="例如：外套" />
        </el-form-item>

        <div class="editor-grid">
          <el-form-item label="排序值">
            <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          </el-form-item>

          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="启用" value="active" />
              <el-option label="停用" value="disabled" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-actions">
          <button class="mobile-action-button secondary" type="button" @click="editorVisible = false">取消</button>
          <button class="mobile-action-button" type="button" :disabled="saving" @click="saveCategory">
            {{ saving ? '保存中…' : '保存分类' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.categories-page {
  gap: 12px;
}

.page-hero,
.category-card {
  padding: 16px;
}

.hero-overline {
  margin-bottom: 12px;
}

.hero-copy {
  margin: 10px 0 0;
  line-height: 1.7;
}

.hero-actions {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.category-head strong {
  display: block;
  font-size: 18px;
  color: #232622;
}

.category-head p {
  margin: 6px 0 0;
  color: #69736d;
  font-size: 13px;
}

.status-pill {
  flex-shrink: 0;
  min-height: 28px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status-pill.active {
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.status-pill.disabled {
  background: rgba(57, 76, 64, 0.08);
  color: #53625b;
}

.category-actions {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.action-chip {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  background: rgba(249, 249, 247, 0.96);
  color: #3d4a43;
  font-weight: 600;
}

.action-chip.primary {
  border-color: rgba(47, 106, 88, 0.16);
  background: rgba(47, 106, 88, 0.08);
  color: var(--brand-deep);
}

.action-chip:disabled {
  opacity: 0.48;
}

.compact-empty {
  padding: 22px 16px;
  border: 1px dashed rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  color: #717972;
  text-align: center;
  background: rgba(255, 255, 255, 0.66);
}

.editor-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.editor-grid {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 12px;
}

.editor-form :deep(.el-input-number),
.editor-form :deep(.el-select) {
  width: 100%;
}

.dialog-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
