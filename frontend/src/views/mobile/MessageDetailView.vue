<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchMessageDetail, markMessageRead, markMessageUnread, replyMessage, type MessageItem } from '../../api/modules/messages'
import { readMobileMessageSnapshot, removeMobileMessageSnapshot, saveMobileMessageSnapshot } from './messageCache'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const message = ref<MessageItem | null>(null)
const replyForm = reactive({ reply_content: '' })

const messageId = computed(() => String(route.params.id || ''))
const hasMessage = computed(() => Boolean(message.value))
const statusLabel = computed(() => {
  if (message.value?.status === 'unread') return '未读'
  if (message.value?.status === 'read') return '已读'
  if (message.value?.status === 'replied') return '已回复'
  return ''
})

const syncMessage = (nextMessage: MessageItem) => {
  message.value = nextMessage
  replyForm.reply_content = nextMessage.reply_content ?? ''
  saveMobileMessageSnapshot(nextMessage)
}

const recoverMessage = async () => {
  const cachedMessage = readMobileMessageSnapshot(messageId.value)
  if (cachedMessage) {
    syncMessage(cachedMessage)
    return
  }

  const numericId = Number(messageId.value)
  if (!Number.isFinite(numericId) || numericId <= 0) {
    ElMessage.warning('留言上下文已失效，已返回列表重新打开。')
    void router.replace('/m/messages')
    return
  }

  loading.value = true
  try {
    const detail = await fetchMessageDetail(numericId)
    syncMessage(detail)
  } catch {
    ElMessage.warning('留言上下文已失效，已返回列表重新打开。')
    void router.replace('/m/messages')
  } finally {
    loading.value = false
  }
}

const toggleReadState = async () => {
  if (!message.value) return

  loading.value = true
  try {
    const nextMessage =
      message.value.status === 'unread'
        ? await markMessageRead(message.value.id)
        : await markMessageUnread(message.value.id)
    syncMessage(nextMessage)
    ElMessage.success(nextMessage.status === 'unread' ? '已恢复未读' : '已标记为已读')
  } finally {
    loading.value = false
  }
}

const submitReply = async () => {
  if (!message.value || !replyForm.reply_content.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }

  saving.value = true
  try {
    const nextMessage = await replyMessage(message.value.id, replyForm.reply_content.trim())
    syncMessage(nextMessage)
    ElMessage.success('留言已回复')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void recoverMessage()
})

const backToList = () => {
  removeMobileMessageSnapshot(messageId.value)
  void router.push('/m/messages')
}
</script>

<template>
  <section v-if="hasMessage" class="mobile-page detail-page">
    <article class="detail-toolbar">
      <div>
        <h2>{{ message?.product_name }}</h2>
        <p>{{ message?.miniapp_user_nickname || message?.miniapp_user_openid }}</p>
      </div>
      <button class="ghost-action" type="button" @click="backToList">返回</button>
    </article>

    <article class="detail-card message-body-card">
      <div class="detail-head-row">
        <span class="message-badge" :class="message?.status">{{ statusLabel }}</span>
        <button class="ghost-action compact" type="button" :disabled="loading" @click="toggleReadState">
          {{ message?.status === 'unread' ? '标记已读' : '恢复未读' }}
        </button>
      </div>
      <p class="message-body">{{ message?.content }}</p>
      <p class="message-time">{{ message?.created_at }}</p>
    </article>

    <article v-if="message?.reply_content" class="detail-card reply-history-card">
      <label>已回复</label>
      <p>{{ message.reply_content }}</p>
    </article>

    <article class="detail-card reply-editor-card">
      <h3>回复</h3>
      <el-input
        v-model="replyForm.reply_content"
        type="textarea"
        :rows="6"
        maxlength="500"
        show-word-limit
        placeholder="输入回复内容"
      />
      <button class="mobile-action-button" type="button" :disabled="saving" @click="submitReply">
        {{ saving ? '发送中…' : '发送回复' }}
      </button>
    </article>
  </section>
</template>

<style scoped>
.detail-page {
  gap: 12px;
}

.detail-toolbar,
.detail-card {
  border: 1px solid rgba(40, 55, 49, 0.08);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 28px rgba(20, 29, 25, 0.05);
}

.detail-toolbar {
  padding: 14px;
  border-radius: 18px 12px 18px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.detail-toolbar h2,
.detail-toolbar p,
.reply-history-card label,
.reply-history-card p,
.message-body,
.message-time,
.reply-editor-card h3 {
  margin: 0;
}

.detail-toolbar h2 {
  font-size: 20px;
  color: #20231f;
}

.detail-toolbar p,
.message-time,
.reply-history-card label {
  color: #68716b;
  font-size: 13px;
}

.detail-card {
  padding: 14px;
}

.message-body-card {
  border-radius: 12px 22px 18px 12px;
}

.reply-history-card {
  border-radius: 12px 18px 12px 22px;
}

.reply-editor-card {
  border-radius: 18px 12px 22px 12px;
}

.detail-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.message-badge {
  min-height: 28px;
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

.message-body {
  margin-top: 12px;
  color: #47514b;
  line-height: 1.65;
}

.message-time {
  margin-top: 12px;
}

.reply-history-card p {
  margin-top: 8px;
  color: #47514b;
  line-height: 1.65;
}

.reply-editor-card h3 {
  font-size: 18px;
  color: #20231f;
}

.reply-editor-card :deep(.el-textarea__inner) {
  margin-top: 12px;
  border-radius: 12px;
  background: rgba(248, 248, 245, 0.96);
}

.reply-editor-card .mobile-action-button {
  width: 100%;
  margin-top: 12px;
}

.ghost-action {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid rgba(57, 76, 64, 0.12);
  border-radius: 12px;
  background: rgba(249, 249, 247, 0.96);
  color: #334039;
  font-weight: 600;
}

.ghost-action.compact {
  min-height: 34px;
}
</style>
