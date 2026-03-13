<script setup lang="ts">
import { EditPen, Picture, Plus, RefreshRight, Sort } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  createProduct,
  fetchProducts,
  updateProduct,
  updateProductSort,
  uploadProductImage,
  type ProductItem,
} from '../api/modules/products'

type ProductFormState = {
  name: string
  category_id: number | null
  description: string
  tagsText: string
  status: 'draft' | 'published' | 'archived'
  sort_order: number
}

const loading = ref(false)
const products = ref<ProductItem[]>([])
const editorVisible = ref(false)
const uploadVisible = ref(false)
const editingProductId = ref<number | null>(null)
const uploadingProduct = ref<ProductItem | null>(null)
const uploadSortOrder = ref(0)
const uploadAsCover = ref(true)
const selectedFile = ref<File | null>(null)

const form = reactive<ProductFormState>({
  name: '',
  category_id: null,
  description: '',
  tagsText: '',
  status: 'draft',
  sort_order: 0,
})

const resetForm = () => {
  editingProductId.value = null
  form.name = ''
  form.category_id = null
  form.description = ''
  form.tagsText = ''
  form.status = 'draft'
  form.sort_order = 0
}

const loadProducts = async () => {
  loading.value = true
  try {
    products.value = await fetchProducts()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  editorVisible.value = true
}

const openEdit = (product: ProductItem) => {
  editingProductId.value = product.id
  form.name = product.name
  form.category_id = product.category_id
  form.description = product.description
  form.tagsText = product.tags.join(', ')
  form.status = product.status
  form.sort_order = product.sort_order
  editorVisible.value = true
}

const saveProduct = async () => {
  const payload = {
    name: form.name.trim(),
    category_id: form.category_id,
    description: form.description.trim(),
    tags: form.tagsText
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean),
    status: form.status,
    sort_order: form.sort_order,
  }

  if (!payload.name) {
    ElMessage.warning('商品名称不能为空')
    return
  }

  if (editingProductId.value) {
    await updateProduct(editingProductId.value, payload)
    ElMessage.success('商品已更新')
  } else {
    await createProduct(payload)
    ElMessage.success('商品已创建')
  }

  editorVisible.value = false
  resetForm()
  await loadProducts()
}

const saveSort = async (product: ProductItem) => {
  await updateProductSort(product.id, product.sort_order)
  ElMessage.success('排序已更新')
  await loadProducts()
}

const openUpload = (product: ProductItem) => {
  uploadingProduct.value = product
  uploadVisible.value = true
  selectedFile.value = null
  uploadSortOrder.value = product.images.length
  uploadAsCover.value = product.images.length === 0
}

const handleFileChange = (uploadFile: { raw?: File }) => {
  selectedFile.value = uploadFile.raw ?? null
}

const submitUpload = async () => {
  if (!uploadingProduct.value || !selectedFile.value) {
    ElMessage.warning('请先选择图片文件')
    return
  }

  await uploadProductImage(
    uploadingProduct.value.id,
    selectedFile.value,
    uploadSortOrder.value,
    uploadAsCover.value,
  )
  ElMessage.success('图片上传成功')
  uploadVisible.value = false
  await loadProducts()
}

void loadProducts()
</script>

<template>
  <section class="products-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">商品管理</h1>
        <p class="page-subtitle">在这里维护商品文案、展示状态、排序和本地图片资源。</p>
      </div>

      <div class="header-actions">
        <el-button plain @click="loadProducts">
          <el-icon><RefreshRight /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增商品
        </el-button>
      </div>
    </div>

    <section class="content-card table-card">
      <el-table :data="products" v-loading="loading">
        <el-table-column prop="name" label="商品名称" min-width="180" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : row.status === 'draft' ? 'warning' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag v-for="tag in row.tags" :key="tag" effect="plain">{{ tag }}</el-tag>
              <span v-if="row.tags.length === 0" class="muted">未设置</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <strong>{{ row.images.length }}</strong>
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button plain @click="openEdit(row)">
                <el-icon><EditPen /></el-icon>
                编辑
              </el-button>
              <el-button plain @click="openUpload(row)">
                <el-icon><Picture /></el-icon>
                上传图片
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="editorVisible"
      :title="editingProductId ? '编辑商品' : '新增商品'"
      width="680px"
      destroy-on-close
    >
      <div class="editor-grid">
        <el-form label-position="top">
          <el-form-item label="商品名称">
            <el-input v-model="form.name" placeholder="例如：羊毛大衣" />
          </el-form-item>

          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="5" placeholder="请输入商品描述" />
          </el-form-item>

          <div class="inline-grid">
            <el-form-item label="标签">
              <el-input v-model="form.tagsText" placeholder="用英文逗号分隔，如：通勤, 春季" />
            </el-form-item>

            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="排序值">
            <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uploadVisible" title="上传商品图片" width="560px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="目标商品">
          <el-input :model-value="uploadingProduct?.name ?? ''" disabled />
        </el-form-item>

        <div class="inline-grid">
          <el-form-item label="图片排序">
            <el-input-number v-model="uploadSortOrder" :min="0" :max="9999" />
          </el-form-item>
          <el-form-item label="封面图">
            <el-switch v-model="uploadAsCover" />
          </el-form-item>
        </div>

        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".jpg,.jpeg,.png,.webp"
          :on-change="handleFileChange"
        >
          <el-icon class="upload-icon"><Picture /></el-icon>
          <div class="el-upload__text">拖拽图片到这里，或点击选择文件</div>
          <template #tip>
            <div class="el-upload__tip">支持 JPG / PNG / WEBP，文件大小不超过 5MB</div>
          </template>
        </el-upload>
      </el-form>

      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload">开始上传</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.products-page {
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
.tag-list,
.sort-box {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.table-card {
  padding: 14px;
}

.muted {
  color: #907e6a;
  font-size: 13px;
}

.editor-grid {
  padding-top: 8px;
}

.inline-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.upload-icon {
  font-size: 28px;
  color: #7d5535;
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
