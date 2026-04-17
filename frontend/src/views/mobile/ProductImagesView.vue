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
    <article class="mobile-card mobile-panel">
      <div class="card-title-row">
        <div>
          <h2 class="mobile-section-title">图片管理</h2>
          <p class="mobile-muted">{{ productName || '当前商品' }}</p>
        </div>
        <el-button plain @click="router.back()">返回</el-button>
      </div>

      <label class="upload-box">
        <input class="hidden-file-input" type="file" accept="image/*" multiple @change="uploadFiles" />
        <span>{{ uploading ? '上传中…' : '选择图片上传' }}</span>
      </label>
    </article>

    <section class="image-list">
      <article v-for="(image, index) in images" :key="image.id" class="mobile-card image-card">
        <img class="image-preview" :src="image.image_url" alt="" />
        <div class="image-copy">
          <strong>{{ image.original_name }}</strong>
          <span class="mobile-muted">排序 {{ image.sort_order }}{{ image.is_cover ? ' · 当前封面' : '' }}</span>
        </div>
        <div class="image-actions">
          <el-button plain :disabled="image.is_cover" @click="setCover(image.id)">设封面</el-button>
          <el-button plain :disabled="index === 0" @click="moveImage(index, -1)">上移</el-button>
          <el-button plain :disabled="index === images.length - 1" @click="moveImage(index, 1)">下移</el-button>
          <el-button plain type="danger" @click="removeImage(image.id)">删除</el-button>
        </div>
      </article>
      <el-empty v-if="!loading && !images.length" description="还没有上传图片" />
    </section>
  </section>
</template>

<style scoped>
.mobile-panel {
  padding: 16px;
}

.upload-box {
  display: block;
  padding: 16px;
  border: 1px dashed rgba(57, 76, 64, 0.2);
  border-radius: 18px;
  background: rgba(47, 106, 88, 0.04);
  text-align: center;
  color: var(--brand-deep);
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
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-preview {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 18px;
  object-fit: cover;
  background: rgba(57, 76, 64, 0.08);
}

.image-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
