<script setup lang="ts">
import { RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import { resolveMediaUrl } from '../../api/base'
import {
  fetchNotificationSettings,
  sendTestNotification,
  updateNotificationSettings,
} from '../../api/modules/notifications'
import { fetchProducts } from '../../api/modules/products'
import { fetchSettings, publishSettings, updateSettings } from '../../api/modules/settings'

type BannerLibraryItem = {
  product_name: string
  image_url: string
  preview_url: string
  original_name: string
  is_cover: boolean
}

const BANNER_LIBRARY_PAGE_SIZE = 50

const loading = ref(false)
const saving = ref(false)
const publishing = ref(false)
const notificationSaving = ref(false)
const notificationTesting = ref(false)
const bannerPickerVisible = ref(false)
const bannerLibraryLoading = ref(false)
const bannerLibraryLoaded = ref(false)
const bannerLibrary = ref<BannerLibraryItem[]>([])
const selectedBannerUrls = ref<string[]>([])
const form = reactive({
  shop_name: '',
  shop_intro: '',
  contact_intro: '',
  contact_phone: '',
  wechat_id: '',
  address: '',
  business_hours: '',
})
const settingsMeta = reactive({
  has_unpublished_changes: false,
  draft_updated_at: '',
  published_at: '',
})
const notificationForm = reactive({
  enabled: false,
  channel: 'wecom' as 'wecom' | 'feishu' | 'generic',
  webhook_url: '',
  message_prefix: 'YRFasion',
})

const extractErrorMessage = (error: unknown, fallback: string) => {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  return typeof detail === 'string' && detail.trim() ? detail : fallback
}

const formatMetaTime = (value: string | null) => {
  if (!value) {
    return '暂无'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', { hour12: false })
}

const normalizeBannerUrls = (urls: string[]) =>
  urls
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, list) => list.indexOf(item) === index)

const setSelectedBannerUrls = (urls: string[]) => {
  selectedBannerUrls.value = normalizeBannerUrls(urls)
}

const resolveBannerPreviewUrl = (url: string) => resolveMediaUrl(url) || url

const loadSettings = async () => {
  loading.value = true
  try {
    const [data, notificationData] = await Promise.all([fetchSettings(), fetchNotificationSettings()])
    form.shop_name = data.shop_name
    form.shop_intro = data.shop_intro
    form.contact_intro = data.contact_intro
    form.contact_phone = data.contact_phone
    form.wechat_id = data.wechat_id
    form.address = data.address
    form.business_hours = data.business_hours
    setSelectedBannerUrls(data.homepage_banner_urls)
    settingsMeta.has_unpublished_changes = data.has_unpublished_changes
    settingsMeta.draft_updated_at = formatMetaTime(data.draft_updated_at)
    settingsMeta.published_at = formatMetaTime(data.published_at)

    notificationForm.enabled = notificationData.enabled
    notificationForm.channel = notificationData.channel
    notificationForm.webhook_url = notificationData.webhook_url
    notificationForm.message_prefix = notificationData.message_prefix
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const data = await updateSettings({
      shop_name: form.shop_name.trim(),
      shop_intro: form.shop_intro.trim(),
      contact_intro: form.contact_intro.trim(),
      contact_phone: form.contact_phone.trim(),
      wechat_id: form.wechat_id.trim(),
      address: form.address.trim(),
      business_hours: form.business_hours.trim(),
      homepage_banner_urls: selectedBannerUrls.value,
    })
    settingsMeta.has_unpublished_changes = data.has_unpublished_changes
    settingsMeta.draft_updated_at = formatMetaTime(data.draft_updated_at)
    settingsMeta.published_at = formatMetaTime(data.published_at)
    ElMessage.success(data.has_unpublished_changes ? '草稿已保存，待发布' : '草稿与线上内容一致')
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '保存草稿失败'))
  } finally {
    saving.value = false
  }
}

const handlePublish = async () => {
  publishing.value = true
  try {
    const data = await publishSettings()
    settingsMeta.has_unpublished_changes = data.has_unpublished_changes
    settingsMeta.draft_updated_at = formatMetaTime(data.draft_updated_at)
    settingsMeta.published_at = formatMetaTime(data.published_at)
    ElMessage.success('店铺设置已发布')
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '发布失败'))
  } finally {
    publishing.value = false
  }
}

