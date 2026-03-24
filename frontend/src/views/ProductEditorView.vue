<script setup lang="ts">
import { ArrowLeft, Delete, Picture, Plus, Sort, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'

import { createCategory, fetchCategories, type CategoryItem } from '../api/modules/categories'
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
const SUGGESTED_TAGS = ['春季', 'OODT', '简约', '休闲', '夏季', '穿搭', '日常']

const saving = ref(false)
const loading = ref(false)
const creatingCategory = ref(false)
const categories = ref<CategoryItem[]>([])
const editorUploadRef = ref<{ clearFiles: () => void } | null>(null)
const editorImages = ref<EditorImageItem[]>([])
const removedImageIds = ref<number[]>([])
const imageUploadKey = ref(0)
const dragImageKey = ref('')
const dragOverImageKey = ref('')
const tagInput = ref('')
const newCategoryName = ref('')
const initialSnapshot = ref('')
const allowLeave = ref(false)
const categoryCreatorVisible = ref(false)

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

const statusLabelMap: Record<ProductFormState['status'], string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}
const statusOptions = [
  {
    value: 'draft' as const,
    label: '草稿',
    description: '仅自己可见，不会出现在商品列表',
  },
  {
    value: 'published' as const,
    label: '已发布',
    description: '所有人可见，展示在商品列表中',
  },
  {
    value: 'archived' as const,
    label: '已归档',
    description: '从商品列表隐藏，但保留后台记录',
  },
]
const selectedCategoryName = computed(
  () => categories.value.find((category) => category.id === form.category_id)?.name ?? '未选择分类',
)
const currentStatusLabel = computed(() => statusLabelMap[form.status])
const remainingTagCount = computed(() => Math.max(TAG_MAX_COUNT - form.tags.length, 0))
const footerStatusHint = computed(() => {
  if (form.status === 'published') {
    return '商品将以已发布状态保存。'
  }
  if (form.status === 'archived') {
    return '商品将以归档状态保存。'
  }
  return '商品将保存为草稿状态。'
})
const editorProgress = computed(() => [
  {
    key: 'name',
    label: '商品名称',
    value: form.name.trim() ? '已填写' : '未填写',
    done: Boolean(form.name.trim()),
  },
  {
    key: 'category',
    label: '商品分类',
    value: form.category_id ? selectedCategoryName.value : '未选择',
    done: Boolean(form.category_id),
  },
  {
    key: 'images',
    label: '图片素材',
    value: `${editorImages.value.length} 张`,
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
  form.name = ''
  form.category_id = null
  form.description = ''
  form.tags = []
  form.status = 'draft'
  form.sort_order = 0
  tagInput.value = ''
  newCategoryName.value = ''
  categoryCreatorVisible.value = false
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

const toggleCategoryCreator = () => {
  categoryCreatorVisible.value = !categoryCreatorVisible.value
  if (!categoryCreatorVisible.value) {
    newCategoryName.value = ''
  }
}

const createCategoryFromEditor = async () => {
  const name = newCategoryName.value.trim()
  if (!name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  if (creatingCategory.value) {
    return
  }

  creatingCategory.value = true
  try {
    const createdCategory = await createCategory({
      name,
      status: 'active',
    })
    categories.value = await fetchCategories()
    form.category_id = createdCategory.id
    newCategoryName.value = ''
    categoryCreatorVisible.value = false
    ElMessage.success('分类已创建并选中')
  } finally {
    creatingCategory.value = false
  }
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
    return
  }
  if (!payload.category_id) {
    ElMessage.warning('请选择分类（必填）')
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

const saveProductWithStatus = async (status: ProductFormState['status']) => {
  form.status = status
  await saveProduct()
}

const showPreviewHint = () => {
  ElMessage.info('预览功能暂未开放')
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
    <header class="editor-shell editor-topbar">
      <div class="editor-topbar-main">
        <button class="back-button" type="button" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </button>
        <div class="editor-toolbar-meta">
          <span class="status-chip">{{ currentStatusLabel }}</span>
          <span class="editor-title-note">{{ hasPendingChanges ? '当前有未保存修改' : '表单已同步最新内容' }}</span>
        </div>
      </div>

      <div class="editor-topbar-actions">
        <el-button class="header-action-button" @click="showPreviewHint">预览</el-button>
        <el-button class="header-action-button" :loading="saving" @click="saveProductWithStatus('draft')">存为草稿</el-button>
        <el-button type="primary" class="editor-save-button" :loading="saving" @click="saveProduct">保存商品</el-button>
      </div>
    </header>

    <div class="editor-shell editor-layout">
      <main class="editor-main">
        <section class="editor-card">
          <div class="card-header">
            <h2>基本信息</h2>
          </div>

          <el-form label-position="top" class="editor-form">
            <el-form-item required class="editor-form-item">
              <template #label>
                商品名称
                <span class="required-mark">*</span>
              </template>
              <el-input
                v-model="form.name"
                placeholder="请输入商品名称，例如：永远喜欢这种随性慵懒的穿搭～"
              />
            </el-form-item>

            <el-form-item label="商品描述" class="editor-form-item">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="6"
                :maxlength="DESCRIPTION_MAX_LENGTH"
                placeholder="详细描述商品特点、风格、适用场景等..."
              />
              <div class="field-meta-row">
                <span>支持换行，推荐使用话题标签增加曝光度</span>
                <span>{{ form.description.length }} / {{ DESCRIPTION_MAX_LENGTH }}</span>
              </div>
            </el-form-item>
          </el-form>
        </section>

        <section class="editor-card">
          <div class="card-header card-header-split">
            <h2>
              商品图片
              <span class="required-mark">*</span>
            </h2>
            <div class="card-header-actions">
              <span class="section-count">{{ editorImages.length }} 张图片</span>
              <el-upload
                ref="editorUploadRef"
                :key="imageUploadKey"
                class="image-upload-trigger"
                multiple
                :auto-upload="false"
                :show-file-list="false"
                accept=".jpg,.jpeg,.png,.webp"
                :on-change="handleEditorFileChange"
              >
                <el-button class="image-upload-button" type="primary" plain>
                  <el-icon><Plus /></el-icon>
                  上传图片
                </el-button>
              </el-upload>
            </div>
          </div>

          <div class="image-panel">
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
              <div class="image-empty-illustration">
                <el-icon><Picture /></el-icon>
              </div>
              <strong>还没有上传图片</strong>
              <p>点击右上角上传图片，建议先放封面图，再补充细节图和搭配图。</p>
            </div>

            <div class="image-tip-box">
              <span class="image-tip-title">图片上传提示</span>
              <ul class="image-tip-list">
                <li>建议上传 2-9 张高清图片，第一张将作为封面</li>
                <li>支持 JPG、PNG、WEBP 格式，单张图片不超过 5MB</li>
                <li>建议图片尺寸为 800 x 800 像素以上</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="editor-card">
          <div class="card-header">
            <h2>标签与关键词</h2>
          </div>

          <div class="tag-editor">
            <label class="field-label">商品标签</label>
            <div class="tag-input-row">
              <el-input
                v-model="tagInput"
                placeholder="输入标签后按回车添加"
                @keyup.enter.prevent="appendTagFromInput"
                @blur="appendTagFromInput"
              />
              <el-button type="primary" class="tag-add-button" @click="appendTagFromInput">添加</el-button>
            </div>

            <div v-if="form.tags.length" class="tag-chip-list">
              <el-tag v-for="tag in form.tags" :key="tag" closable effect="plain" @close="removeTag(tag)">
                {{ tag }}
              </el-tag>
            </div>

            <div class="tag-suggestions">
              <span class="tag-suggestions-label">推荐标签：</span>
              <button
                v-for="tag in SUGGESTED_TAGS"
                :key="tag"
                type="button"
                class="suggestion-chip"
                @click="addSuggestedTag(tag)"
              >
                + {{ tag }}
              </button>
            </div>

            <span class="tag-helper">还可添加 {{ remainingTagCount }} 个标签</span>
          </div>
        </section>
      </main>

      <aside class="editor-sidebar">
        <section class="editor-card sidebar-card">
          <div class="card-header">
            <h2>保存前检查</h2>
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

        <section class="editor-card sidebar-card">
          <div class="card-header">
            <h2>商品设置</h2>
          </div>

          <el-form label-position="top" class="sidebar-form">
            <el-form-item required class="sidebar-form-item">
              <template #label>
                分类
                <span class="required-mark">*</span>
              </template>
              <div class="category-field">
                <el-select v-model="form.category_id" clearable placeholder="请选择分类">
                  <el-option
                    v-for="category in categories"
                    :key="category.id"
                    :label="category.status === 'active' ? category.name : `${category.name}（已停用）`"
                    :value="category.id"
                  />
                </el-select>

                <div class="category-actions">
                  <span class="field-tip">没有合适的分类时，可直接创建。</span>
                  <el-popover v-model:visible="categoryCreatorVisible" placement="bottom-end" :width="320" trigger="manual">
                    <div class="category-popover">
                      <div class="category-popover-header">
                        <strong>新建分类</strong>
                        <span>创建后会自动选中到当前商品</span>
                      </div>
                      <el-input
                        v-model="newCategoryName"
                        placeholder="输入新分类名称，例如：针织衫"
                        @keyup.enter.prevent="createCategoryFromEditor"
                      />
                      <div class="category-popover-actions">
                        <el-button @click="toggleCategoryCreator">取消</el-button>
                        <el-button type="primary" :loading="creatingCategory" @click="createCategoryFromEditor">
                          新建并选中
                        </el-button>
                      </div>
                    </div>
                    <template #reference>
                      <button type="button" class="category-inline-button" @click="toggleCategoryCreator">
                        <el-icon><Plus /></el-icon>
                        新建分类
                      </button>
                    </template>
                  </el-popover>
                </div>
              </div>
            </el-form-item>

            <div class="sidebar-field-block">
              <label class="field-label">发布状态</label>
              <div class="status-option-list">
                <button
                  v-for="option in statusOptions"
                  :key="option.value"
                  type="button"
                  class="status-option"
                  :class="{ active: form.status === option.value }"
                  @click="form.status = option.value"
                >
                  <span class="status-radio" :class="{ active: form.status === option.value }" />
                  <div class="status-option-copy">
                    <strong>{{ option.label }}</strong>
                    <span>{{ option.description }}</span>
                  </div>
                </button>
              </div>
            </div>

            <el-form-item label="排序值" class="sidebar-form-item">
              <div class="sort-field">
                <span class="field-tip">数值越大越靠前</span>
                <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
              </div>
            </el-form-item>
          </el-form>
        </section>

        <section class="editor-card sidebar-card image-guide-card">
          <div class="guide-icon">
            <el-icon><Picture /></el-icon>
          </div>
          <div class="guide-copy">
            <h3>图片优化建议</h3>
            <p>上传清晰的商品图片可以提升转化率，并让封面展示更稳定。</p>
            <el-button class="guide-action" @click="showPreviewHint">了解更多技巧</el-button>
          </div>
        </section>
      </aside>
    </div>

    <footer class="editor-shell editor-footer">
      <div class="editor-footer-copy">
        <span>保存后，{{ footerStatusHint }}</span>
      </div>
      <div class="editor-footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" class="editor-save-button" :loading="saving" @click="saveProduct">保存商品</el-button>
      </div>
    </footer>
  </section>
</template>

<style scoped>
.product-editor-page {
  --editor-bg: rgba(247, 244, 238, 0.94);
  --editor-card-bg: rgba(255, 255, 255, 0.92);
  --editor-border: rgba(115, 95, 67, 0.12);
  --editor-border-strong: rgba(177, 142, 95, 0.24);
  --editor-text: #2f271d;
  --editor-muted: #8b7d6d;
  --editor-primary: #a48a5d;
  --editor-primary-deep: #8f764d;
  --editor-primary-soft: rgba(164, 138, 93, 0.12);
  --editor-tip-bg: rgba(225, 237, 255, 0.72);
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 24px;
}

.editor-shell,
.editor-footer {
  width: min(1220px, 100%);
  margin: 0 auto;
}

.editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 0 4px;
}

.editor-topbar-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-width: 0;
}

.editor-toolbar-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px 0 0;
  border: 0;
  background: transparent;
  color: #6f6253;
  font-weight: 600;
  cursor: pointer;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--editor-primary-soft);
  color: var(--editor-primary-deep);
  font-size: 12px;
  font-weight: 700;
}

.editor-title-note {
  color: var(--editor-muted);
  font-size: 13px;
}

.editor-topbar-actions,
.editor-footer,
.editor-footer-actions,
.tag-input-row,
.category-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-topbar-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.header-action-button {
  border-radius: 12px;
}

.editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 320px);
  gap: 20px;
  align-items: start;
}

