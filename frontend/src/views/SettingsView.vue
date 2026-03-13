<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import { fetchSettings, updateSettings } from '../api/modules/settings'

const loading = ref(false)
const form = reactive({
  shop_name: '',
  shop_intro: '',
  contact_phone: '',
  wechat_id: '',
  address: '',
  business_hours: '',
  homepage_banner_text: '',
})

const loadSettings = async () => {
  loading.value = true
  try {
    const data = await fetchSettings()
    form.shop_name = data.shop_name
    form.shop_intro = data.shop_intro
    form.contact_phone = data.contact_phone
    form.wechat_id = data.wechat_id
    form.address = data.address
    form.business_hours = data.business_hours
    form.homepage_banner_text = data.homepage_banner_urls.join('\n')
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
