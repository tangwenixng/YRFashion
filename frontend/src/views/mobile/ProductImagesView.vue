<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  deleteProductImage,
  fetchProduct,
  updateProductImageCover,
  updateProductImagesSort,
  uploadProductImage,
  type ProductImage,
} from '../../api/modules/products'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const uploading = ref(false)
const productName = ref('')
const images = ref<ProductImage[]>([])

const productId = computed(() => Number(route.params.id || 0))

const loadProduct = async () => {
  if (!productId.value) {
    return
  }

  loading.value = true
  try {
    const product = await fetchProduct(productId.value)
    productName.value = product.name
    images.value = product.images.slice().sort((left, right) => left.sort_order - right.sort_order)
  } finally {
    loading.value = false
  }
}

const syncSort = async () => {
  await updateProductImagesSort(productId.value, {
    items: images.value.map((image, index) => ({ id: image.id, sort_order: index })),
  })
  await loadProduct()
}

const moveImage = async (index: number, direction: -1 | 1) => {
  const targetIndex = index + direction
  if (!images.value[targetIndex]) {
    return
  }

  const nextImages = [...images.value]
  const [currentImage] = nextImages.splice(index, 1)
  nextImages.splice(targetIndex, 0, currentImage)
  images.value = nextImages
  await syncSort()
  ElMessage.success('图片排序已更新')
}

const setCover = async (imageId: number) => {
  await updateProductImageCover(productId.value, imageId)
  ElMessage.success('封面已更新')
  await loadProduct()
}

const removeImage = async (imageId: number) => {
  try {
    await ElMessageBox.confirm('确认删除这张图片吗？', '删除图片', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  await deleteProductImage(productId.value, imageId)
  ElMessage.success('图片已删除')
  await loadProduct()
}

const uploadFiles = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const fileList = Array.from(input.files ?? [])
  if (!fileList.length) {
    return
  }

  uploading.value = true
  try {
    for (const [index, file] of fileList.entries()) {
      await uploadProductImage(productId.value, file, images.value.length + index)
    }
    ElMessage.success('图片上传完成')
    await loadProduct()
  } finally {
    uploading.value = false
    input.value = ''
  }
}

onMounted(() => {
  void loadProduct()
})
</script>

<template>
  <section class="mobile-page image-page" v-loading="loading">
    <article class="image-toolbar">
      <div>
        <h2>图片</h2>
        <p>{{ productName || '当前商品' }}</p>
      </div>
      <label class="upload-trigger">
        <input class="hidden-file-input" type="file" accept="image/*" multiple @change="uploadFiles" />
        {{ uploading ? '上传中…' : '上传' }}
      </label>
    </article>

    <section class="image-list">
      <article v-for="(image, index) in images" :key="image.id" class="image-card">
        <div class="image-frame">
          <img class="image-preview" :src="image.image_url" alt="" />
          <span class="image-order-badge">#{{ index + 1 }}</span>
          <span v-if="image.is_cover" class="image-cover-badge">封面</span>
        </div>
        <div class="image-copy">
          <strong>{{ image.original_name }}</strong>
          <span>排序 {{ image.sort_order }}</span>
        </div>
        <div class="image-actions-grid">
          <button class="action-chip" type="button" :disabled="image.is_cover" @click="setCover(image.id)">设封面</button>
          <button class="action-chip" type="button" :disabled="index === 0" @click="moveImage(index, -1)">上移</button>
          <button class="action-chip" type="button" :disabled="index === images.length - 1" @click="moveImage(index, 1)">下移</button>
          <button class="action-chip danger" type="button" @click="removeImage(image.id)">删除</button>
        </div>
      </article>
      <el-empty v-if="!loading && !images.length" description="还没有上传图片" />
    </section>

    <button class="ghost-action full-width" type="button" @click="router.back()">返回</button>
  </section>
</template>

<style scoped>
.image-page {
  gap: 12px;
}

.image-toolbar,
.image-card,
.full-width {
  border: 1px solid rgba(40, 55, 49, 0.08);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 28px rgba(20, 29, 25, 0.05);
}

.image-toolbar {
  padding: 14px;
  border-radius: 18px 12px 18px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.image-toolbar h2,
.image-toolbar p {
  margin: 0;
}

.image-toolbar h2 {
  font-size: 22px;
  color: #20231f;
}

.image-toolbar p {
  margin-top: 6px;
  color: #68716b;
  font-size: 13px;
}

.upload-trigger,
.action-chip,
.ghost-action {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 12px 16px 12px 16px;
  background: rgba(249, 249, 247, 0.96);
  color: #334039;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hidden-file-input {
  display: none;
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-card {
  padding: 14px;
  border-radius: 12px 22px 22px 12px;
}

.image-frame {
  position: relative;
}

.image-preview {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 12px 22px 22px 12px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
}

.image-order-badge,
.image-cover-badge {
  position: absolute;
  min-height: 28px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.image-order-badge {
  top: 8px;
  left: 8px;
  background: rgba(21, 43, 37, 0.76);
  color: #f9f4ec;
}

.image-cover-badge {
  right: 8px;
  bottom: 8px;
  background: rgba(192, 138, 54, 0.92);
  color: #2b2419;
}

.image-copy {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #68716b;
  font-size: 13px;
}

.image-copy strong {
  color: #20231f;
}

.image-actions-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.action-chip.danger {
  color: #b54d38;
  background: rgba(214, 92, 70, 0.08);
}

.full-width {
  width: 100%;
}
</style>

<style scoped>
.text-truncate-wrap {
  min-width: 0;
}
.text-truncate-wrap > * {
  min-width: 0;
}
.text-truncate-wrap :deep(*) {
  min-width: 0;
}
</style>