.editor-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.editor-sidebar {
  position: sticky;
  top: 20px;
  display: grid;
  gap: 16px;
}

.editor-card,
.editor-footer {
  border: 1px solid var(--editor-border);
  border-radius: 18px;
  background: var(--editor-card-bg);
  box-shadow: 0 12px 32px rgba(83, 67, 44, 0.06);
  backdrop-filter: blur(18px);
}

.editor-card {
  padding: 0;
  overflow: hidden;
}

.card-header {
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(115, 95, 67, 0.08);
}

.card-header h2 {
  margin: 0;
  color: var(--editor-text);
  font-size: 22px;
  font-weight: 700;
}

.card-header-split {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header-actions {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.section-count {
  color: var(--editor-muted);
  font-size: 12px;
}

.editor-form,
.sidebar-form,
.tag-editor,
.image-panel {
  padding: 18px 20px 20px;
}

.editor-form {
  display: grid;
  gap: 18px;
}

.editor-form :deep(.el-form-item),
.sidebar-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.editor-form :deep(.el-form-item__label),
.sidebar-form :deep(.el-form-item__label),
.field-label {
  margin-bottom: 8px;
  color: #5e4f3d;
  font-size: 13px;
  font-weight: 600;
}

.editor-form :deep(.el-input__wrapper),
.editor-form :deep(.el-textarea__inner),
.sidebar-form :deep(.el-select__wrapper),
.sidebar-form :deep(.el-input-number),
.tag-editor :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px rgba(115, 95, 67, 0.12);
  background: #fff;
}

.editor-form :deep(.el-input__wrapper.is-focus),
.editor-form :deep(.el-textarea__inner:focus),
.sidebar-form :deep(.el-select__wrapper.is-focused),
.sidebar-form :deep(.el-input-number:focus-within),
.tag-editor :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px rgba(164, 138, 93, 0.56),
    0 0 0 4px rgba(164, 138, 93, 0.1);
}

