<script setup lang="ts">
import { ChatLineRound, Goods, TrendCharts, User } from '@element-plus/icons-vue'
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
  recent_message_trend: [],
  top_products: [],
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

    <section class="insight-grid">
      <article class="content-card insight-card">
        <div class="insight-header">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div>
            <h2>最近 7 天咨询趋势</h2>
            <p>按天查看咨询变化，方便判断内容热度是否上升。</p>
          </div>
        </div>

        <div class="trend-list">
          <div v-for="item in summary.recent_message_trend" :key="item.date" class="trend-row">
            <span>{{ item.date }}</span>
            <strong>{{ item.count }}</strong>
          </div>
        </div>
      </article>

      <article class="content-card insight-card">
        <div class="insight-header">
          <div class="stat-icon">
            <el-icon><ChatLineRound /></el-icon>
          </div>
          <div>
            <h2>咨询最多的商品</h2>
            <p>优先关注高咨询商品，适合继续优化图文和推荐位。</p>
          </div>
        </div>

        <div v-if="summary.top_products.length" class="top-product-list">
          <div v-for="item in summary.top_products" :key="item.product_id" class="top-product-row">
            <span class="top-product-name">{{ item.product_name }}</span>
            <strong>{{ item.message_count }} 条咨询</strong>
          </div>
        </div>
        <p v-else class="empty-note">当前还没有可统计的咨询数据。</p>
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
.notification-card,
.insight-card {
  padding: 28px;
}

.hero-strip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stats-grid,
.insight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.insight-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
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

.insight-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.insight-header h2,
.tips-card h2,
.notification-card h2 {
  margin: 0 0 10px;
  font-family: 'Fraunces', serif;
  font-size: 28px;
  color: #30251b;
}

.insight-header p,
.notification-text,
.tips-card ul,
.empty-note {
  margin: 0;
  color: #6f5f50;
  line-height: 1.8;
}

.trend-list,
.top-product-list {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-row,
.top-product-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(139, 94, 60, 0.06);
  color: #4b3728;
}

.top-product-name {
  font-weight: 600;
}

.tips-card ul {
  padding-left: 20px;
}

.notification-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

@media (max-width: 900px) {
  .hero-strip,
  .notification-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid,
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
</style>
