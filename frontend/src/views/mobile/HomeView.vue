<script setup lang="ts">
import { ChatLineRound, Goods, Promotion, User } from '@element-plus/icons-vue'
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

const metrics = [
  { key: 'unread_message_count', label: '未读留言', icon: ChatLineRound, tone: 'accent' },
  { key: 'product_count', label: '商品数', icon: Goods, tone: 'plain' },
  { key: 'miniapp_user_count', label: '用户数', icon: User, tone: 'plain' },
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
  <section class="mobile-page home-page" v-loading="loading">
    <section class="metric-grid">
      <article v-for="metric in metrics" :key="metric.key" class="metric-card" :class="metric.tone">
        <div class="metric-label-row">
          <div class="metric-icon">
            <el-icon><component :is="metric.icon" /></el-icon>
          </div>
          <span>{{ metric.label }}</span>
        </div>
        <strong>{{ summary[metric.key] }}</strong>
      </article>
    </section>

    <section class="quick-grid">
      <button class="entry-card" type="button" @click="router.push('/m/products')">
        <div>
          <strong>商品</strong>
          <span>列表、编辑、图片</span>
        </div>
        <em>进入</em>
      </button>

      <button class="entry-card muted" type="button" @click="router.push('/m/messages')">
        <div>
          <strong>留言</strong>
          <span>未读、详情、回复</span>
        </div>
        <em>查看</em>
      </button>
    </section>

    <article class="section-block trend-block">
      <div class="section-head compact">
        <h2>最近 7 天</h2>
        <button class="ghost-action" type="button" @click="loadSummary">刷新</button>
      </div>

      <div v-if="summary.recent_message_trend.length" class="trend-list">
        <div v-for="item in summary.recent_message_trend" :key="item.date" class="trend-row">
          <span>{{ item.date }}</span>
          <div class="trend-row-main">
            <i class="trend-bar" :style="{ width: `${Math.min(100, Math.max(12, item.count * 14))}%` }" />
            <strong>{{ item.count }}</strong>
          </div>
        </div>
      </div>
      <div v-else class="compact-empty">最近 7 天暂无数据</div>
    </article>
  </section>
</template>

<style scoped>
.home-page {
  gap: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.metric-card {
  padding: 14px;
  border: 1px solid rgba(40, 55, 49, 0.06);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 250, 246, 0.94));
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 8px 20px rgba(28, 40, 34, 0.05);
}

.metric-card.plain {
  border-radius: 18px;
}

.metric-card.accent {
  border-radius: 22px;
  background: linear-gradient(160deg, var(--mobile-shell-dark), #27463c);
  color: #f8f4ed;
  box-shadow: 0 10px 24px rgba(29, 64, 53, 0.16);
}

.metric-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-label-row span {
  font-size: 12px;
  color: inherit;
  opacity: 0.84;
}

.metric-card strong {
  font-size: 32px;
  line-height: 1;
}

.metric-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.12);
}

.metric-card.plain .metric-icon {
  background: rgba(47, 106, 88, 0.08);
  color: var(--brand-deep);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.entry-card {
  min-height: 104px;
  padding: 16px;
  border: 1px solid rgba(38, 55, 48, 0.06);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 250, 246, 0.94));
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  box-shadow: 0 8px 20px rgba(28, 40, 34, 0.05);
}

.entry-card.muted {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(246, 248, 243, 0.92));
}

.entry-card strong,
.entry-card span,
.entry-card em {
  display: block;
}

.entry-card strong {
  font-size: 18px;
  color: #232521;
}

.entry-card span {
  margin-top: 6px;
  color: #646d66;
  line-height: 1.4;
  font-size: 13px;
}

.entry-card em {
  font-style: normal;
  color: var(--brand-deep);
  font-size: 12px;
  font-weight: 700;
}

.section-block {
  padding: 16px;
  border: 1px solid rgba(40, 55, 49, 0.06);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 250, 246, 0.94));
  box-shadow: 0 8px 20px rgba(28, 40, 34, 0.05);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.section-head h2 {
  margin: 0;
  font-size: 18px;
  color: #20231f;
}

.ghost-action {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(47, 106, 88, 0.1);
  border-radius: 12px;
  background: rgba(247, 248, 244, 0.9);
  color: var(--brand-deep);
  font-weight: 600;
}

.trend-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 10px;
  align-items: center;
  font-size: 13px;
  color: #5e6761;
}

.trend-row-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trend-bar {
  display: block;
  height: 8px;
  min-width: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent-gold), var(--brand));
}

.compact-empty {
  margin-top: 12px;
  border-top: 1px dashed rgba(57, 76, 64, 0.12);
  padding-top: 12px;
  color: #717972;
  font-size: 13px;
}
</style>