.progress-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 18px 20px 20px;
  list-style: none;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0;
}

.progress-item.done {
  color: var(--editor-text);
}

.progress-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: rgba(141, 125, 104, 0.42);
}

.progress-item.done .progress-dot {
  background: var(--editor-primary);
}

.progress-copy {
  display: grid;
  gap: 1px;
}

.progress-copy strong {
  color: #433626;
  font-size: 13px;
  font-weight: 600;
}

.progress-copy span {
  color: var(--editor-muted);
  font-size: 12px;
}

.field-meta-row,
.category-field,
.category-popover,
.sort-field,
.guide-copy {
  display: grid;
  gap: 10px;
}

.field-meta-row {
  margin-top: 8px;
  grid-template-columns: minmax(0, 1fr) auto;
  color: var(--editor-muted);
  font-size: 12px;
}

.category-field :deep(.el-select) {
  width: 100%;
}

.category-popover-header {
  display: grid;
  gap: 4px;
}

.category-popover-header strong {
  color: var(--editor-text);
  font-size: 14px;
}

.category-popover-header span {
  color: var(--editor-muted);
  font-size: 12px;
  line-height: 1.5;
}

.category-popover-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.category-inline-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--editor-primary-deep);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.sidebar-form {
  display: grid;
  gap: 16px;
}

