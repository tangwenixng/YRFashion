<script setup lang="ts">
import { ArrowLeft, Delete, Picture, Sort, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchCategories, type CategoryItem } from '../api/modules/categories'
import {
  createProduct,
  deleteProductImage,
  fetchProduct,
  updateProduct,
  updateProductImageCover,
  updateProductImagesSort,
  uploadProductImage,
  type ProductImage,
} from '../api/modules/products'

type ProductFormState = {
  name: string
  category_id: number | null
  description: string
  tagsText: string
  status: 'draft' | 'published' | 'archived'
  sort_order: number
}

type EditorImageItem = {
  key: string
  id: number | null
  image_url: string
  original_name: string
  sort_order: number
  is_cover: boolean
  source: 'existing' | 'new'
  file: File | null
  object_url: string | null
}

const route = useRoute()
const router = useRouter()

const saving = ref(false)
const loading = ref(false)
const categories = ref<CategoryItem[]>([])
const editorUploadRef = ref<{ clearFiles: () => void } | null>(null)
const editorActiveTab = ref<'basic' | 'media'>('basic')
const editorImages = ref<EditorImageItem[]>([])
const removedImageIds = ref<number[]>([])
const imageUploadKey = ref(0)
const dragImageKey = ref('')
const dragOverImageKey = ref('')

const form = reactive<ProductFormState>({
  name: '',
  category_id: null,
  description: '',
  tagsText: '',
  status: 'draft',
  sort_order: 0,
})

const productId = computed(() => {
  const rawId = Number(route.params.id || 0)
  return Number.isFinite(rawId) && rawId > 0 ? rawId : null
})

const isEditing = computed(() => Boolean(productId.value))
const pageTitle = computed(() => (isEditing.value ? '编辑商品' : '新增商品'))
const pageSubtitle = computed(() =>
  isEditing.value
    ? '调整基础信息与图片顺序，保存后会同步更新列表展示。'
    : '先填写基础信息，再补充图片与封面，完成后保存到商品列表。',
)

const resetEditorImages = () => {
  editorImages.value.forEach((image) => {
    if (image.object_url) {
      URL.revokeObjectURL(image.object_url)
    }
  })
  editorImages.value = []
  removedImageIds.value = []
  dragImageKey.value = ''
  dragOverImageKey.value = ''
  imageUploadKey.value += 1
  editorUploadRef.value?.clearFiles?.()
}

const resetForm = () => {
  editorActiveTab.value = 'basic'
  form.name = ''
  form.category_id = null
  form.description = ''
  form.tagsText = ''
  form.status = 'draft'
  form.sort_order = 0
  resetEditorImages()
}

const normalizeEditorImages = (nextImages: EditorImageItem[], preferredCoverKey = '') => {
  const fallbackCoverKey =
    nextImages.find((item) => item.key === preferredCoverKey)?.key ||
    nextImages.find((item) => item.is_cover)?.key ||
    nextImages[0]?.key ||
    ''

  editorImages.value = nextImages.map((item, index) => ({
    ...item,
    sort_order: index,
    is_cover: item.key === fallbackCoverKey,
  }))
}

const toEditorImage = (image: ProductImage): EditorImageItem => ({
  key: `existing-${image.id}`,
  id: image.id,
  image_url: image.image_url,
  original_name: image.original_name,
  sort_order: image.sort_order,
  is_cover: image.is_cover,
  source: 'existing',
  file: null,
  object_url: null,
})

const loadCategoriesAndProduct = async () => {
  loading.value = true
  resetForm()
  try {
    categories.value = await fetchCategories()

    if (!productId.value) {
      return
    }

    const product = await fetchProduct(productId.value)
    form.name = product.name
    form.category_id = product.category_id
    form.description = product.description
    form.tagsText = product.tags.join(', ')
    form.status = product.status
    form.sort_order = product.sort_order
    normalizeEditorImages(product.images.map(toEditorImage))
  } catch (error) {
    ElMessage.error(isEditing.value ? '商品加载失败' : '初始化失败')
    if (isEditing.value) {
      void router.push('/products')
    }
  } finally {
    loading.value = false
  }
}

const buildPayload = () => ({
  name: form.name.trim(),
  category_id: form.category_id,
  description: form.description.trim(),
  tags: form.tagsText
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
  status: form.status,
  sort_order: form.sort_order,
})

