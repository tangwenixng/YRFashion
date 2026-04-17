<script setup lang="ts">
import { ArrowRight, ChatLineRound, Goods, TrendCharts, User } from '@element-plus/icons-vue'
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

const sideCards = [
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
      <div class="hero-card-main">
        <div>
          <span class="hero-chip">今日重点</span>
          <h2 class="mobile-section-title">先处理未读咨询，再补商品与图片</h2>
          <p class="mobile-muted hero-copy">把最常用的动作放到一屏内：先看提醒，再快速跳到商品或留言。</p>
        </div>
        <button class="mobile-action-button secondary hero-refresh" type="button" @click="loadSummary">
          刷新数据
        </button>
      </div>

      <div class="stats-grid" v-loading="loading">
        <article class="unread-stat-card">
          <div class="stat-label-row">
            <span>未读留言</span>
            <el-icon><ChatLineRound /></el-icon>
          </div>
          <strong>{{ summary.unread_message_count }}</strong>
          <p>优先进入留言中心，减少超时未回复。</p>
        </article>

        <article v-for="card in sideCards" :key="card.key" class="mini-stat-card">
          <div class="mini-stat-icon">
            <el-icon><component :is="card.icon" /></el-icon>
          </div>
          <span>{{ card.label }}</span>
          <strong>{{ summary[card.key] }}</strong>
        </article>
      </div>
    </article>

    <article class="mobile-card shortcuts-card">
      <div class="section-row">
        <div>
          <span class="section-kicker">快速入口</span>
          <h2 class="mobile-section-title">高频动作保持一跳直达</h2>
        </div>
      </div>

      <div class="shortcut-list">
        <button class="mobile-card-link shortcut-item" type="button" @click="router.push('/m/products')">
          <div class="shortcut-copy">
            <strong>商品管理</strong>
            <span>搜索、编辑、图片维护、发布与撤回都集中在这一组流程里。</span>
          </div>
          <span class="shortcut-arrow"><el-icon><ArrowRight /></el-icon></span>
        </button>

        <button class="mobile-card-link shortcut-item" type="button" @click="router.push('/m/messages')">
          <div class="shortcut-copy">
            <strong>留言中心</strong>
            <span>优先查看未读、进入详情并完成回复，减少反复来回切换。</span>
          </div>
          <span class="shortcut-arrow"><el-icon><ArrowRight /></el-icon></span>
        </button>
      </div>
    </article>

    <article class="mobile-card insight-card">
      <div class="section-row">
        <div>
          <span class="section-kicker">趋势速览</span>
          <h2 class="mobile-section-title">最近 7 天咨询变化</h2>
        </div>
        <span class="mobile-chip muted-chip">
          <el-icon><TrendCharts /></el-icon>
          动态
        </span>
      </div>

      <div v-if="summary.recent_message_trend.length" class="trend-list">
        <div v-for="item in summary.recent_message_trend" :key="item.date" class="trend-row">
          <div>
            <strong>{{ item.count }}</strong>
            <span>{{ item.date }}</span>
          </div>
          <div class="trend-bar-track">
            <span class="trend-bar-fill" :style="{ width: `${Math.min(100, Math.max(18, item.count * 14))}%` }" />
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无趋势数据" />
    </article>
  </section>
</template>

<style scoped>
.hero-card,
.shortcuts-card,
.insight-card {
  padding: 18px;
}

.hero-card {
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.16), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 245, 239, 0.96));
}

.hero-card-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-chip,
.section-kicker {
  display: inline-flex;
  width: fit-content;
  margin-bottom: 10px;
  padding: 0 12px;
  min-height: 30px;
  align-items: center;
  border-radius: 999px;
  background: rgba(47, 106, 88, 0.08);
  color: var(--brand-deep);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-copy {
  margin: 12px 0 0;
  line-height: 1.75;
}

.hero-refresh {
  width: 100%;
}

.stats-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.unread-stat-card {
  grid-column: 1 / -1;
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(145deg, var(--mobile-shell-dark), #29483e);
  color: #f9f4ec;
  box-shadow: 0 16px 30px rgba(25, 35, 31, 0.18);
}

.stat-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: rgba(249, 244, 236, 0.74);
}

.unread-stat-card strong {
  display: block;
  margin-top: 14px;
  font-size: 42px;
  line-height: 1;
}

.unread-stat-card p {
  margin: 10px 0 0;
  color: rgba(249, 244, 236, 0.78);
  line-height: 1.7;
}

.mini-stat-card {
  padding: 16px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(57, 76, 64, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mini-stat-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(192, 138, 54, 0.12);
  color: #875d25;
}

.mini-stat-card span {
  color: var(--mobile-muted);
  font-size: 12px;
}

.mini-stat-card strong {
  font-size: 28px;
  line-height: 1;
}

.section-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.shortcut-copy {
  min-width: 0;
}

.shortcut-arrow {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(47, 106, 88, 0.08);
  color: var(--brand-deep);
}

.muted-chip {
  gap: 6px;
  color: #805b2a;
  background: rgba(192, 138, 54, 0.12);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.trend-row {
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(47, 106, 88, 0.06);
}

.trend-row > div:first-child {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.trend-row strong {
  font-size: 22px;
}

.trend-row span {
  color: var(--mobile-muted);
}

.trend-bar-track {
  margin-top: 12px;
  height: 8px;
  border-radius: 999px;
  background: rgba(57, 76, 64, 0.1);
  overflow: hidden;
}

.trend-bar-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent-gold), var(--brand));
}
</style>
