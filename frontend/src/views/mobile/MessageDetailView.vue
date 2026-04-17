<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { markMessageRead, markMessageUnread, replyMessage, type MessageItem } from '../../api/modules/messages'
import { readMobileMessageSnapshot, removeMobileMessageSnapshot, saveMobileMessageSnapshot } from './messageCache'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const message = ref<MessageItem | null>(null)
const replyForm = reactive({
  reply_content: '',
})

const messageId = computed(() => String(route.params.id || ''))
const hasMessage = computed(() => Boolean(message.value))

const syncMessage = (nextMessage: MessageItem) => {
  message.value = nextMessage
  replyForm.reply_content = nextMessage.reply_content ?? ''
  saveMobileMessageSnapshot(nextMessage)
}

const recoverMessage = () => {
  const cachedMessage = readMobileMessageSnapshot(messageId.value)
  if (!cachedMessage) {
    ElMessage.warning('留言上下文已失效，已返回列表重新打开。')
    void router.replace('/m/messages')
    return
  }

  syncMessage(cachedMessage)
}

const toggleReadState = async () => {
  if (!message.value) {
    return
  }

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
  recoverMessage()
})

const backToList = () => {
  removeMobileMessageSnapshot(messageId.value)
  void router.push('/m/messages')
}
</script>

<template>
  <section v-if="hasMessage" class="mobile-page detail-page">
    <article class="mobile-card detail-hero-card">
      <span class="section-kicker">留言详情</span>
      <h2 class="mobile-section-title">{{ message?.product_name }}</h2>
      <p class="mobile-muted">来自 {{ message?.miniapp_user_nickname || message?.miniapp_user_openid }} · {{ message?.created_at }}</p>
    </article>

    <article class="mobile-card mobile-panel detail-panel">
      <div class="message-status-row">
        <span class="mobile-chip soft-chip">{{ message?.status === 'unread' ? '待优先处理' : message?.status === 'replied' ? '已回复' : '已读' }}</span>
        <button class="mobile-action-button secondary status-button" type="button" :disabled="loading" @click="toggleReadState">
          {{ message?.status === 'unread' ? '标记已读' : '恢复未读' }}
        </button>
      </div>

      <div class="message-bubble">
        {{ message?.content }}
      </div>

      <div v-if="message?.reply_content" class="reply-card">
        <label>当前回复</label>
        <p>{{ message.reply_content }}</p>
      </div>
    </article>

    <article class="mobile-card mobile-panel reply-panel">
      <div class="reply-title-row">
        <div>
          <h3>快速回复</h3>
          <p class="mobile-muted">处理后即可返回列表继续下一条。</p>
        </div>
      </div>

      <el-input
        v-model="replyForm.reply_content"
        type="textarea"
        :rows="7"
        maxlength="500"
        show-word-limit
        placeholder="输入回复内容"
      />

      <div class="reply-action-row">
        <button class="mobile-action-button secondary" type="button" @click="backToList">返回列表</button>
        <button class="mobile-action-button" type="button" :disabled="saving" @click="submitReply">
          {{ saving ? '发送中…' : '发送回复' }}
        </button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.detail-page {
  padding-bottom: 8px;
}

.detail-hero-card,
.mobile-panel {
  padding: 18px;
}

.detail-hero-card {
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 244, 238, 0.96));
}

.detail-hero-card p {
  margin: 12px 0 0;
}

.detail-panel,
.reply-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-status-row,
.reply-action-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.soft-chip {
  width: fit-content;
  background: rgba(192, 138, 54, 0.12);
  color: #805b2a;
}

.status-button {
  width: 100%;
}

.message-bubble,
.reply-card {
  padding: 18px;
  border-radius: 24px;
  line-height: 1.75;
}

.message-bubble {
  background: rgba(47, 106, 88, 0.08);
  color: #455049;
}

.reply-card {
  background: rgba(192, 138, 54, 0.08);
}

.reply-card label,
.reply-card p {
  margin: 0;
}

.reply-card label {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--mobile-muted);
}

.reply-title-row h3 {
  margin: 0;
  font-size: 20px;
}

.reply-title-row p {
  margin: 8px 0 0;
}

.reply-panel :deep(.el-textarea__inner) {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}
</style>