.sidebar-field-block {
  display: grid;
  gap: 10px;
}

.status-option-list {
  display: grid;
  gap: 10px;
}

.status-option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(115, 95, 67, 0.12);
  border-radius: 14px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.status-option:hover {
  transform: translateY(-1px);
}

.status-option.active {
  border-color: var(--editor-border-strong);
  background: rgba(252, 249, 241, 0.96);
}

.status-radio {
  position: relative;
  width: 16px;
  height: 16px;
  margin-top: 2px;
  border: 1px solid rgba(141, 125, 104, 0.5);
  border-radius: 50%;
}

.status-radio.active::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  background: var(--editor-primary);
}

.status-option-copy {
  display: grid;
  gap: 4px;
}

.status-option-copy strong {
  color: var(--editor-text);
  font-size: 13px;
}

.status-option-copy span {
  color: var(--editor-muted);
  font-size: 12px;
  line-height: 1.6;
}

.field-tip,
.tag-helper {
  color: var(--editor-muted);
  font-size: 12px;
  line-height: 1.6;
}

.required-mark {
  margin-left: 4px;
  color: #d36a51;
  font-weight: 700;
}

.tag-editor {
  display: grid;
  gap: 12px;
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
  color: var(--editor-muted);
  font-size: 12px;
  font-weight: 600;
}

