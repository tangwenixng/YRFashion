<script setup lang="ts">
import { ArrowLeft, Delete, InfoFilled, Picture, Sort, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'

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
  tags: string[]
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

const DESCRIPTION_MAX_LENGTH = 500
const TAG_MAX_COUNT = 8
const TAG_MAX_LENGTH = 16
const SUGGESTED_TAGS = ['通勤', '春季', '夏季', '秋冬', '日常', '约会']

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
const tagInput = ref('')
const initialSnapshot = ref('')
const allowLeave = ref(false)

const form = reactive<ProductFormState>({
  name: '',
  category_id: null,
  description: '',
  tags: [],
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
const statusLabelMap: Record<ProductFormState['status'], string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}
const selectedCategoryName = computed(
  () => categories.value.find((category) => category.id === form.category_id)?.name ?? '未选择分类',
)
const currentStatusLabel = computed(() => statusLabelMap[form.status])
const remainingTagCount = computed(() => Math.max(TAG_MAX_COUNT - form.tags.length, 0))
const editorProgress = computed(() => [
  {
    key: 'name',
    label: '商品名称',
    value: form.name.trim() ? '已填写' : '待填写',
    done: Boolean(form.name.trim()),
  },
  {
    key: 'category',
    label: '分类归属',
    value: form.category_id ? selectedCategoryName.value : '待选择',
    done: Boolean(form.category_id),
  },
  {
    key: 'images',
    label: '图片素材',
    value: editorImages.value.length ? `${editorImages.value.length} 张` : '暂未添加',
    done: Boolean(editorImages.value.length),
  },
])

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
  allowLeave.value = false
  editorActiveTab.value = 'basic'
  form.name = ''
  form.category_id = null
  form.description = ''
  form.tags = []
  form.status = 'draft'
  form.sort_order = 0
  tagInput.value = ''
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
    form.tags = [...product.tags]
    form.status = product.status
    form.sort_order = product.sort_order
    normalizeEditorImages(product.images.map(toEditorImage))
    markSnapshot()
    return
  } catch (error) {
    ElMessage.error(isEditing.value ? '商品加载失败' : '初始化失败')
    if (isEditing.value) {
      void router.push('/products')
    }
  } finally {
    if (!productId.value) {
      markSnapshot()
    }
    loading.value = false
  }
}

const buildPayload = () => ({
  name: form.name.trim(),
  category_id: form.category_id,
  description: form.description.trim(),
  tags: [...form.tags],
  status: form.status,
  sort_order: form.sort_order,
})

const normalizeTag = (value: string) => value.trim().replace(/\s+/g, ' ')

const addTag = (rawTag: string) => {
  const tag = normalizeTag(rawTag)
  if (!tag) {
    return
  }
  if (tag.length > TAG_MAX_LENGTH) {
    ElMessage.warning(`单个标签不超过 ${TAG_MAX_LENGTH} 个字`)
    return
  }
  if (form.tags.includes(tag)) {
    return
  }
  if (form.tags.length >= TAG_MAX_COUNT) {
    ElMessage.warning(`最多添加 ${TAG_MAX_COUNT} 个标签`)
    return
  }
  form.tags = form.tags.concat(tag)
}

const appendTagFromInput = () => {
  if (!tagInput.value.trim()) {
    return
  }
  addTag(tagInput.value)
  tagInput.value = ''
}

const removeTag = (tag: string) => {
  form.tags = form.tags.filter((item) => item !== tag)
}

const addSuggestedTag = (tag: string) => {
  addTag(tag)
}

const editorSnapshot = () =>
  JSON.stringify({
    name: form.name.trim(),
    category_id: form.category_id,
    description: form.description,
    tags: [...form.tags],
    status: form.status,
    sort_order: form.sort_order,
    image_keys: editorImages.value.map((item) => item.key),
    image_ids: editorImages.value.map((item) => item.id),
    image_cover: editorImages.value.map((item) => item.is_cover),
    image_sort: editorImages.value.map((item) => item.sort_order),
    image_source: editorImages.value.map((item) => item.source),
    removed: [...removedImageIds.value].sort((a, b) => a - b),
  })

const markSnapshot = () => {
  initialSnapshot.value = editorSnapshot()
}

