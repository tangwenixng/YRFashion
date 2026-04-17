<script setup lang="ts">
import { EditPen, Plus, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  createCategory,
  fetchCategories,
  updateCategory,
  updateCategorySort,
  updateCategoryStatus,
  type CategoryItem,
} from '../api/modules/categories'

const loading = ref(false)
const categories = ref<CategoryItem[]>([])
const movingCategoryId = ref<number | null>(null)
const editorVisible = ref(false)
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
  <section class="categories-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">分类管理</h1>
        <p class="page-subtitle">维护商品分类名称、启停状态和前台展示顺序。</p>
      </div>

      <div class="header-actions">
        <el-button plain @click="loadCategories">
          <el-icon><RefreshRight /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增分类
        </el-button>
      </div>
    </div>

    <section class="content-card table-card">
      <el-table :data="categories" v-loading="loading">
        <el-table-column prop="name" label="分类名称" width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_count" label="关联商品" width="110" />
        <el-table-column label="排序" width="180">
          <template #default="{ row, $index }">
            <div class="sort-box">
              <span class="sort-value">#{{ row.sort_order }}</span>
              <div class="sort-actions">
                <el-button
                  link
                  size="small"
                  class="sort-action"
                  :disabled="$index === 0 || movingCategoryId === row.id"
                  @click="moveCategory(row, 'up')"
                >
                  上移
                </el-button>
                <span class="sort-divider"></span>
                <el-button
                  link
                  size="small"
                  class="sort-action"
                  :disabled="$index === categories.length - 1 || movingCategoryId === row.id"
                  @click="moveCategory(row, 'down')"
                >
                  下移
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button plain @click="openEdit(row)">
                <el-icon><EditPen /></el-icon>
                编辑
              </el-button>
              <el-button plain @click="toggleStatus(row)">
                {{ row.status === 'active' ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="editorVisible"
      :title="editingCategoryId ? '编辑分类' : '新增分类'"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="分类名称">
          <el-input v-model="form.name" placeholder="例如：外套" />
        </el-form-item>

        <div class="inline-grid">
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
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.categories-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.header-actions,
.row-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sort-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  white-space: nowrap;
}

.sort-value {
  min-width: 36px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.sort-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.sort-action {
  padding: 0;
}

.sort-divider {
  width: 1px;
  height: 12px;
  background: var(--line-soft);
}

.table-card {
  padding: 14px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

:deep(.el-table) {
  min-width: 760px;
}

.inline-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1024px) {
  .page-header {
    flex-direction: column;
  }

  .inline-grid {
    grid-template-columns: 1fr;
  }
}
</style>
