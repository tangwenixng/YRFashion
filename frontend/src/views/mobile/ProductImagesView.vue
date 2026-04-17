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
    items: images.value.map((image, index) => ({
      id: image.id,
      sort_order: index,
    })),
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
  <section class="mobile-page" v-loading="loading">
    <article class="mobile-card mobile-panel intro-card">
      <span class="section-kicker">图片管理</span>
      <h2 class="mobile-section-title">{{ productName || '当前商品' }}</h2>
      <p class="mobile-muted">上传、设封面和排序都集中在这里，手机端减少来回跳转。</p>
      <label class="upload-box">
        <input class="hidden-file-input" type="file" accept="image/*" multiple @change="uploadFiles" />
        <strong>{{ uploading ? '上传中…' : '选择图片上传' }}</strong>
        <span>建议一次批量上传后再决定封面与顺序</span>
      </label>
    </article>

    <section class="image-list">
      <article v-for="(image, index) in images" :key="image.id" class="mobile-card image-card">
        <div class="image-frame">
          <img class="image-preview" :src="image.image_url" alt="" />
          <span class="image-order-badge">#{{ index + 1 }}</span>
          <span v-if="image.is_cover" class="image-cover-badge">当前封面</span>
        </div>
        <div class="image-copy">
          <strong>{{ image.original_name }}</strong>
          <span class="mobile-muted">排序 {{ image.sort_order }} · {{ image.is_cover ? '展示优先' : '普通图片' }}</span>
        </div>
        <div class="image-actions-grid">
          <button class="mobile-action-button secondary" type="button" :disabled="image.is_cover" @click="setCover(image.id)">设封面</button>
          <button class="mobile-action-button secondary" type="button" :disabled="index === 0" @click="moveImage(index, -1)">上移</button>
          <button class="mobile-action-button secondary" type="button" :disabled="index === images.length - 1" @click="moveImage(index, 1)">下移</button>
          <button class="mobile-action-button danger-button" type="button" @click="removeImage(image.id)">删除</button>
        </div>
      </article>
      <el-empty v-if="!loading && !images.length" description="还没有上传图片" />
    </section>

    <button class="mobile-action-button secondary return-button" type="button" @click="router.back()">返回商品编辑页</button>
  </section>
</template>

<style scoped>
.mobile-panel,
.return-button {
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

.upload-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 18px;
  padding: 18px;
  border: 1px dashed rgba(57, 76, 64, 0.16);
  border-radius: 24px;
  background: rgba(47, 106, 88, 0.04);
  text-align: left;
}

.upload-box strong {
  color: var(--brand-deep);
}

.upload-box span {
  color: var(--mobile-muted);
  line-height: 1.6;
}

.hidden-file-input {
  display: none;
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.image-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.image-frame {
  position: relative;
}

.image-preview {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 24px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
}

.image-order-badge,
.image-cover-badge {
  position: absolute;
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 700;
  backdrop-filter: blur(10px);
}

.image-order-badge {
  top: 10px;
  left: 10px;
  background: rgba(21, 43, 37, 0.76);
  color: #f9f4ec;
}

.image-cover-badge {
  right: 10px;
  bottom: 10px;
  background: rgba(192, 138, 54, 0.92);
  color: #2b2419;
}

.image-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-copy strong {
  font-size: 17px;
}

.image-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.danger-button {
  background: linear-gradient(145deg, #e88d73, #cf694c);
  color: #fff8f3;
}

.return-button {
  width: 100%;
}
</style>