const hasPendingChanges = computed(() => {
  if (!initialSnapshot.value) {
    return false
  }
  return editorSnapshot() !== initialSnapshot.value
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
    ElMessage.warning('请填写商品名称（必填）')
    editorActiveTab.value = 'basic'
    return
  }
  if (!payload.category_id) {
    ElMessage.warning('请选择分类（必填）')
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
    allowLeave.value = true
    void router.push('/products')
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  if (allowLeave.value || !hasPendingChanges.value) {
    void router.push('/products')
    return
  }
  void ElMessageBox.confirm('当前有未保存修改，确认离开吗？', '离开确认', {
    type: 'warning',
    confirmButtonText: '离开',
    cancelButtonText: '继续编辑',
  })
    .then(() => {
      allowLeave.value = true
      void router.push('/products')
    })
    .catch(() => {})
}

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (allowLeave.value || !hasPendingChanges.value) {
    return
  }
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave((_to, _from, next) => {
  if (allowLeave.value || !hasPendingChanges.value) {
    next()
    return
  }
  void ElMessageBox.confirm('当前有未保存修改，确认离开吗？', '离开确认', {
    type: 'warning',
    confirmButtonText: '离开',
    cancelButtonText: '继续编辑',
  })
    .then(() => {
      allowLeave.value = true
      next()
    })
    .catch(() => next(false))
})

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  resetEditorImages()
})

watch(
  () => route.fullPath,
  () => {
    void loadCategoriesAndProduct()
  },
  { immediate: true },
)
</script>