const loadBannerLibrary = async () => {
  if (bannerLibraryLoading.value || bannerLibraryLoaded.value) {
    return
  }

  bannerLibraryLoading.value = true
  try {
    const items: BannerLibraryItem[] = []
    const imageUrlSet = new Set<string>()
    let nextPage = 1
    let total = 0

    do {
      const result = await fetchProducts({
        page: nextPage,
        page_size: BANNER_LIBRARY_PAGE_SIZE,
      })
      total = result.total

      result.items.forEach((product) => {
        product.images.forEach((image) => {
          if (!image.image_url || imageUrlSet.has(image.image_url)) {
            return
          }

          imageUrlSet.add(image.image_url)
          items.push({
            product_name: product.name,
            image_url: image.raw_image_url || image.image_url,
            preview_url: image.image_url,
            original_name: image.original_name,
            is_cover: image.is_cover,
          })
        })
      })

      nextPage += 1
    } while ((nextPage - 1) * BANNER_LIBRARY_PAGE_SIZE < total)

    bannerLibrary.value = items
    bannerLibraryLoaded.value = true
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '加载图片墙失败'))
  } finally {
    bannerLibraryLoading.value = false
  }
}

const openBannerPicker = async () => {
  bannerPickerVisible.value = true
  await loadBannerLibrary()
}

const toggleBannerSelection = (imageUrl: string) => {
  const nextUrls = selectedBannerUrls.value.slice()
  const currentIndex = nextUrls.indexOf(imageUrl)
  if (currentIndex >= 0) {
    nextUrls.splice(currentIndex, 1)
  } else {
    nextUrls.push(imageUrl)
  }
  setSelectedBannerUrls(nextUrls)
}

const removeSelectedBanner = (imageUrl: string) => {
  setSelectedBannerUrls(selectedBannerUrls.value.filter((item) => item !== imageUrl))
}

const moveSelectedBanner = (imageUrl: string, offset: -1 | 1) => {
  const currentIndex = selectedBannerUrls.value.indexOf(imageUrl)
  const targetIndex = currentIndex + offset
  if (currentIndex < 0 || targetIndex < 0 || targetIndex >= selectedBannerUrls.value.length) {
    return
  }

  const nextUrls = selectedBannerUrls.value.slice()
  const [currentItem] = nextUrls.splice(currentIndex, 1)
  nextUrls.splice(targetIndex, 0, currentItem)
  setSelectedBannerUrls(nextUrls)
}

const clearSelectedBanners = () => {
  setSelectedBannerUrls([])
}

const saveNotificationSettings = async () => {
  if (notificationForm.enabled && !notificationForm.webhook_url.trim()) {
    ElMessage.warning('启用提醒时必须填写 Webhook 地址')
    return
  }

  notificationSaving.value = true
  try {
    await updateNotificationSettings({
      enabled: notificationForm.enabled,
      channel: notificationForm.channel,
      webhook_url: notificationForm.webhook_url.trim(),
      message_prefix: notificationForm.message_prefix.trim() || 'YRFasion',
    })
    ElMessage.success('提醒设置已保存')
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '提醒设置保存失败'))
  } finally {
    notificationSaving.value = false
  }
}

const sendNotificationProbe = async () => {
  notificationTesting.value = true
  try {
    const result = await sendTestNotification()
    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '测试提醒发送失败'))
  } finally {
    notificationTesting.value = false
  }
}

void loadSettings()
</script>

