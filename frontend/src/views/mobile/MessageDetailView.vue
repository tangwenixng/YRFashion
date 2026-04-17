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
  <section class="mobile-page" v-if="hasMessage">
    <article class="mobile-card mobile-panel detail-panel">
      <div class="card-title-row">
        <div>
          <h2 class="mobile-section-title">留言详情</h2>
          <p class="mobile-muted">{{ message?.product_name }}</p>
        </div>
        <el-button plain @click="backToList">返回</el-button>
      </div>

      <div class="meta-block">
        <strong>{{ message?.miniapp_user_nickname || message?.miniapp_user_openid }}</strong>
        <span class="mobile-muted">{{ message?.created_at }}</span>
      </div>

      <div class="message-bubble">
        {{ message?.content }}
      </div>

      <div v-if="message?.reply_content" class="reply-card">
        <label>已回复</label>
        <p>{{ message.reply_content }}</p>
      </div>
    </article>

    <article class="mobile-card mobile-panel reply-panel">
      <div class="card-title-row">
        <h2 class="mobile-section-title">回复与状态</h2>
        <el-button plain :loading="loading" @click="toggleReadState">
          {{ message?.status === 'unread' ? '标记已读' : '恢复未读' }}
        </el-button>
      </div>

      <el-input v-model="replyForm.reply_content" type="textarea" :rows="6" maxlength="500" show-word-limit placeholder="输入回复内容" />
      <el-button class="reply-submit" type="primary" :loading="saving" @click="submitReply">发送回复</el-button>
    </article>
  </section>
</template>

<style scoped>
.mobile-panel {
  padding: 16px;
}

.detail-panel,
.reply-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.meta-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble,
.reply-card {
  padding: 16px;
  border-radius: 18px;
  line-height: 1.7;
}

.message-bubble {
  background: rgba(47, 106, 88, 0.08);
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
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--ink-soft);
}

.reply-submit {
  margin-top: 14px;
  height: 46px;
  border-radius: 18px;
}
</style>
