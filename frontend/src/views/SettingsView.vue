<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  fetchNotificationSettings,
  sendTestNotification,
  updateNotificationSettings,
} from '../api/modules/notifications'
import { fetchSettings, updateSettings } from '../api/modules/settings'

const loading = ref(false)
const notificationSaving = ref(false)
const notificationTesting = ref(false)
const form = reactive({
  shop_name: '',
  shop_intro: '',
  contact_phone: '',
  wechat_id: '',
  address: '',
  business_hours: '',
  homepage_banner_text: '',
})
const notificationForm = reactive({
  enabled: false,
  channel: 'wecom' as 'wecom' | 'feishu' | 'generic',
  webhook_url: '',
  message_prefix: 'YRFasion',
})

const loadSettings = async () => {
  loading.value = true
  try {
    const [data, notificationData] = await Promise.all([
      fetchSettings(),
      fetchNotificationSettings(),
    ])
    form.shop_name = data.shop_name
    form.shop_intro = data.shop_intro
    form.contact_phone = data.contact_phone
    form.wechat_id = data.wechat_id
    form.address = data.address
    form.business_hours = data.business_hours
    form.homepage_banner_text = data.homepage_banner_urls.join('\n')
    notificationForm.enabled = notificationData.enabled
    notificationForm.channel = notificationData.channel
    notificationForm.webhook_url = notificationData.webhook_url
    notificationForm.message_prefix = notificationData.message_prefix
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  await updateSettings({
    shop_name: form.shop_name.trim(),
    shop_intro: form.shop_intro.trim(),
    contact_phone: form.contact_phone.trim(),
    wechat_id: form.wechat_id.trim(),
    address: form.address.trim(),
    business_hours: form.business_hours.trim(),
    homepage_banner_urls: form.homepage_banner_text
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean),
  })
  ElMessage.success('店铺设置已保存')
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
        <p class="page-subtitle">统一维护首页介绍、联系方式、地址和横幅资源路径。</p>
      </div>
    </div>

    <section class="content-card form-card" v-loading="loading">
      <el-form label-position="top">
        <div class="grid-two">
          <el-form-item label="店铺名称">
            <el-input v-model="form.shop_name" />
          </el-form-item>

          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" />
          </el-form-item>
        </div>

        <div class="grid-two">
          <el-form-item label="微信号">
            <el-input v-model="form.wechat_id" />
          </el-form-item>

          <el-form-item label="营业时间">
            <el-input v-model="form.business_hours" />
          </el-form-item>
        </div>

        <el-form-item label="门店地址">
          <el-input v-model="form.address" />
        </el-form-item>

        <el-form-item label="店铺介绍">
          <el-input v-model="form.shop_intro" type="textarea" :rows="5" />
        </el-form-item>

        <el-form-item label="首页横幅 URL">
          <el-input
            v-model="form.homepage_banner_text"
            type="textarea"
            :rows="5"
            placeholder="每行一个图片 URL"
          />
        </el-form-item>

        <div class="footer-actions">
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
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
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
