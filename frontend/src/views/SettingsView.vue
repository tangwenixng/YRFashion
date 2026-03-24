<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  fetchNotificationSettings,
  sendTestNotification,
  updateNotificationSettings,
} from '../api/modules/notifications'
import { fetchProducts } from '../api/modules/products'
import { fetchSettings, publishSettings, updateSettings } from '../api/modules/settings'

type BannerLibraryItem = {
  product_id: number
  product_name: string
  image_url: string
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
  homepage_banner_text: '',
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

const normalizeBannerUrls = (urls: string[]) => {
  return urls
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, list) => list.indexOf(item) === index)
}

const syncBannerText = () => {
  form.homepage_banner_text = selectedBannerUrls.value.join('\n')
}

const setSelectedBannerUrls = (urls: string[]) => {
  selectedBannerUrls.value = normalizeBannerUrls(urls)
  syncBannerText()
}

const loadSettings = async () => {
  loading.value = true
  try {
    const [data, notificationData] = await Promise.all([
      fetchSettings(),
      fetchNotificationSettings(),
    ])
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
    ElMessage.success(data.has_unpublished_changes ? '草稿已保存，尚未发布' : '草稿与已发布内容一致')
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
            product_id: product.id,
            product_name: product.name,
            image_url: image.image_url,
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
  } finally {
    notificationSaving.value = false
  }
}

const sendNotificationProbe = async () => {
  notificationTesting.value = true
  try {
    const result = await sendTestNotification()
    ElMessage.success(result.message)
  } finally {
    notificationTesting.value = false
  }
}

void loadSettings()
</script>