<template>
  <section class="product-editor-page" v-loading="loading">
    <div class="editor-page-header">
      <div class="editor-page-heading">
        <button class="back-button" type="button" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </button>
        <span class="editor-kicker">{{ isEditing ? 'PRODUCT EDITOR' : 'PRODUCT CREATE' }}</span>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageSubtitle }}</p>
      </div>

      <div class="editor-page-actions">
        <div class="header-chip-row">
          <span class="header-chip">{{ currentStatusLabel }}</span>
          <span class="header-chip subtle">{{ editorImages.length ? `${editorImages.length} 张图片` : '未添加图片' }}</span>
          <span v-if="hasPendingChanges" class="unsaved-indicator">未保存修改</span>
        </div>

        <div class="header-action-row">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" class="editor-save-button" :loading="saving" @click="saveProduct">保存商品</el-button>
        </div>
      </div>
    </div>

    <div class="editor-workspace">
      <div class="editor-main">
        <div class="editor-canvas">
          <el-form label-position="top">
            <el-tabs v-model="editorActiveTab" class="editor-tabs">
              <el-tab-pane name="basic" label="基本信息">
                <section class="editor-section">
                  <div class="editor-section-header">
                    <div>
                      <span class="section-kicker">基础信息</span>
                      <h3>先完成商品内容，再决定展示方式</h3>
                      <p>标题和描述负责表达商品本身，分类、状态和排序在右侧统一管理，减少填写时的视觉干扰。</p>
                    </div>
                  </div>

                  <div class="basic-form-stack">
                    <el-form-item required class="field-block field-block-hero">
                      <template #label>
                        商品名称
                        <span class="required-mark">*</span>
                      </template>
                      <el-input v-model="form.name" placeholder="例如：羊毛大衣" />
                    </el-form-item>

                    <el-form-item label="描述" class="field-block">
                      <el-input
                        v-model="form.description"
                        type="textarea"
                        :rows="5"
                        :maxlength="DESCRIPTION_MAX_LENGTH"
                        placeholder="用于详情页展示穿搭亮点、面料与场景。"
                      />
                      <div class="field-counter">{{ form.description.length }} / {{ DESCRIPTION_MAX_LENGTH }}</div>
                    </el-form-item>

                    <div class="basic-tips-grid">
                      <article class="info-tile">
                        <span class="info-tile-label">详情展示</span>
                        <strong>描述建议控制在 2 到 4 句</strong>
                        <p>优先写版型、面料、季节和适用场景，避免把标签内容重复写进描述。</p>
                      </article>
                      <article class="info-tile">
                        <span class="info-tile-label">封面逻辑</span>
                        <strong>首张或手动设置的封面优先用于列表</strong>
                        <p>图片维护区支持拖拽排序，保存后会同步更新封面预览与后台列表顺序。</p>
                      </article>
                    </div>
                  </div>
                </section>
              </el-tab-pane>

              <el-tab-pane name="media" label="图片维护">
                <section class="editor-section editor-media-panel">
                  <div class="editor-section-header editor-section-header-split">
                    <div>
                      <span class="section-kicker">图片管理</span>
                      <h3>把上传入口和整理动作分开</h3>
                      <p>先补充素材，再拖拽调整顺序；封面图会优先用于列表和首页等关键位置展示。</p>
                    </div>
                    <span class="section-meta">{{ editorImages.length ? `共 ${editorImages.length} 张图片` : '还没有图片' }}</span>
                  </div>

                  <div class="media-layout">
                    <section class="media-panel media-upload-panel">
                      <div class="media-panel-heading">
                        <h4>上传图片</h4>
                        <p>支持 JPG / PNG / WEBP，单张不超过 5MB。</p>
                      </div>

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
                          <span>点击后可连续选择多张图片</span>
                        </div>
                      </el-upload>
                    </section>

                    <section class="media-panel media-library-panel">
                      <div class="image-manager-header">
                        <div>
                          <h4>图片顺序与封面</h4>
                          <p>
                            {{
                              editorImages.length
                                ? '拖动卡片调整顺序，单击星标设置封面。'
                                : '上传图片后可在这里完成顺序整理和封面设置。'
                            }}
                          </p>
                        </div>
                        <span class="muted">{{ editorImages.length ? `当前 ${editorImages.length} 张` : '等待上传' }}</span>
                      </div>

                      <div v-if="editorImages.length" class="image-grid image-grid-editor">
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

                      <div v-else class="image-empty-state">
                        <strong>还没有图片</strong>
                        <p>先在左侧上传素材，随后即可拖拽排序并选择封面图。</p>
                      </div>
                    </section>
                  </div>
                </section>
              </el-tab-pane>
            </el-tabs>
          </el-form>
        </div>
      </div>

      <aside class="editor-sidebar">
        <section class="sidebar-panel">
          <div class="sidebar-panel-header">
            <span class="sidebar-kicker">编辑进度</span>
            <h3>保存前检查</h3>
            <p>这三个信息会直接影响商品是否能顺利上架与展示。</p>
          </div>

          <ul class="progress-list">
            <li v-for="item in editorProgress" :key="item.key" class="progress-item" :class="{ done: item.done }">
              <span class="progress-dot" />
              <div class="progress-copy">
                <strong>{{ item.label }}</strong>
                <span>{{ item.value }}</span>
              </div>
            </li>
          </ul>
        </section>

        <section class="sidebar-panel">
          <div class="sidebar-panel-header">
            <span class="sidebar-kicker">发布设置</span>
            <h3>控制展示归属</h3>
          </div>

          <el-form label-position="top" class="sidebar-form">
            <el-form-item required>
              <template #label>
                分类
                <span class="required-mark">*</span>
              </template>
              <el-select v-model="form.category_id" clearable placeholder="请选择分类">
                <el-option
                  v-for="category in categories"
                  :key="category.id"
                  :label="category.status === 'active' ? category.name : `${category.name}（已停用）`"
                  :value="category.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <template #label>
                排序值
                <el-tooltip content="值越小越靠前，支持直接输入或点击步进" placement="top">
                  <el-icon class="hint-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </template>
              <div class="sort-field">
                <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
                <span class="field-tip">值越小越靠前显示</span>
              </div>
            </el-form-item>
          </el-form>
        </section>

        <section class="sidebar-panel">
          <div class="sidebar-panel-header">
            <span class="sidebar-kicker">标签维护</span>
            <h3>补充检索关键词</h3>
            <p>最多 {{ TAG_MAX_COUNT }} 个标签，建议保留季节、风格与场景信息。</p>
          </div>

          <div class="tag-editor">
            <div v-if="form.tags.length" class="tag-chip-list">
              <el-tag v-for="tag in form.tags" :key="tag" closable size="small" effect="plain" @close="removeTag(tag)">
                {{ tag }}
              </el-tag>
            </div>
            <el-input
              v-model="tagInput"
              placeholder="输入标签后回车，如：通勤"
              @keyup.enter.prevent="appendTagFromInput"
              @blur="appendTagFromInput"
            />
            <div class="tag-suggestions">
              <span class="tag-suggestions-label">推荐</span>
              <button
                v-for="tag in SUGGESTED_TAGS"
                :key="tag"
                type="button"
                class="suggestion-chip"
                @click="addSuggestedTag(tag)"
              >
                {{ tag }}
              </button>
            </div>
            <span class="tag-helper">还可添加 {{ remainingTagCount }} 个标签</span>
          </div>
        </section>
      </aside>
    </div>

    <div class="editor-footer">
      <div class="editor-footer-copy">
        <strong>保存后会同步更新商品列表</strong>
        <p class="editor-footer-tip">封面图、排序值和发布状态会立即影响后台和前台展示。</p>
      </div>
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
  gap: 24px;
  padding-bottom: 18px;
}