<template>
  <section class="mobile-page settings-page" v-loading="loading">
    <article class="mobile-card form-card">
      <div class="card-head">
        <h3>店铺资料</h3>
        <button class="icon-action" type="button" aria-label="刷新店铺资料" @click="loadSettings">
          <el-icon><RefreshRight /></el-icon>
        </button>
      </div>

      <div class="meta-grid">
        <span class="meta-chip">{{ settingsMeta.has_unpublished_changes ? '有未发布草稿' : '已发布内容最新' }}</span>
        <span class="meta-item">草稿：{{ settingsMeta.draft_updated_at }}</span>
        <span class="meta-item">发布：{{ settingsMeta.published_at }}</span>
      </div>

      <el-form label-position="top" class="mobile-form">
        <div class="field-grid">
          <el-form-item label="店铺名称">
            <el-input v-model="form.shop_name" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" placeholder="建议填写门店联系电话" />
          </el-form-item>
        </div>

        <div class="field-grid">
          <el-form-item label="微信号">
            <el-input v-model="form.wechat_id" placeholder="仅填写微信号本身" />
          </el-form-item>
          <el-form-item label="营业时间">
            <el-input v-model="form.business_hours" placeholder="例如：10:00-21:00" />
          </el-form-item>
        </div>

        <el-form-item label="门店地址">
          <el-input v-model="form.address" />
        </el-form-item>

        <el-form-item label="店铺介绍">
          <el-input v-model="form.shop_intro" type="textarea" :rows="5" />
        </el-form-item>

        <el-form-item label="留言反馈页文案">
          <el-input v-model="form.contact_intro" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
    </article>

    <article class="mobile-card banner-card">
      <div class="card-head">
        <h3>首页横幅</h3>
        <div class="inline-actions">
          <button class="ghost-action" type="button" @click="openBannerPicker">从图片墙选择</button>
          <button class="ghost-action" type="button" :disabled="!selectedBannerUrls.length" @click="clearSelectedBanners">清空</button>
        </div>
      </div>

      <p class="section-tip">已选 {{ selectedBannerUrls.length }} 张，顺序会直接影响小程序首页轮播。</p>

      <div v-if="selectedBannerUrls.length" class="selected-banner-list">
        <article v-for="(url, index) in selectedBannerUrls" :key="url" class="selected-banner-card">
          <img class="selected-banner-image" :src="resolveBannerPreviewUrl(url)" alt="" />
          <div class="selected-banner-copy">
            <strong>第 {{ index + 1 }} 张横幅</strong>
            <span>{{ url }}</span>
          </div>
          <div class="selected-banner-actions">
            <button class="action-chip" type="button" :disabled="index === 0" @click="moveSelectedBanner(url, -1)">前移</button>
            <button class="action-chip" type="button" :disabled="index === selectedBannerUrls.length - 1" @click="moveSelectedBanner(url, 1)">后移</button>
            <button class="action-chip danger" type="button" @click="removeSelectedBanner(url)">移除</button>
          </div>
        </article>
      </div>
      <div v-else class="compact-empty">还没有选择横幅图，可从商品图片墙中挑选。</div>
    </article>

    <article class="mobile-card notification-card">
      <div class="card-head">
        <h3>消息提醒</h3>
        <span class="meta-chip neutral">{{ notificationForm.enabled ? '已启用' : '未启用' }}</span>
      </div>

      <el-form label-position="top" class="mobile-form">
        <el-form-item label="提醒状态">
          <el-switch v-model="notificationForm.enabled" />
        </el-form-item>

        <el-form-item label="提醒通道">
          <el-segmented
            v-model="notificationForm.channel"
            :options="[
              { label: '企微', value: 'wecom' },
              { label: '飞书', value: 'feishu' },
              { label: '通用', value: 'generic' },
            ]"
          />
        </el-form-item>

        <el-form-item label="Webhook 地址">
          <el-input v-model="notificationForm.webhook_url" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item label="消息前缀">
          <el-input v-model="notificationForm.message_prefix" />
        </el-form-item>
      </el-form>

      <div class="notification-actions">
        <button class="mobile-action-button secondary" type="button" :disabled="notificationSaving" @click="saveNotificationSettings">
          {{ notificationSaving ? '保存中…' : '保存提醒' }}
        </button>
        <button class="mobile-action-button secondary" type="button" :disabled="notificationTesting" @click="sendNotificationProbe">
          {{ notificationTesting ? '发送中…' : '发送测试' }}
        </button>
      </div>
    </article>

    <div class="sticky-submit-bar mobile-card">
      <button class="mobile-action-button secondary" type="button" :disabled="saving" @click="saveSettings">
        {{ saving ? '保存中…' : '保存草稿' }}
      </button>
      <button class="mobile-action-button" type="button" :disabled="publishing || !settingsMeta.has_unpublished_changes" @click="handlePublish">
        {{ publishing ? '发布中…' : '发布设置' }}
      </button>
    </div>

    <el-dialog v-model="bannerPickerVisible" title="从图片墙选择横幅" width="94%" destroy-on-close align-center>
      <div class="picker-shell" v-loading="bannerLibraryLoading">
        <article
          v-for="item in bannerLibrary"
          :key="item.image_url"
          class="picker-card"
          :class="{ active: selectedBannerUrls.includes(item.image_url) }"
          role="button"
          tabindex="0"
          @click="toggleBannerSelection(item.image_url)"
          @keyup.enter="toggleBannerSelection(item.image_url)"
        >
          <img class="picker-card-image" :src="item.preview_url" alt="" />
          <div class="picker-card-copy">
            <strong>{{ item.product_name }}</strong>
            <span>{{ item.original_name }}</span>
          </div>
          <span class="picker-card-flag">{{ selectedBannerUrls.includes(item.image_url) ? '已选' : item.is_cover ? '封面' : '可选' }}</span>
        </article>
        <div v-if="!bannerLibraryLoading && !bannerLibrary.length" class="compact-empty">暂时没有可用商品图片。</div>
      </div>

      <template #footer>
        <div class="dialog-actions">
          <button class="mobile-action-button secondary" type="button" @click="bannerPickerVisible = false">关闭</button>
          <button class="mobile-action-button" type="button" @click="bannerPickerVisible = false">完成选择</button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.settings-page {
  gap: 12px;
}