.suggestion-chip {
  border: 1px solid rgba(141, 125, 104, 0.18);
  border-radius: 999px;
  padding: 4px 10px;
  background: #f5f3ef;
  color: #6f6253;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.suggestion-chip:hover {
  border-color: var(--editor-border-strong);
  transform: translateY(-1px);
}

.tag-add-button {
  min-width: 74px;
  border-radius: 12px;
}

.image-panel {
  display: grid;
  gap: 14px;
}

.image-upload-trigger {
  display: inline-flex;
}

.image-upload-trigger :deep(.el-upload) {
  display: inline-flex;
}

.image-upload-button {
  min-width: 112px;
  height: 38px;
  border-radius: 12px;
  border-color: rgba(155, 131, 87, 0.16);
  background: rgba(252, 249, 241, 0.92);
  color: var(--editor-primary-deep);
  font-weight: 600;
}

.image-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.image-thumb-card,
.image-empty-state {
  border-radius: 14px;
  border: 1px solid rgba(115, 95, 67, 0.12);
  background: #fff;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.image-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  text-align: center;
  padding: 24px;
  border-style: dashed;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(250, 247, 241, 0.92));
}

.image-empty-illustration {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(180, 149, 98, 0.1);
  color: var(--editor-primary-deep);
}

.image-empty-illustration :deep(.el-icon) {
  font-size: 24px;
}

.image-empty-state strong {
  color: var(--editor-text);
  font-size: 16px;
}

.image-empty-state p {
  margin: 0;
  color: var(--editor-muted);
  font-size: 12px;
  line-height: 1.7;
  max-width: 320px;
}

.image-thumb-card {
  position: relative;
  overflow: hidden;
  min-height: 120px;
}

.image-thumb-card.cover {
  border-color: var(--editor-border-strong);
  box-shadow: 0 12px 24px rgba(126, 102, 63, 0.12);
}