.editor-page-header,
.editor-workspace,
.editor-footer {
  width: min(1240px, 100%);
  margin: 0 auto;
}

.editor-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 6px 4px 0;
}

.editor-page-heading {
  min-width: 0;
}

.editor-kicker,
.section-kicker,
.sidebar-kicker {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.editor-kicker {
  margin-top: 14px;
  padding: 6px 10px;
  background: rgba(255, 250, 244, 0.9);
  color: #9a7b61;
}

.editor-page-heading h1 {
  margin: 14px 0 8px;
  font-family: 'Fraunces', serif;
  font-size: clamp(32px, 4vw, 40px);
  color: #2f241a;
  letter-spacing: -0.03em;
}

.editor-page-heading p {
  margin: 0;
  max-width: 700px;
  color: #7c6855;
  line-height: 1.75;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px;
  border: 0;
  background: transparent;
  color: #7d5535;
  font-weight: 600;
  cursor: pointer;
}

.editor-page-actions {
  display: grid;
  gap: 12px;
  min-width: 320px;
  padding: 16px;
  border: 1px solid rgba(122, 92, 65, 0.1);
  border-radius: 24px;
  background: rgba(255, 251, 246, 0.88);
  box-shadow: 0 20px 44px rgba(99, 74, 53, 0.08);
}

.header-chip-row,
.header-action-row,
.editor-footer,
.editor-footer-actions,
.image-manager-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-chip-row {
  flex-wrap: wrap;
}

.header-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(139, 94, 60, 0.12);
  color: #6b4526;
  font-size: 12px;
  font-weight: 700;
}

.header-chip.subtle {
  background: rgba(108, 89, 68, 0.08);
  color: #7a6551;
}

.header-action-row {
  justify-content: flex-end;
}

.unsaved-indicator {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(172, 86, 76, 0.12);
  color: #9f473d;
  font-size: 12px;
  font-weight: 700;
}

.editor-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.68fr) minmax(320px, 0.82fr);
  gap: 20px;
  align-items: start;
}

.editor-main,
.editor-sidebar {
  min-width: 0;
}

.editor-canvas,
.sidebar-panel,
.editor-footer {
  border: 1px solid rgba(122, 92, 65, 0.09);
  background: rgba(255, 251, 246, 0.88);
  box-shadow: 0 22px 52px rgba(99, 74, 53, 0.07);
  backdrop-filter: blur(16px);
}

.editor-canvas {
  padding: 24px;
  border-radius: 30px;
}

.editor-tabs :deep(.el-tabs__header) {
  margin: 0 0 22px;
}

.editor-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.editor-tabs :deep(.el-tabs__nav-wrap) {
  padding: 6px;
  border-radius: 18px;
  background: rgba(245, 237, 228, 0.9);
}

.editor-tabs :deep(.el-tabs__item) {
  height: 42px;
  padding: 0 18px;
  border-radius: 14px;
  color: #876d56;
  font-weight: 600;
}

.editor-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.editor-tabs :deep(.el-tabs__item.is-active) {
  color: #332419;
  background: #fffdfa;
  box-shadow: 0 10px 22px rgba(99, 74, 53, 0.08);
}

.editor-tabs :deep(.el-form-item) {
  margin-bottom: 0;
}

.editor-tabs :deep(.el-form-item__label),
.sidebar-form :deep(.el-form-item__label) {
  margin-bottom: 8px;
  color: #4b3625;
  font-weight: 600;
}

.editor-tabs :deep(.el-input__wrapper),
.editor-tabs :deep(.el-textarea__inner),
.editor-tabs :deep(.el-select__wrapper),
.sidebar-form :deep(.el-input__wrapper),
.sidebar-form :deep(.el-select__wrapper),
.sidebar-form :deep(.el-input-number) {
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px rgba(122, 92, 65, 0.1);
  background: rgba(255, 255, 255, 0.96);
}

