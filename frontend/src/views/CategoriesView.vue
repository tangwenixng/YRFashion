<script setup lang="ts">
import { EditPen, Plus, RefreshRight, Sort } from '@element-plus/icons-vue'
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

const saveSort = async (category: CategoryItem) => {
  await updateCategorySort(category.id, category.sort_order)
  ElMessage.success('分类排序已更新')
  await loadCategories()
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
        <el-table-column prop="name" label="分类名称" min-width="220" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_count" label="关联商品" width="120" />
        <el-table-column label="排序" width="160">
          <template #default="{ row }">
            <div class="sort-box">
              <el-input-number v-model="row.sort_order" :min="0" :max="9999" />
              <el-button plain circle @click="saveSort(row)">
                <el-icon><Sort /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
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
.row-actions,
.sort-box {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.table-card {
  padding: 14px;
}

.inline-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .inline-grid {
    grid-template-columns: 1fr;
  }
}
</style>
