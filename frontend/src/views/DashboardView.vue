<script setup lang="ts">
import { ChatLineRound, Goods, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { fetchDashboardSummary, type DashboardSummary } from '../api/modules/dashboard'
import { sendUnreadSummaryNotification } from '../api/modules/notifications'

const loading = ref(false)
const summary = ref<DashboardSummary>({
  unread_message_count: 0,
  product_count: 0,
  miniapp_user_count: 0,
  notification_enabled: false,
  notification_channel: null,
})

const statCards = [
  {
    key: 'product_count',
    title: '商品总数',
    subtitle: '当前后台已维护的商品数',
    icon: Goods,
  },
  {
    key: 'unread_message_count',
    title: '未读留言',
    subtitle: '需要尽快处理的咨询消息',
    icon: ChatLineRound,
  },
  {
    key: 'miniapp_user_count',
    title: '小程序用户',
    subtitle: '已记录的访问用户总量',
    icon: User,
  },
] as const

const loadSummary = async () => {
  loading.value = true
  try {
    summary.value = await fetchDashboardSummary()
  } finally {
    loading.value = false
  }
}

const sendSummaryNotification = async () => {
  await sendUnreadSummaryNotification()
  ElMessage.success('未读汇总提醒已发送')
}

onMounted(() => {
  void loadSummary()
})
</script>

<template>
  <section class="dashboard-page">
    <div class="hero-strip content-card">
      <div>
        <h1 class="page-title">概览</h1>
        <p class="page-subtitle">
          这是一版偏运营导向的后台。你可以快速查看未读留言、用户增长和商品维护规模。
        </p>
      </div>

      <el-button plain @click="loadSummary">刷新数据</el-button>
    </div>

    <section class="stats-grid" v-loading="loading">
      <article v-for="item in statCards" :key="item.key" class="stat-card content-card">
        <div class="stat-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <p class="stat-title">{{ item.title }}</p>
        <strong class="stat-value">{{ summary[item.key] }}</strong>
        <span class="stat-note">{{ item.subtitle }}</span>
      </article>
    </section>

    <section class="content-card tips-card">
      <h2>当前阶段建议</h2>
      <ul>
        <li>优先保持商品图片、文案和标签一致，保证小程序展示稳定。</li>
        <li>未读留言尽量当天处理，第一版用户感知最强的就是响应速度。</li>
        <li>商品排序建议按“主推款、新上款、稳定款”三层逻辑维护。</li>
      </ul>
    </section>

    <section class="content-card notification-card">
      <div>
        <h2>提醒通道</h2>
        <p class="notification-text">
          {{
            summary.notification_enabled
              ? `当前已启用 ${summary.notification_channel} Webhook，可主动推送未读汇总。`
              : '当前未启用主动提醒，请先到店铺设置中配置提醒通道。'
          }}
        </p>
      </div>

      <el-button
        type="primary"
        :disabled="!summary.notification_enabled"
        @click="sendSummaryNotification"
      >
        发送未读汇总提醒
      </el-button>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-strip,
.tips-card,
.notification-card {
  padding: 28px;
}

.hero-strip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.stat-card {
  padding: 24px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(139, 94, 60, 0.12);
  color: #6c4526;
  font-size: 22px;
}

.stat-title {
  margin: 18px 0 8px;
  color: #715d49;
}

.stat-value {
  display: block;
  font-family: 'Fraunces', serif;
  font-size: 52px;
  line-height: 1;
  color: #2e2319;
}

.stat-note {
  display: block;
  margin-top: 10px;
  color: #8d7964;
  line-height: 1.7;
}

.tips-card h2 {
  margin: 0 0 16px;
  font-family: 'Fraunces', serif;
  font-size: 28px;
  color: #30251b;
}

.notification-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.notification-card h2 {
  margin: 0 0 10px;
  font-family: 'Fraunces', serif;
  font-size: 28px;
  color: #30251b;
}

.notification-text {
  margin: 0;
  color: #6f5f50;
  line-height: 1.8;
}

.tips-card ul {
  margin: 0;
  padding-left: 20px;
  color: #6f5f50;
  line-height: 1.9;
}

@media (max-width: 900px) {
  .hero-strip {
    flex-direction: column;
  }

  .notification-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
