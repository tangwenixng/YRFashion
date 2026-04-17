<script setup lang="ts">
import { onMounted, ref } from 'vue'
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
  <section class="mobile-page">
    <article class="mobile-card mobile-panel hero-message-card">
      <div class="section-row">
        <div>
          <span class="section-kicker">留言中心</span>
          <h2 class="mobile-section-title">优先处理未读，再进入详情回复</h2>
          <p class="mobile-muted">共 {{ total }} 条留言，当前按 {{ statusTabs.find((tab) => tab.value === status)?.label }} 查看。</p>
        </div>
        <button class="mobile-action-button secondary refresh-button" type="button" @click="loadMessages">
          刷新
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
        class="mobile-card message-card"
        role="button"
        tabindex="0"
        @click="openMessage(message)"
        @keyup.enter="openMessage(message)"
      >
        <div class="message-head">
          <div class="message-title-block">
            <strong>{{ message.product_name }}</strong>
            <p>{{ message.miniapp_user_nickname || message.miniapp_user_openid }}</p>
          </div>
          <span class="message-status" :class="message.status">{{ message.status }}</span>
        </div>

        <p class="message-content">{{ message.content }}</p>

        <div class="message-footer">
          <span class="mobile-chip soft-chip">{{ message.reply_content ? '已回复' : '待处理' }}</span>
          <span class="mobile-muted">{{ message.created_at }}</span>
        </div>
      </article>
      <el-empty v-if="!loading && !items.length" description="暂无留言" />
    </section>

    <article v-if="items.length" class="mobile-card mobile-panel pagination-card">
      <div class="pagination-actions">
        <button class="mobile-action-button secondary" type="button" :disabled="page <= 1" @click="page -= 1; loadMessages()">上一页</button>
        <button class="mobile-action-button secondary" type="button" :disabled="page * pageSize >= total" @click="page += 1; loadMessages()">下一页</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.mobile-panel,
.pagination-card {
  padding: 18px;
}

.hero-message-card {
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 244, 238, 0.96));
}

.section-row {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.refresh-button {
  width: 100%;
}

.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.status-chip {
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--mobile-muted);
  font-weight: 600;
}

.status-chip.active {
  border-color: rgba(47, 106, 88, 0.22);
  background: rgba(47, 106, 88, 0.1);
  color: var(--brand-deep);
  box-shadow: 0 10px 18px rgba(29, 67, 56, 0.08);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-head,
.message-footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.message-title-block {
  min-width: 0;
}

.message-title-block strong {
  display: block;
  font-size: 17px;
  line-height: 1.35;
  color: #252320;
}

.message-title-block p,
.message-content {
  margin: 0;
}

.message-title-block p {
  margin-top: 6px;
  color: var(--mobile-muted);
}

.message-status {
  flex-shrink: 0;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.message-status.unread {
  background: rgba(214, 92, 70, 0.14);
  color: #b54d38;
}

.message-status.read {
  background: rgba(57, 76, 64, 0.08);
  color: #51615a;
}

.message-status.replied {
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.message-content {
  line-height: 1.75;
  color: #4c544e;
}

.soft-chip {
  background: rgba(192, 138, 54, 0.1);
  color: #805b2a;
}

.pagination-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
