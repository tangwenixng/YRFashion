<script setup lang="ts">
import { ChatLineRound, Goods, User } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchDashboardSummary, type DashboardSummary } from '../../api/modules/dashboard'

const router = useRouter()
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

const cards = [
  { key: 'unread_message_count', label: '未读留言', icon: ChatLineRound },
  { key: 'product_count', label: '已维护商品', icon: Goods },
  { key: 'miniapp_user_count', label: '小程序用户', icon: User },
] as const

const loadSummary = async () => {
  loading.value = true
  try {
    summary.value = await fetchDashboardSummary()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadSummary()
})
</script>

<template>
  <section class="mobile-page mobile-home">
    <article class="mobile-card hero-card">
      <div>
        <p class="hero-eyebrow">今日待处理</p>
        <h2 class="mobile-section-title">快速查看留言、商品和用户变化</h2>
        <p class="mobile-muted">现在更适合手机浏览器的节奏：先看摘要，再进入单项任务处理。</p>
      </div>
      <el-button plain :loading="loading" @click="loadSummary">刷新</el-button>
    </article>

    <section class="stats-grid" v-loading="loading">
      <article v-for="card in cards" :key="card.key" class="mobile-card stat-card">
        <div class="stat-icon">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ summary[card.key] }}</strong>
      </article>
    </section>

    <article class="mobile-card shortcuts-card">
      <div class="card-title-row">
        <h2 class="mobile-section-title">快捷入口</h2>
        <span class="mobile-muted">高频操作优先</span>
      </div>
      <div class="shortcut-list">
        <button class="shortcut-button" type="button" @click="router.push('/m/products')">
          <strong>商品管理</strong>
          <span>搜索、编辑、处理图片</span>
        </button>
        <button class="shortcut-button" type="button" @click="router.push('/m/messages')">
          <strong>留言管理</strong>
          <span>查看未读、进入详情、快速回复</span>
        </button>
      </div>
    </article>

    <article class="mobile-card insight-card">
      <div class="card-title-row">
        <h2 class="mobile-section-title">最近 7 天咨询趋势</h2>
        <span class="mobile-muted">按天查看</span>
      </div>
      <div v-if="summary.recent_message_trend.length" class="trend-list">
        <div v-for="item in summary.recent_message_trend" :key="item.date" class="trend-row">
          <span>{{ item.date }}</span>
          <strong>{{ item.count }}</strong>
        </div>
      </div>
      <el-empty v-else description="暂无趋势数据" />
    </article>
  </section>
</template>

<style scoped>
.mobile-home {
  padding-bottom: 8px;
}

.hero-card,
.shortcuts-card,
.insight-card {
  padding: 18px;
}

.hero-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-soft);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(47, 106, 88, 0.1);
  color: var(--brand-deep);
}

.stat-label {
  font-size: 12px;
  color: var(--ink-soft);
}

.stat-value {
  font-size: 26px;
  line-height: 1;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-button {
  padding: 16px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  border-radius: 18px;
  background: rgba(47, 106, 88, 0.06);
  text-align: left;
}

.shortcut-button strong,
.shortcut-button span {
  display: block;
}

.shortcut-button span {
  margin-top: 6px;
  color: var(--ink-soft);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(47, 106, 88, 0.06);
}
</style>
