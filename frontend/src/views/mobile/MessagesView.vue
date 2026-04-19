<script setup lang="ts">
import { RefreshRight } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchMessages, type MessageItem } from '../../api/modules/messages'
import { saveMobileMessageSnapshot } from './messageCache'

const router = useRouter()
const loading = ref(false)
const status = ref<'all' | 'unread' | 'read' | 'replied'>('all')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const items = ref<MessageItem[]>([])

const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '未读', value: 'unread' },
  { label: '已读', value: 'read' },
  { label: '已回复', value: 'replied' },
] as const

const currentStatusLabel = computed(() => statusTabs.find((tab) => tab.value === status.value)?.label || '全部')

const formatStatusLabel = (value: MessageItem['status']) => {
  if (value === 'unread') return '未读'
  if (value === 'read') return '已读'
  return '已回复'
}

const loadMessages = async () => {
  loading.value = true
  try {
    const result = await fetchMessages({
      page: page.value,
      page_size: pageSize.value,
      status: status.value === 'all' ? undefined : status.value,
    })
    items.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

const openMessage = (message: MessageItem) => {
  saveMobileMessageSnapshot(message)
  void router.push(`/m/messages/${message.id}`)
}

onMounted(() => {
  void loadMessages()
})
</script>

<template>
  <section class="mobile-page messages-page">
    <article class="toolbar-shell">
      <div class="toolbar-main-row">
        <p class="toolbar-summary">{{ total }} 条 · {{ currentStatusLabel }}</p>
        <button class="icon-action" type="button" aria-label="刷新留言列表" @click="loadMessages">
          <el-icon><RefreshRight /></el-icon>
        </button>
      </div>
      <div class="status-chips">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          class="status-chip"
          :class="{ active: status === tab.value }"
          type="button"
          @click="status = tab.value; page = 1; loadMessages()"
        >
          {{ tab.label }}
        </button>
      </div>
    </article>

    <section class="message-list" v-loading="loading">
      <article
        v-for="message in items"
        :key="message.id"
        class="message-card"
        role="button"
        tabindex="0"
        @click="openMessage(message)"
        @keyup.enter="openMessage(message)"
      >
        <div class="message-card-head">
          <div class="message-main">
            <strong>{{ message.product_name }}</strong>
            <p>{{ message.miniapp_user_nickname || message.miniapp_user_openid }}</p>
          </div>
          <span class="message-badge" :class="message.status">{{ formatStatusLabel(message.status) }}</span>
        </div>

        <p class="message-content">{{ message.content }}</p>

        <div class="message-card-foot">
          <span class="message-time">{{ message.created_at }}</span>
          <span class="message-hint">{{ message.reply_content ? '已回复' : '进入详情回复' }}</span>
        </div>
      </article>
      <div v-if="!loading && !items.length" class="compact-empty">当前筛选下暂无留言</div>
    </section>

    <article v-if="items.length" class="pager-shell">
      <button class="mobile-action-button secondary" type="button" :disabled="page <= 1" @click="page -= 1; loadMessages()">上一页</button>
      <button class="mobile-action-button secondary" type="button" :disabled="page * pageSize >= total" @click="page += 1; loadMessages()">下一页</button>
    </article>
  </section>
</template>

<style scoped>
.messages-page {
  gap: 12px;
}

.toolbar-shell,
.pager-shell,
.message-card {
  border: 1px solid rgba(40, 55, 49, 0.08);
  background: rgba(255, 255, 255, 0.96);
}

.toolbar-shell {
  padding: 14px;
  border-radius: 16px;
}

.toolbar-main-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.toolbar-summary {
  margin: 0;
  margin-top: 4px;
  color: #67706a;
  font-size: 12px;
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

.status-chips {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 999px;
  background: rgba(249, 249, 247, 0.96);
  color: #66706a;
  font-weight: 600;
}

.status-chip.active {
  border-color: rgba(47, 106, 88, 0.16);
  background: rgba(47, 106, 88, 0.08);
  color: var(--brand-deep);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-card {
  padding: 14px;
  border-radius: 14px;
}

.message-card-head,
.message-card-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.message-main {
  min-width: 0;
}

.message-main strong {
  display: block;
  font-size: 16px;
  color: #242622;
  line-height: 1.3;
}

.message-main p,
.message-content,
.message-time,
.message-hint {
  margin: 0;
}

.message-main p {
  margin-top: 5px;
  color: #6a736d;
  font-size: 13px;
}

.message-badge {
  flex-shrink: 0;
  min-height: 26px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.message-badge.unread {
  background: rgba(214, 92, 70, 0.14);
  color: #b54d38;
}

.message-badge.read {
  background: rgba(57, 76, 64, 0.08);
  color: #51615a;
}

.message-badge.replied {
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.message-content {
  margin-top: 12px;
  color: #49524c;
  line-height: 1.6;
}

.message-card-foot {
  margin-top: 12px;
  align-items: center;
}

.message-time {
  color: #79817c;
  font-size: 12px;
}

.message-hint {
  color: #77501a;
  font-size: 12px;
  font-weight: 600;
}

.compact-empty {
  padding: 22px 16px;
  border: 1px dashed rgba(57, 76, 64, 0.12);
  border-radius: 14px;
  color: #717972;
  text-align: center;
  background: rgba(255, 255, 255, 0.66);
}

.pager-shell {
  padding: 12px;
  border-radius: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
