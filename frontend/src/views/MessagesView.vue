<script setup lang="ts">
import { ChatDotRound, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import { fetchProducts, type ProductItem } from '../api/modules/products'
import {
  batchMarkMessageRead,
  fetchMessages,
  markMessageRead,
  markMessageUnread,
  replyMessage,
  type MessageItem,
} from '../api/modules/messages'

const loading = ref(false)
const messages = ref<MessageItem[]>([])
const products = ref<ProductItem[]>([])
const statusFilter = ref<'all' | 'unread' | 'read' | 'replied'>('all')
const productFilter = ref<number | null>(null)
const replyVisible = ref(false)
const replyingMessage = ref<MessageItem | null>(null)
const selectedMessageIds = ref<number[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const replyForm = reactive({
  reply_content: '',
})

const loadMessages = async () => {
  loading.value = true
  try {
    const result = await fetchMessages({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value === 'all' ? undefined : statusFilter.value,
      product_id: productFilter.value,
    })
    messages.value = result.items
    total.value = result.total
    selectedMessageIds.value = []
  } finally {
    loading.value = false
  }
}

const loadProducts = async () => {
  const result = await fetchProducts({ page: 1, page_size: 50 })
  products.value = result.items
}

const filteredCountLabel = computed(() => {
  if (statusFilter.value === 'all') {
    return `共 ${total.value} 条留言`
  }
  return `${statusFilter.value} 状态 ${total.value} 条`
})

const applyFilters = async () => {
  page.value = 1
  await loadMessages()
}

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

const batchSetRead = async () => {
  if (!selectedMessageIds.value.length) {
    ElMessage.warning('请先选择留言')
    return
  }

  await batchMarkMessageRead(selectedMessageIds.value)
  ElMessage.success('已批量标记为已读')
  await loadMessages()
}

const handleSelectionChange = (selection: MessageItem[]) => {
  selectedMessageIds.value = selection.map((item) => item.id)
}

const handlePageChange = async (nextPage: number) => {
  page.value = nextPage
  await loadMessages()
}

const handlePageSizeChange = async (nextPageSize: number) => {
  pageSize.value = nextPageSize
  page.value = 1
  await loadMessages()
}

void loadProducts()
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
        <el-select v-model="statusFilter" style="width: 160px" @change="applyFilters">
          <el-option label="全部状态" value="all" />
          <el-option label="未读" value="unread" />
          <el-option label="已读" value="read" />
          <el-option label="已回复" value="replied" />
        </el-select>
        <el-select v-model="productFilter" clearable style="width: 220px" placeholder="按商品筛选" @change="applyFilters">
          <el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" />
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
        <el-button plain :disabled="!selectedMessageIds.length" @click="batchSetRead">批量标为已读</el-button>
      </div>

      <el-table :data="messages" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" />
        <el-table-column label="留言内容" min-width="520">
          <template #default="{ row }">
            <article class="message-item">
              <div class="message-main">
                <div class="message-head">
                  <div class="message-origin">
                    <div v-if="row.miniapp_user_avatar_url" class="message-avatar-frame">
                      <img :src="row.miniapp_user_avatar_url" class="message-avatar" alt="" />
                    </div>
                    <div v-else class="message-avatar-fallback">
                      {{ (row.miniapp_user_nickname || row.miniapp_user_openid).slice(0, 1).toUpperCase() }}
                    </div>

                    <div>
                      <strong>{{ row.product_name }}</strong>
                      <p>来自 {{ row.miniapp_user_nickname || row.miniapp_user_openid }}</p>
                    </div>
                  </div>
                  <el-tag :type="row.status === 'unread' ? 'danger' : row.status === 'replied' ? 'success' : 'warning'">
                    {{ row.status }}
                  </el-tag>
                </div>

                <div class="message-bubble">
                  <el-icon><ChatDotRound /></el-icon>
                  <p>{{ row.content }}</p>
                </div>

                <div v-if="row.reply_content" class="reply-block">
                  <label>已回复</label>
                  <p>{{ row.reply_content }}</p>
                </div>
              </div>
            </article>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="message-actions">
              <el-button size="small" plain @click="openReply(row)">回复</el-button>
              <el-button
                v-if="row.status === 'unread'"
                size="small"
                plain
                @click="setRead(row)"
              >
                标为已读
              </el-button>
              <el-button
                v-else
                size="small"
                plain
                @click="setUnread(row)"
              >
                标为未读
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <span class="messages-meta">{{ filteredCountLabel }}</span>
        <el-pagination
          background
          layout="prev, pager, next, sizes"
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
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
.message-bubble,
.messages-meta,
.pagination-bar {
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
  align-items: center;
}

.message-item {
  padding: 4px 0;
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
  align-items: center;
  justify-content: flex-start;
}

.pagination-bar {
  margin-top: 18px;
  align-items: center;
}

@media (max-width: 900px) {
  .page-header,
  .header-actions,
  .pagination-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