const handleEditorFileChange = (uploadFile: { raw?: File }) => {
  const rawFile = uploadFile.raw
  if (!rawFile) {
    return
  }

  const objectUrl = URL.createObjectURL(rawFile)
  const nextImages = editorImages.value.concat({
    key: `new-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    id: null,
    image_url: objectUrl,
    original_name: rawFile.name,
    sort_order: editorImages.value.length,
    is_cover: editorImages.value.length === 0,
    source: 'new',
    file: rawFile,
    object_url: objectUrl,
  })
  normalizeEditorImages(nextImages)
  editorActiveTab.value = 'media'
}

const setEditorCover = (imageKey: string) => {
  normalizeEditorImages(editorImages.value, imageKey)
}

const removeEditorImage = (imageKey: string) => {
  const target = editorImages.value.find((item) => item.key === imageKey)
  if (!target) {
    return
  }

  if (target.source === 'existing' && target.id) {
    removedImageIds.value.push(target.id)
  }
  if (target.object_url) {
    URL.revokeObjectURL(target.object_url)
  }

  normalizeEditorImages(editorImages.value.filter((item) => item.key !== imageKey))
}

const handleImageDragStart = (imageKey: string) => {
  dragImageKey.value = imageKey
}

const handleImageDragEnter = (imageKey: string) => {
  if (dragImageKey.value && dragImageKey.value !== imageKey) {
    dragOverImageKey.value = imageKey
  }
}

const handleImageDragEnd = () => {
  dragImageKey.value = ''
  dragOverImageKey.value = ''
}

const handleImageDrop = (targetKey: string) => {
  const sourceKey = dragImageKey.value
  dragImageKey.value = ''
  dragOverImageKey.value = ''

  if (!sourceKey || sourceKey === targetKey) {
    return
  }

  const nextImages = [...editorImages.value]
  const sourceIndex = nextImages.findIndex((item) => item.key === sourceKey)
  const targetIndex = nextImages.findIndex((item) => item.key === targetKey)
  if (sourceIndex === -1 || targetIndex === -1) {
    return
  }

  const [movedImage] = nextImages.splice(sourceIndex, 1)
  nextImages.splice(targetIndex, 0, movedImage)
  normalizeEditorImages(nextImages, movedImage.is_cover ? movedImage.key : '')
}

const saveProduct = async () => {
  if (saving.value) {
    return
  }

  const payload = buildPayload()
  if (!payload.name) {
    ElMessage.warning('商品名称不能为空')
    editorActiveTab.value = 'basic'
    return
  }

  saving.value = true
  try {
    const savedProduct = productId.value
      ? await updateProduct(productId.value, payload)
      : await createProduct(payload)

    for (const imageId of removedImageIds.value) {
      await deleteProductImage(savedProduct.id, imageId)
    }

    const uploadedImageMap = new Map<string, ProductImage>()
    for (const image of editorImages.value) {
      if (image.source !== 'new' || !image.file) {
        continue
      }

      const uploadedImage = await uploadProductImage(savedProduct.id, image.file, image.sort_order, false)
      uploadedImageMap.set(image.key, uploadedImage)
    }

    const finalSortItems = editorImages.value
      .map((image, index) => {
        const imageId = image.source === 'existing' ? image.id : uploadedImageMap.get(image.key)?.id
        if (!imageId) {
          return null
        }
        return {
          id: imageId,
          sort_order: index,
        }
      })
      .filter((item): item is { id: number; sort_order: number } => item !== null)

    if (finalSortItems.length) {
      await updateProductImagesSort(savedProduct.id, { items: finalSortItems })
      const coverImage = editorImages.value.find((image) => image.is_cover)
      const coverImageId = coverImage
        ? (coverImage.source === 'existing' ? coverImage.id : uploadedImageMap.get(coverImage.key)?.id) || null
        : null
      if (coverImageId) {
        await updateProductImageCover(savedProduct.id, coverImageId)
      }
    }

    ElMessage.success(productId.value ? '商品已更新' : '商品已创建')
    void router.push('/products')
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  void router.push('/products')
}

watch(
  () => route.fullPath,
  () => {
    void loadCategoriesAndProduct()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  resetEditorImages()
})
</script>

<template>
  <section class="product-editor-page" v-loading="loading">
    <div class="editor-page-header">
      <div class="editor-page-heading">
        <button class="back-button" type="button" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </button>
        <span class="editor-kicker">{{ isEditing ? 'CONTENT ATELIER' : 'NEW ENTRY' }}</span>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageSubtitle }}</p>
      </div>

      <div class="editor-page-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" class="editor-save-button" :loading="saving" @click="saveProduct">
          保存商品
        </el-button>
      </div>
    </div>

    <div class="editor-grid">
      <div class="editor-canvas">
        <el-form label-position="top">
          <el-tabs v-model="editorActiveTab" class="editor-tabs">
            <el-tab-pane name="basic" label="基本信息">
              <section class="editor-section editor-section-basic">
                <div class="section-shell">
                  <div class="section-kicker">BASIC</div>
                </div>
                <div class="editor-section-header">
                  <div>
                    <h3>基础信息</h3>
                    <p>先确认标题、描述和分类信息，再继续处理图片与展示顺序。</p>
                  </div>
              </div>

              <div class="basic-form-layout">
                <div class="basic-form-main">
                  <el-form-item label="商品名称">
                    <el-input v-model="form.name" placeholder="例如：羊毛大衣" />
                  </el-form-item>

                  <el-form-item label="描述">
                    <el-input v-model="form.description" type="textarea" :rows="8" placeholder="请输入商品描述" />
                  </el-form-item>
                </div>

                <div class="basic-form-side">
                  <el-form-item label="分类">
                    <el-select v-model="form.category_id" clearable placeholder="请选择分类">
                      <el-option
                        v-for="category in categories"
                        :key="category.id"
                        :label="category.status === 'active' ? category.name : `${category.name}（已停用）`"
                        :value="category.id"
                      />
                    </el-select>
                  </el-form-item>

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

                  <el-form-item label="排序值">
                    <div class="sort-field">
                      <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
                      <span class="field-tip">值越小越靠前显示</span>
                    </div>
                  </el-form-item>
                </div>
              </div>
              </section>
            </el-tab-pane>

            <el-tab-pane name="media" label="图片维护">
              <section class="editor-section editor-media-panel">
                <div class="section-shell">
                  <div class="section-kicker">MEDIA</div>
                </div>
                <div class="editor-section-header">
                  <div>
                    <h3>图片管理</h3>
                    <p>上传图片后可直接拖拽排序，单击缩略图查看大图，第一张或封面图会优先用于列表展示。</p>
                  </div>
              </div>

              <div class="media-subsection image-manager">
                <div class="image-manager-header">
                  <div>
                    <h4>图片维护</h4>
                    <p>支持 JPG / PNG / WEBP，单张不超过 5MB。</p>
                  </div>
                  <span class="muted">{{ editorImages.length ? `当前 ${editorImages.length} 张` : '还没有图片' }}</span>
                </div>

                <div class="image-grid image-grid-editor">
                  <el-upload
                    ref="editorUploadRef"
                    :key="imageUploadKey"
                    class="image-upload-tile"
                    multiple
                    :auto-upload="false"
                    :show-file-list="false"
                    accept=".jpg,.jpeg,.png,.webp"
                    :on-change="handleEditorFileChange"
                  >
                    <div class="image-upload-tile-inner">
                      <el-icon class="upload-icon"><Picture /></el-icon>
                      <strong>添加图片</strong>
                      <span>点击选择多张图片</span>
                    </div>
                  </el-upload>

                  <article
                    v-for="image in editorImages"
                    :key="image.key"
                    class="image-thumb-card"
                    :class="{
                      cover: image.is_cover,
                      dragging: dragImageKey === image.key,
                      'drag-over': dragOverImageKey === image.key,
                    }"
                    draggable="true"
                    @dragstart="handleImageDragStart(image.key)"
                    @dragenter.prevent="handleImageDragEnter(image.key)"
                    @dragover.prevent
                    @dragend="handleImageDragEnd"
                    @drop.prevent="handleImageDrop(image.key)"
                  >
                    <div class="image-card-handle">
                      <el-icon><Sort /></el-icon>
                      <span>#{{ image.sort_order + 1 }}</span>
                    </div>

                    <el-image
                      :src="image.image_url"
                      fit="cover"
                      class="managed-image managed-image-thumb"
                      :preview-src-list="editorImages.map((item) => item.image_url)"
                      preview-teleported
                    >
                      <template #error>
                        <div class="cover-fallback">IMG</div>
                      </template>
                    </el-image>

                    <div class="image-thumb-badges">
                      <span v-if="image.is_cover" class="thumb-badge thumb-badge-cover">封面</span>
                      <span v-if="image.source === 'new'" class="thumb-badge thumb-badge-new">待上传</span>
                    </div>

                    <div class="image-thumb-toolbar">
                      <button
                        type="button"
                        class="thumb-icon-button"
                        :class="{ active: image.is_cover }"
                        :title="image.is_cover ? '当前封面' : '设为封面'"
                        @click.stop="setEditorCover(image.key)"
                      >
                        <el-icon><Star /></el-icon>
                      </button>
                      <button
                        type="button"
                        class="thumb-icon-button danger"
                        title="删除图片"
                        @click.stop="removeEditorImage(image.key)"
                      >
                        <el-icon><Delete /></el-icon>
                      </button>
                    </div>
                  </article>
                </div>
              </div>
              </section>
            </el-tab-pane>
          </el-tabs>
        </el-form>
      </div>
    </div>

    <div class="editor-footer">
      <span class="muted editor-footer-tip">保存后将同步更新列表展示与封面预览。</span>
      <div class="editor-footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" class="editor-save-button" :loading="saving" @click="saveProduct">保存商品</el-button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.product-editor-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.editor-page-header,
.editor-page-actions,
.editor-footer,
.editor-footer-actions,
.image-manager-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-page-header,
.editor-footer {
  justify-content: space-between;
}

.editor-page-header,
.editor-grid,
.editor-footer {
  width: min(1180px, 100%);
  margin: 0 auto;
}

.editor-page-header {
  align-items: flex-start;
  padding: 8px 4px 0;
}

.editor-kicker {
  display: inline-flex;
  align-items: center;
  margin-top: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 250, 244, 0.9);
  color: #9a7b61;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.editor-page-heading h1 {
  margin: 14px 0 8px;
  font-family: 'Fraunces', serif;
  font-size: 36px;
  color: #2f241a;
  letter-spacing: -0.02em;
}

.editor-page-heading p {
  margin: 0;
  color: #8d765f;
  line-height: 1.7;
  max-width: 640px;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  padding: 0 2px;
  background: transparent;
  color: #7d5535;
  font-weight: 600;
  cursor: pointer;
}

.editor-page-actions {
  padding: 10px 12px;
  border: 1px solid rgba(122, 92, 65, 0.1);
  border-radius: 20px;
  background: rgba(255, 251, 246, 0.82);
  box-shadow: 0 12px 28px rgba(99, 74, 53, 0.08);
}

.editor-grid {
  padding: 4px 0;
}

.editor-canvas {
  padding: 22px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  border-radius: 32px;
  background:
    radial-gradient(circle at top right, rgba(255, 246, 235, 0.95), transparent 28%),
    linear-gradient(180deg, rgba(255, 251, 246, 0.98), rgba(250, 245, 237, 0.95));
  box-shadow: 0 26px 60px rgba(107, 77, 50, 0.08);
}

.editor-tabs :deep(.el-tabs__header) {
  margin: 0 0 22px;
}

.editor-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.editor-tabs :deep(.el-tabs__nav-wrap) {
  padding: 6px;
  border-radius: 999px;
  background: rgba(246, 237, 227, 0.92);
}

.editor-tabs :deep(.el-tabs__nav) {
  gap: 6px;
}

.editor-tabs :deep(.el-tabs__item) {
  height: 42px;
  padding: 0 20px;
  border-radius: 999px;
  color: #8a755d;
  font-weight: 600;
}

.editor-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.editor-tabs :deep(.el-tabs__item.is-active) {
  color: #3d2b1f;
  background: #fff;
  box-shadow: 0 10px 20px rgba(99, 74, 53, 0.1);
}

.editor-section {
  position: relative;
  padding: 24px;
  border: 1px solid rgba(122, 92, 65, 0.1);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 252, 247, 0.94));
  box-shadow: 0 18px 42px rgba(99, 74, 53, 0.08);
}

.editor-section-header,
.inline-grid {
  display: grid;
}

.section-shell {
  margin-bottom: 14px;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(193, 137, 78, 0.12);
  color: #9f6841;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.editor-section-header {
  gap: 8px;
  margin-bottom: 22px;
}

.editor-section-header h3 {
  margin: 0;
  font-size: 24px;
  font-family: 'Fraunces', serif;
  color: #332419;
}

.editor-section-header p {
  margin: 0;
  color: #8a755d;
  font-size: 14px;
  line-height: 1.6;
}

.basic-form-layout {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.95fr);
  align-items: start;
}

.basic-form-main,
.basic-form-side {
  display: grid;
  gap: 16px;
}

.basic-form-main {
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, #fffdf9 0%, #fff8f0 100%);
  border: 1px solid rgba(122, 92, 65, 0.08);
}

.basic-form-side {
  padding: 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, #fdf6ee 0%, #faf0e3 100%);
  border: 1px solid rgba(193, 137, 78, 0.12);
}

.sort-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.field-tip {
  color: #907e6a;
  font-size: 12px;
  line-height: 1.5;
}

.editor-media-panel {
  margin-top: 0;
}

.media-subsection {
  padding: 18px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.96), rgba(255, 249, 240, 0.9));
}

.image-manager-header {
  margin-bottom: 14px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

.image-manager-header h4 {
  margin: 0;
  font-size: 15px;
  color: #3d2b1f;
}

.image-manager-header p {
  margin: 6px 0 0;
  color: #8a755d;
  font-size: 13px;
  line-height: 1.6;
}

.image-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.image-grid-editor {
  align-items: stretch;
}

.image-upload-tile,
.image-thumb-card {
  position: relative;
  min-height: 0;
}

.image-upload-tile :deep(.el-upload) {
  width: 100%;
  height: 100%;
  min-height: 148px;
}

.image-upload-tile-inner,
.image-thumb-card {
  border-radius: 18px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  background: #fffdfa;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.image-upload-tile-inner {
  height: 100%;
  min-height: 148px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #7d5535;
}

.image-upload-tile-inner strong,
.image-upload-tile-inner span {
  display: block;
}

.image-upload-tile-inner strong {
  font-size: 14px;
}

.image-upload-tile-inner span {
  font-size: 12px;
  color: #8a755d;
}

.image-thumb-card {
  overflow: hidden;
}

.image-thumb-card.cover {
  border-color: rgba(169, 127, 78, 0.42);
  box-shadow: 0 16px 28px rgba(117, 86, 53, 0.12);
}

.image-thumb-card.dragging {
  opacity: 0.72;
  transform: scale(0.98);
}

.image-thumb-card.drag-over {
  border-color: rgba(92, 61, 37, 0.34);
  box-shadow: 0 14px 28px rgba(90, 60, 47, 0.12);
}

.image-card-handle {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(50, 33, 22, 0.68);
  color: #fffaf6;
  font-size: 11px;
  cursor: grab;
}

.managed-image {
  width: 100%;
  aspect-ratio: 1 / 1;
  height: auto;
  display: block;
}

.managed-image-thumb {
  cursor: zoom-in;
}

.image-thumb-badges {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.thumb-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(50, 33, 22, 0.7);
  color: #fffaf6;
  font-size: 11px;
  line-height: 1;
}

.thumb-badge-cover {
  background: rgba(193, 137, 78, 0.88);
}

.thumb-badge-new {
  background: rgba(72, 118, 88, 0.84);
}

.image-thumb-toolbar {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.thumb-icon-button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(50, 33, 22, 0.72);
  color: #fffaf6;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.thumb-icon-button:hover {
  transform: translateY(-1px);
}

.thumb-icon-button.active {
  background: rgba(193, 137, 78, 0.92);
}

.thumb-icon-button.danger {
  background: rgba(172, 86, 76, 0.88);
}

.editor-save-button {
  min-width: 136px;
  height: 42px;
  border: 0;
  background: linear-gradient(135deg, #c68457 0%, #9d5c38 100%);
  box-shadow: 0 12px 24px rgba(157, 92, 56, 0.24);
}

.editor-save-button:hover,
.editor-save-button:focus {
  background: linear-gradient(135deg, #d18f62 0%, #a76440 100%);
}

.editor-footer {
  width: 100%;
  justify-content: space-between;
  padding: 12px 6px 0;
  border-top: 1px solid rgba(122, 92, 65, 0.08);
}

.editor-footer-tip {
  line-height: 1.5;
}

.muted {
  color: #907e6a;
  font-size: 13px;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  padding-bottom: 8px;
  color: #5b4330;
  font-size: 13px;
  font-weight: 700;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper),
:deep(.el-input-number) {
  border-radius: 16px;
  box-shadow: none;
  border: 1px solid rgba(122, 92, 65, 0.1);
  background: rgba(255, 252, 248, 0.96);
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 46px;
}

:deep(.el-textarea__inner) {
  padding: 14px 16px;
  line-height: 1.75;
  min-height: 220px;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus),
:deep(.el-select__wrapper.is-focused),
:deep(.el-input-number:hover) {
  border-color: rgba(193, 137, 78, 0.42);
  box-shadow: 0 0 0 4px rgba(193, 137, 78, 0.08);
}

:deep(.el-button:not(.editor-save-button)) {
  border-radius: 14px;
}

@media (max-width: 1100px) {
  .image-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .editor-page-header,
  .editor-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-page-actions,
  .editor-footer-actions {
    justify-content: flex-end;
  }

  .basic-form-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .editor-canvas {
    padding: 18px;
    border-radius: 24px;
  }

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
