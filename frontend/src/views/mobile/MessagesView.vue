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
    <article class="mobile-card mobile-panel">
      <div class="card-title-row">
        <h2 class="mobile-section-title">留言管理</h2>
        <el-button plain :loading="loading" @click="loadMessages">刷新</el-button>
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
      <p class="mobile-muted total-note">共 {{ total }} 条</p>
    </article>

    <section class="message-list" v-loading="loading">
      <article v-for="message in items" :key="message.id" class="mobile-card message-card" @click="openMessage(message)">
        <div class="message-head">
          <div>
            <strong>{{ message.product_name }}</strong>
            <p class="mobile-muted">{{ message.miniapp_user_nickname || message.miniapp_user_openid }}</p>
          </div>
          <el-tag size="small" :type="message.status === 'unread' ? 'danger' : message.status === 'replied' ? 'success' : 'warning'">
            {{ message.status }}
          </el-tag>
        </div>
        <p class="message-content">{{ message.content }}</p>
        <span class="mobile-muted">{{ message.created_at }}</span>
      </article>
      <el-empty v-if="!loading && !items.length" description="暂无留言" />
    </section>

    <article v-if="items.length" class="mobile-card mobile-panel pagination-card">
      <div class="pagination-actions">
        <el-button :disabled="page <= 1" @click="page -= 1; loadMessages()">上一页</el-button>
        <el-button :disabled="page * pageSize >= total" @click="page += 1; loadMessages()">下一页</el-button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.mobile-panel,
.pagination-card {
  padding: 16px;
}

.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink-soft);
}

.status-chip.active {
  border-color: rgba(47, 106, 88, 0.3);
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.total-note {
  margin: 14px 0 0;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.message-head p,
.message-content {
  margin: 0;
}

.message-content {
  line-height: 1.7;
}

.pagination-actions {
  display: flex;
  gap: 10px;
}
</style>