<template>
  <section class="settings-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">店铺设置</h1>
        <p class="page-subtitle">统一维护首页介绍、联系方式、地址和横幅图片，并将编辑与发布分离。</p>
      </div>
    </div>

    <section class="content-card form-card" v-loading="loading">
      <el-alert type="warning" :closable="false" show-icon>
        <template #title>合规录入提示</template>
        <p>动态更新仅限已审核业务范围内的文案、联系方式和横幅，不要借动态内容新增业务能力或主流程。</p>
        <p>避免出现“加微信下单”“扫码进群”“私聊领券”等导流表达，图片上线前也需要人工复核。</p>
      </el-alert>

      <div class="publish-meta">
        <span>当前状态：{{ settingsMeta.has_unpublished_changes ? '有未发布草稿' : '已发布内容最新' }}</span>
        <span>草稿更新时间：{{ settingsMeta.draft_updated_at }}</span>
        <span>最近发布时间：{{ settingsMeta.published_at }}</span>
      </div>

      <el-form label-position="top">
        <div class="grid-two">
          <el-form-item label="店铺名称">
            <el-input v-model="form.shop_name" />
          </el-form-item>

          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" placeholder="建议填写门店电话，不要写导流文案" />
          </el-form-item>
        </div>

        <div class="grid-two">
          <el-form-item label="微信号">
            <el-input v-model="form.wechat_id" placeholder="仅填写微信号本身，不要附带加好友引导" />
          </el-form-item>

          <el-form-item label="营业时间">
            <el-input v-model="form.business_hours" placeholder="例如：10:00-21:00" />
          </el-form-item>
        </div>

        <el-form-item label="门店地址">
          <el-input v-model="form.address" placeholder="建议填写可到店地址，不要出现站外导流说明" />
        </el-form-item>

        <el-form-item label="店铺介绍">
          <el-input
            v-model="form.shop_intro"
            type="textarea"
            :rows="5"
            placeholder="介绍店铺定位、主营风格和到店信息，避免导流和夸张营销话术"
          />
        </el-form-item>

        <el-form-item label="留言反馈页文案">
          <el-input
            v-model="form.contact_intro"
            type="textarea"
            :rows="4"
            placeholder="用于留言反馈页顶部说明，建议使用欢迎交流、分享想法、稍后回复等弱导流表达"
          />
        </el-form-item>

        <el-form-item label="首页横幅">
          <div class="banner-field">
            <div class="banner-toolbar">
              <div class="banner-toolbar-copy">
                <span>已选 {{ selectedBannerUrls.length }} 张横幅图</span>
                <span class="banner-toolbar-tip">横幅将按这里的顺序在小程序首页轮播展示</span>
              </div>
              <div class="banner-toolbar-actions">
                <el-button @click="openBannerPicker">从图片墙选择</el-button>
                <el-button :disabled="!selectedBannerUrls.length" @click="clearSelectedBanners">清空</el-button>
              </div>
            </div>

            <div v-if="selectedBannerUrls.length" class="selected-banner-list">
              <div v-for="(url, index) in selectedBannerUrls" :key="url" class="selected-banner-card">
                <div class="selected-banner-preview">
                  <el-image
                    :src="url"
                    fit="cover"
                    :preview-src-list="selectedBannerUrls"
                    preview-teleported
                  />
                  <span class="selected-banner-index">{{ index + 1 }}</span>
                </div>
                <div class="selected-banner-actions">
                  <el-button text :disabled="index === 0" @click="moveSelectedBanner(url, -1)">前移</el-button>
                  <el-button
                    text
                    :disabled="index === selectedBannerUrls.length - 1"
                    @click="moveSelectedBanner(url, 1)"
                  >
                    后移
                  </el-button>
                  <el-button text type="danger" @click="removeSelectedBanner(url)">移除</el-button>
                </div>
              </div>
            </div>

            <el-empty v-else description="还没有选择首页横幅图，可从已上传的图片墙中挑选" />
          </div>
        </el-form-item>

        <div class="footer-actions">
          <el-button :loading="saving" @click="saveSettings">保存草稿</el-button>
          <el-button
            type="primary"
            :loading="publishing"
            :disabled="!settingsMeta.has_unpublished_changes"
            @click="handlePublish"
          >
            发布到小程序
          </el-button>
        </div>
      </el-form>
    </section>

    <section class="content-card form-card">
      <div class="section-head">
        <div>
          <h2>消息提醒</h2>
          <p>支持企业微信、飞书或通用 Webhook，先用低成本主动提醒闭环留言处理。</p>
        </div>
      </div>

      <el-form label-position="top">
        <div class="grid-two">
          <el-form-item label="启用提醒">
            <el-switch v-model="notificationForm.enabled" />
          </el-form-item>

          <el-form-item label="通道类型">
            <el-select v-model="notificationForm.channel">
              <el-option label="企业微信 Webhook" value="wecom" />
              <el-option label="飞书 Webhook" value="feishu" />
              <el-option label="通用 Webhook" value="generic" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="Webhook 地址">
          <el-input
            v-model="notificationForm.webhook_url"
            placeholder="https://example.com/webhook"
          />
        </el-form-item>

        <el-form-item label="消息前缀">
          <el-input v-model="notificationForm.message_prefix" placeholder="例如：YRFasion" />
        </el-form-item>

        <div class="footer-actions">
          <el-button :loading="notificationTesting" @click="sendNotificationProbe">发送测试提醒</el-button>
          <el-button
            type="primary"
            :loading="notificationSaving"
            @click="saveNotificationSettings"
          >
            保存提醒设置
          </el-button>
        </div>
      </el-form>
    </section>
  </section>

  <el-dialog v-model="bannerPickerVisible" title="从图片墙选择横幅" width="960px" destroy-on-close>
    <div v-loading="bannerLibraryLoading" class="banner-picker">
      <div class="banner-picker-head">
        <p>点击图片即可选中或取消。已选 {{ selectedBannerUrls.length }} 张，保存草稿后即可用于首页横幅。</p>
      </div>

      <el-empty
        v-if="!bannerLibraryLoading && !bannerLibrary.length"
        description="图片墙还没有内容，请先到商品管理上传图片"
      />

      <div v-else class="banner-library-grid">
        <button
          v-for="item in bannerLibrary"
          :key="item.image_url"
          type="button"
          class="banner-library-card"
          :class="{ 'banner-library-card-active': selectedBannerUrls.includes(item.image_url) }"
          @click="toggleBannerSelection(item.image_url)"
        >
          <div class="banner-library-preview">
            <el-image :src="item.image_url" fit="cover" />
            <span v-if="selectedBannerUrls.includes(item.image_url)" class="banner-library-check">已选</span>
          </div>
          <div class="banner-library-meta">
            <p class="banner-library-title">{{ item.product_name }}</p>
            <p class="banner-library-name">{{ item.original_name || '已上传图片' }}</p>
            <p class="banner-library-badge">{{ item.is_cover ? '封面图' : '详情图' }}</p>
          </div>
        </button>
      </div>
    </div>

    <template #footer>
      <div class="footer-actions">
        <el-button @click="bannerPickerVisible = false">关闭</el-button>
        <el-button type="primary" @click="bannerPickerVisible = false">完成选择</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-card {
  padding: 28px;
}

