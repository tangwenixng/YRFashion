<script setup lang="ts">
import { ChatDotRound, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import {
  fetchMessages,
  markMessageRead,
  markMessageUnread,
  replyMessage,
  type MessageItem,
} from '../api/modules/messages'

const loading = ref(false)
const messages = ref<MessageItem[]>([])
const statusFilter = ref<'all' | 'unread' | 'read' | 'replied'>('all')
const replyVisible = ref(false)
const replyingMessage = ref<MessageItem | null>(null)
const replyForm = reactive({
  reply_content: '',
})

const loadMessages = async () => {
  loading.value = true
  try {
    messages.value = await fetchMessages(statusFilter.value === 'all' ? undefined : statusFilter.value)
  } finally {
    loading.value = false
  }
}

const filteredCountLabel = computed(() => {
  if (statusFilter.value === 'all') {
    return `共 ${messages.value.length} 条留言`
  }
  return `${statusFilter.value} 状态 ${messages.value.length} 条`
})

const openReply = (message: MessageItem) => {
  replyingMessage.value = message
  replyForm.reply_content = message.reply_content ?? ''
  replyVisible.value = true
}

const submitReply = async () => {
  if (!replyingMessage.value || !replyForm.reply_content.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }

  await replyMessage(replyingMessage.value.id, replyForm.reply_content.trim())
  ElMessage.success('留言已回复')
  replyVisible.value = false
  await loadMessages()
}

const setRead = async (message: MessageItem) => {
  await markMessageRead(message.id)
  ElMessage.success('已标记为已读')
  await loadMessages()
}

const setUnread = async (message: MessageItem) => {
  await markMessageUnread(message.id)
  ElMessage.success('已恢复为未读')
  await loadMessages()
}

void loadMessages()
</script>

<template>
  <section class="messages-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">留言管理</h1>
        <p class="page-subtitle">集中处理小程序侧的商品咨询，先把未读和已回复分清楚。</p>
      </div>

      <div class="header-actions">
        <el-select v-model="statusFilter" style="width: 160px" @change="loadMessages">
          <el-option label="全部状态" value="all" />
          <el-option label="未读" value="unread" />
          <el-option label="已读" value="read" />
          <el-option label="已回复" value="replied" />
        </el-select>
        <el-button plain @click="loadMessages">
          <el-icon><RefreshRight /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <section class="content-card messages-card">
      <div class="messages-meta">
        <span>{{ filteredCountLabel }}</span>
      </div>

      <div v-loading="loading" class="message-list">
        <article v-for="message in messages" :key="message.id" class="message-item">
          <div class="message-main">
            <div class="message-head">
              <div class="message-origin">
                <div v-if="message.miniapp_user_avatar_url" class="message-avatar-frame">
                  <img :src="message.miniapp_user_avatar_url" class="message-avatar" alt="" />
                </div>
                <div v-else class="message-avatar-fallback">
                  {{ (message.miniapp_user_nickname || message.miniapp_user_openid).slice(0, 1).toUpperCase() }}
                </div>

                <div>
                <strong>{{ message.product_name }}</strong>
                <p>
                  来自
                  {{ message.miniapp_user_nickname || message.miniapp_user_openid }}
                </p>
                </div>
              </div>
              <el-tag :type="message.status === 'unread' ? 'danger' : message.status === 'replied' ? 'success' : 'warning'">
                {{ message.status }}
              </el-tag>
            </div>

            <div class="message-bubble">
              <el-icon><ChatDotRound /></el-icon>
              <p>{{ message.content }}</p>
            </div>

            <div v-if="message.reply_content" class="reply-block">
              <label>已回复</label>
              <p>{{ message.reply_content }}</p>
            </div>
          </div>

          <div class="message-actions">
            <el-button size="small" plain @click="openReply(message)">回复</el-button>
            <el-button
              v-if="message.status === 'unread'"
              size="small"
              plain
              @click="setRead(message)"
            >
              标为已读
            </el-button>
            <el-button
              v-else
              size="small"
              plain
              @click="setUnread(message)"
            >
              标为未读
            </el-button>
          </div>
        </article>
      </div>
    </section>

    <el-dialog v-model="replyVisible" title="回复留言" width="620px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="原留言">
          <el-input :model-value="replyingMessage?.content ?? ''" type="textarea" :rows="4" disabled />
        </el-form-item>
        <el-form-item label="回复内容">
          <el-input v-model="replyForm.reply_content" type="textarea" :rows="5" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="replyVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReply">提交回复</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.messages-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header,
.header-actions,
.message-head,
.message-actions,
.message-bubble {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.messages-card {
  padding: 22px;
}

.messages-meta {
  margin-bottom: 16px;
  color: #7f6d59;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 18px;
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 251, 245, 0.86);
  border: 1px solid rgba(126, 97, 69, 0.12);
}

.message-head strong {
  display: block;
  color: #2d241b;
}

.message-head p {
  margin: 6px 0 0;
  color: #866f58;
}

.message-origin {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-avatar-frame,
.message-avatar-fallback {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  overflow: hidden;
  flex-shrink: 0;
}

.message-avatar-frame {
  border: 1px solid rgba(126, 97, 69, 0.16);
  background: rgba(255, 255, 255, 0.88);
}

.message-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.message-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #dec0a4 0%, #b48b63 100%);
  color: #fffaf4;
  font-size: 16px;
  font-weight: 700;
}

.message-bubble {
  justify-content: flex-start;
  padding: 16px;
  margin-top: 16px;
  border-radius: 18px;
  background: rgba(139, 94, 60, 0.08);
  color: #463526;
}

.message-bubble p {
  margin: 0;
  line-height: 1.8;
}

.reply-block {
  margin-top: 16px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(53, 105, 74, 0.08);
}

.reply-block label {
  display: block;
  margin-bottom: 8px;
  color: #33694f;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.reply-block p {
  margin: 0;
  color: #425446;
  line-height: 1.8;
}

.message-actions {
  flex-direction: column;
  align-items: stretch;
}

@media (max-width: 900px) {
  .page-header,
  .header-actions,
  .message-item {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