.form-card,
.banner-card,
.notification-card,
.sticky-submit-bar {
  padding: 16px;
}

.meta-grid {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-chip,
.meta-item {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
}

.meta-chip {
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
  font-weight: 700;
}

.meta-chip.neutral {
  background: rgba(57, 76, 64, 0.08);
  color: #53625b;
}

.meta-item {
  background: rgba(255, 255, 255, 0.72);
  color: #5e6761;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head h3 {
  margin: 0;
  font-size: 18px;
  color: #232622;
}

.icon-action {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 16px;
  background: rgba(249, 249, 247, 0.96);
  color: #526059;
  box-shadow: 0 8px 18px rgba(25, 35, 31, 0.05);
}

.icon-action :deep(.el-icon) {
  font-size: 18px;
}

.inline-actions,
.notification-actions,
.dialog-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.inline-actions {
  width: min(100%, 220px);
}

.ghost-action,
.action-chip {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  background: rgba(249, 249, 247, 0.96);
  color: #3d4a43;
  font-weight: 600;
}

.section-tip {
  margin: 12px 0 0;
  color: #66706a;
  line-height: 1.6;
  font-size: 13px;
}

.mobile-form {
  margin-top: 14px;
}

.mobile-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.selected-banner-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selected-banner-card {
  padding: 12px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  display: grid;
  grid-template-columns: 78px 1fr;
  gap: 12px;
}

.selected-banner-image {
  width: 78px;
  height: 78px;
  border-radius: 16px;
  object-fit: cover;
}

.selected-banner-copy {
  min-width: 0;
}

.selected-banner-copy strong,
.selected-banner-copy span {
  display: block;
}

.selected-banner-copy strong {
  color: #272521;
}

.selected-banner-copy span {
  margin-top: 6px;
  color: #68716b;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-all;
}

.selected-banner-actions {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.action-chip.danger {
  color: #b8543c;
}

.compact-empty {
  padding: 22px 16px;
  border: 1px dashed rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  color: #717972;
  text-align: center;
  background: rgba(255, 255, 255, 0.66);
}

.sticky-submit-bar {
  position: sticky;
  bottom: calc(90px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.picker-shell {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 62vh;
  overflow: auto;
}

.picker-card {
  padding: 10px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  display: grid;
  grid-template-columns: 72px 1fr auto;
  align-items: center;
  gap: 12px;
}

.picker-card.active {
  border-color: rgba(47, 106, 88, 0.2);
  background: rgba(47, 106, 88, 0.06);
}

.picker-card-image {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  object-fit: cover;
}

.picker-card-copy {
  min-width: 0;
}

.picker-card-copy strong,
.picker-card-copy span {
  display: block;
}

.picker-card-copy strong {
  color: #272521;
  line-height: 1.35;
}

.picker-card-copy span {
  margin-top: 6px;
  color: #68716b;
  font-size: 12px;
  line-height: 1.5;
}

.picker-card-flag {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  color: #55645c;
  font-size: 12px;
  font-weight: 700;
}
</style>