.publish-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin: 18px 0 22px;
  color: #7d6955;
  font-size: 13px;
}

.section-head h2 {
  margin: 0 0 8px;
  font-family: 'Fraunces', serif;
  font-size: 28px;
  color: #30251b;
}

.section-head p {
  margin: 0 0 18px;
  color: #7d6955;
  line-height: 1.8;
}

.grid-two {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.footer-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.banner-field {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.banner-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.banner-toolbar-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #5e4d3e;
}

.banner-toolbar-tip {
  color: #8d7865;
  font-size: 13px;
}

.banner-toolbar-actions {
  display: flex;
  gap: 12px;
}

.selected-banner-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.selected-banner-card {
  border: 1px solid #eadfce;
  border-radius: 18px;
  padding: 12px;
  background: #fffaf4;
}

.selected-banner-preview {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: #f5ecdf;
}

.selected-banner-preview :deep(.el-image) {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
}

.selected-banner-index {
  position: absolute;
  top: 10px;
  left: 10px;
  min-width: 26px;
  height: 26px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(48, 37, 27, 0.78);
  color: #fff;
  font-size: 12px;
  line-height: 26px;
  text-align: center;
}

.selected-banner-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.banner-picker-head {
  margin-bottom: 16px;
  color: #7d6955;
}

.banner-picker-head p {
  margin: 0;
  line-height: 1.8;
}

.banner-library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  max-height: 60vh;
  overflow: auto;
  padding-right: 4px;
}

.banner-library-card {
  border: 1px solid #eadfce;
  border-radius: 18px;
  padding: 12px;
  background: #fffaf4;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.banner-library-card:hover {
  border-color: #c8aa87;
  box-shadow: 0 12px 24px rgba(90, 60, 47, 0.08);
  transform: translateY(-1px);
}

.banner-library-card-active {
  border-color: #7f5a3d;
  box-shadow: 0 14px 28px rgba(90, 60, 47, 0.12);
}

.banner-library-preview {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: #f5ecdf;
}

.banner-library-preview :deep(.el-image) {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
}

.banner-library-check {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(48, 37, 27, 0.82);
  color: #fff;
  font-size: 12px;
}

.banner-library-meta {
  margin-top: 10px;
}

.banner-library-title,
.banner-library-name,
.banner-library-badge {
  margin: 0;
  line-height: 1.6;
}

.banner-library-title {
  color: #30251b;
  font-weight: 600;
}

.banner-library-name,
.banner-library-badge {
  color: #8d7865;
  font-size: 13px;
}

@media (max-width: 1024px) {
  .grid-two {
    grid-template-columns: 1fr;
  }

  .banner-toolbar {
    flex-direction: column;
  }

  .banner-toolbar-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