.image-thumb-card.dragging {
  opacity: 0.72;
  transform: scale(0.98);
}

.image-thumb-card.drag-over {
  border-color: var(--editor-primary);
  box-shadow: 0 12px 20px rgba(126, 102, 63, 0.12);
}

.image-card-handle {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 7px;
  border-radius: 999px;
  background: rgba(58, 47, 34, 0.72);
  color: #fff;
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
  background: rgba(58, 47, 34, 0.72);
  color: #fff;
  font-size: 11px;
  line-height: 1;
}

.thumb-badge-cover {
  background: rgba(164, 138, 93, 0.92);
}

.thumb-badge-new {
  background: rgba(84, 132, 101, 0.9);
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
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(58, 47, 34, 0.78);
  color: #fff;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.thumb-icon-button:hover {
  transform: translateY(-1px);
}

.thumb-icon-button.active {
  background: rgba(164, 138, 93, 0.96);
}

.thumb-icon-button.danger {
  background: rgba(196, 98, 79, 0.9);
}

.cover-fallback {
  display: grid;
  place-items: center;
  height: 100%;
  color: var(--editor-muted);
  background: #f4efe7;
  font-weight: 700;
}

.image-tip-box {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid rgba(115, 95, 67, 0.08);
  border-radius: 12px;
  background: var(--editor-tip-bg);
}

.image-tip-title {
  color: #4f77c6;
  font-size: 12px;
  font-weight: 700;
}

.image-tip-list {
  display: grid;
  gap: 4px;
  margin: 0;
  padding-left: 18px;
  color: #4f77c6;
  font-size: 12px;
  line-height: 1.6;
}

.image-guide-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(233, 242, 255, 0.86), rgba(240, 246, 255, 0.92));
}

.guide-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(89, 136, 223, 0.16);
  color: #4f77c6;
}

.guide-copy h3 {
  margin: 0;
  color: var(--editor-text);
  font-size: 16px;
}

.guide-copy p {
  margin: 0;
  color: #5c6f8f;
  font-size: 12px;
  line-height: 1.7;
}

.guide-action {
  width: 100%;
  border-radius: 12px;
}

.editor-footer {
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: 16px;
}

.editor-save-button {
  min-width: 136px;
  height: 40px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #b49a6b 0%, #9b8357 100%);
  box-shadow: 0 10px 20px rgba(155, 131, 87, 0.24);
}

.editor-save-button:hover,
.editor-save-button:focus {
  background: linear-gradient(135deg, #bea577 0%, #a58a5d 100%);
}

:deep(.el-button:not(.editor-save-button)) {
  border-radius: 12px;
}

@media (max-width: 1120px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }

  .editor-topbar {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-topbar-main {
    justify-content: space-between;
  }

  .editor-sidebar {
    position: static;
  }

  .image-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .product-editor-page {
    gap: 18px;
  }

  .editor-topbar-main {
    align-items: flex-start;
  }

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .editor-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-footer-actions,
  .editor-topbar-actions,
  .tag-input-row {
    justify-content: stretch;
  }

  .editor-footer-actions :deep(.el-button),
  .editor-topbar-actions :deep(.el-button),
  .tag-input-row :deep(.el-button) {
    flex: 1;
  }
}

@media (max-width: 560px) {
  .card-header,
  .editor-form,
  .sidebar-form,
  .tag-editor,
  .image-panel,
  .progress-list,
  .editor-footer,
  .image-guide-card {
    padding-left: 16px;
    padding-right: 16px;
  }

  .card-header-split,
  .field-meta-row,
  .category-actions {
    grid-template-columns: 1fr;
    display: grid;
    justify-items: start;
  }

  .card-header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tag-input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .image-guide-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 420px) {
  .image-grid {
    grid-template-columns: 1fr;
  }
}
</style>