.editor-tabs :deep(.el-input__wrapper.is-focus),
.editor-tabs :deep(.el-textarea__inner:focus),
.editor-tabs :deep(.el-select__wrapper.is-focused),
.sidebar-form :deep(.el-input__wrapper.is-focus),
.sidebar-form :deep(.el-select__wrapper.is-focused),
.sidebar-form :deep(.el-input-number:focus-within) {
  box-shadow:
    inset 0 0 0 1px rgba(139, 94, 60, 0.5),
    0 0 0 4px rgba(139, 94, 60, 0.08);
}

.editor-section {
  padding: 28px;
  border-radius: 26px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 251, 246, 0.94));
}

.editor-section-header {
  display: grid;
  gap: 10px;
  margin-bottom: 24px;
}

.editor-section-header-split {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.section-kicker,
.sidebar-kicker {
  margin-bottom: 8px;
  padding: 5px 10px;
  background: rgba(193, 137, 78, 0.12);
  color: #9f6841;
}

.editor-section-header h3,
.sidebar-panel-header h3 {
  margin: 0;
  font-family: 'Fraunces', serif;
  color: #332419;
  letter-spacing: -0.02em;
}

.editor-section-header h3 {
  font-size: 28px;
}

.editor-section-header p,
.sidebar-panel-header p {
  margin: 8px 0 0;
  color: #86725f;
  line-height: 1.7;
}

.section-meta {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(244, 233, 220, 0.86);
  color: #6f5842;
  font-size: 13px;
  font-weight: 700;
}

.basic-form-stack {
  display: grid;
  gap: 18px;
}

.field-block {
  padding: 18px 18px 16px;
  border-radius: 22px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  background: rgba(255, 252, 248, 0.9);
}

.field-block-hero {
  padding: 20px;
  background: linear-gradient(180deg, rgba(255, 252, 248, 0.98), rgba(255, 247, 237, 0.94));
}

.basic-tips-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-tile {
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  background: rgba(249, 241, 231, 0.7);
}

.info-tile-label {
  display: inline-flex;
  margin-bottom: 8px;
  color: #9d6f47;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.info-tile strong {
  display: block;
  color: #38291d;
  font-size: 15px;
}

.info-tile p {
  margin: 8px 0 0;
  color: #7b6651;
  font-size: 13px;
  line-height: 1.65;
}

.editor-sidebar {
  position: sticky;
  top: 20px;
  display: grid;
  gap: 16px;
}

.sidebar-panel {
  padding: 20px;
  border-radius: 24px;
}

.sidebar-panel-header {
  margin-bottom: 16px;
}

.sidebar-panel-header h3 {
  font-size: 24px;
}

.sidebar-form {
  display: grid;
  gap: 16px;
}

.progress-list {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(250, 243, 235, 0.84);
  border: 1px solid rgba(122, 92, 65, 0.08);
}

.progress-item.done {
  background: rgba(240, 248, 242, 0.94);
}

.progress-dot {
  width: 11px;
  height: 11px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: rgba(165, 109, 61, 0.28);
}

.progress-item.done .progress-dot {
  background: #4e8a61;
  box-shadow: 0 0 0 6px rgba(78, 138, 97, 0.12);
}

.progress-copy {
  display: grid;
  gap: 2px;
}

.progress-copy strong {
  color: #37291d;
  font-size: 14px;
}

.progress-copy span {
  color: #7e6a57;
  font-size: 13px;
}

.sort-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.field-tip,
.field-counter,
.tag-helper,
.muted {
  color: #907e6a;
  font-size: 12px;
  line-height: 1.6;
}

.field-counter {
  margin-top: 8px;
  text-align: right;
}

.tag-helper {
  display: inline-flex;
}

.required-mark {
  margin-left: 4px;
  color: #ad4d3f;
  font-weight: 700;
}

.hint-icon {
  margin-left: 6px;
  color: #987455;
  font-size: 14px;
  vertical-align: middle;
}

.tag-editor {
  display: grid;
  gap: 10px;
}

.tag-chip-list {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-suggestions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-suggestions-label {
  color: #9a7b61;
  font-size: 12px;
  font-weight: 700;
}

.suggestion-chip {
  border: 1px solid rgba(157, 107, 74, 0.2);
  border-radius: 999px;
  padding: 4px 10px;
  background: rgba(255, 248, 240, 0.95);
  color: #7b563b;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.suggestion-chip:hover {
  border-color: rgba(157, 107, 74, 0.42);
  transform: translateY(-1px);
}

.media-layout {
  display: grid;
  gap: 18px;
}

.media-panel {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(122, 92, 65, 0.08);
  background: rgba(255, 252, 248, 0.9);
}

.media-panel-heading h4,
.image-manager-header h4 {
  margin: 0;
  color: #3d2b1f;
  font-size: 16px;
}

.media-panel-heading p,
.image-manager-header p,
.image-empty-state p {
  margin: 6px 0 0;
  color: #8a755d;
  font-size: 13px;
  line-height: 1.65;
}

.image-manager-header {
  margin-bottom: 14px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

.image-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.image-upload-tile {
  display: block;
}

.image-upload-tile :deep(.el-upload) {
  width: 100%;
  min-height: 168px;
}

.image-upload-tile-inner,
.image-thumb-card,
.image-empty-state {
  border-radius: 20px;
  border: 1px solid rgba(122, 92, 65, 0.12);
  background: #fffdfa;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.image-upload-tile-inner {
  min-height: 168px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(180deg, rgba(255, 252, 248, 1), rgba(252, 244, 235, 0.98));
  color: #7d5535;
}

.upload-icon {
  font-size: 28px;
}

.image-upload-tile-inner strong {
  font-size: 15px;
}

.image-upload-tile-inner span {
  color: #8a755d;
  font-size: 12px;
}

.image-empty-state {
  display: grid;
  place-items: center;
  min-height: 180px;
  text-align: center;
  padding: 20px;
}

.image-empty-state strong {
  color: #3d2b1f;
  font-size: 16px;
}

.image-grid-editor {
  align-items: stretch;
}

.image-thumb-card {
  position: relative;
  overflow: hidden;
  min-height: 0;
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
  top: 10px;
  left: 10px;
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
  top: 10px;
  right: 10px;
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
  background: rgba(193, 137, 78, 0.9);
}

.thumb-badge-new {
  background: rgba(72, 118, 88, 0.86);
}

.image-thumb-toolbar {
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 10px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.thumb-icon-button {
  width: 34px;
  height: 34px;
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
  background: rgba(193, 137, 78, 0.94);
}

.thumb-icon-button.danger {
  background: rgba(172, 86, 76, 0.9);
}

.cover-fallback {
  display: grid;
  place-items: center;
  height: 100%;
  color: #8a755d;
  background: rgba(248, 239, 229, 0.86);
  font-weight: 700;
}

.editor-footer {
  justify-content: space-between;
  padding: 18px 20px;
  border-radius: 24px;
}

.editor-footer-copy strong {
  display: block;
  color: #34261b;
  font-size: 15px;
}

.editor-footer-tip {
  margin: 6px 0 0;
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

:deep(.el-button:not(.editor-save-button)) {
  border-radius: 14px;
}

@media (max-width: 1120px) {
  .editor-workspace {
    grid-template-columns: 1fr;
  }

  .editor-page-header {
    flex-direction: column;
  }

  .editor-page-actions {
    width: 100%;
    min-width: 0;
  }

  .editor-sidebar {
    position: static;
  }

  .image-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .product-editor-page {
    gap: 18px;
  }

  .editor-canvas,
  .sidebar-panel,
  .editor-footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .editor-section {
    padding: 20px;
  }

  .editor-section-header-split {
    grid-template-columns: 1fr;
  }

  .basic-tips-grid {
    grid-template-columns: 1fr;
  }

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .editor-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-footer-actions,
  .header-action-row {
    justify-content: stretch;
  }

  .editor-footer-actions :deep(.el-button),
  .header-action-row :deep(.el-button) {
    flex: 1;
  }
}

@media (max-width: 560px) {
  .editor-canvas {
    padding: 16px;
  }

  .editor-page-actions,
  .sidebar-panel,
  .editor-footer {
    padding: 14px;
  }

  .editor-section {
    padding: 16px;
  }

  .field-block,
  .media-panel,
  .info-tile {
    padding: 14px;
  }

  .image-grid {
    grid-template-columns: 1fr;
  }
}
</style>
