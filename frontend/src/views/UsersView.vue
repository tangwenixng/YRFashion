<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { ref } from 'vue'

import {
  approveMiniappUserAvatar,
  fetchMiniappUsers,
  rejectMiniappUserAvatar,
  type MiniappUserItem,
} from '../api/modules/users'

const loading = ref(false)
const actionLoadingUserId = ref<number | null>(null)
const keyword = ref('')
const avatarReviewStatus = ref<'' | 'pending' | 'approved' | 'rejected'>('')
const sort = ref<'last_visit_desc' | 'first_visit_desc'>('last_visit_desc')
const users = ref<MiniappUserItem[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const loadUsers = async () => {
  loading.value = true
  try {
    const result = await fetchMiniappUsers({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim(),
      avatar_review_status: avatarReviewStatus.value,
      sort: sort.value,
    })
    users.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  page.value = 1
  await loadUsers()
}

const handlePageChange = async (nextPage: number) => {
  page.value = nextPage
  await loadUsers()
}

const handlePageSizeChange = async (nextPageSize: number) => {
  pageSize.value = nextPageSize
  page.value = 1
  await loadUsers()
}

const replaceUser = (nextUser: MiniappUserItem) => {
  users.value = users.value.map((item) => (item.id === nextUser.id ? nextUser : item))
}

const avatarStatusTagTypeMap = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
} as const

const avatarStatusLabelMap = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
} as const

const handleApproveAvatar = async (user: MiniappUserItem) => {
  actionLoadingUserId.value = user.id
  try {
    const result = await approveMiniappUserAvatar(user.id)
    replaceUser(result)
    ElMessage.success('头像已审核通过')
  } catch (error) {
    const message =
      (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      '头像通过失败'
    ElMessage.error(message)
  } finally {
    actionLoadingUserId.value = null
  }
}

const handleRejectAvatar = async (user: MiniappUserItem) => {
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入驳回原因，用户会在小程序侧看到这条提示。',
      '驳回头像',
      {
        confirmButtonText: '确认驳回',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：头像主体不清晰，请重新上传正面清晰头像',
        inputValue: user.avatar_reject_reason || '',
      },
    )
    actionLoadingUserId.value = user.id
    const result = await rejectMiniappUserAvatar(user.id, value || '')
    replaceUser(result)
    ElMessage.success('头像已驳回')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    const message =
      (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      '头像驳回失败'
    ElMessage.error(message)
  } finally {
    actionLoadingUserId.value = null
  }
}

void loadUsers()
</script>

<template>
  <section class="users-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">用户列表</h1>
        <p class="page-subtitle">这里记录的是小程序访问用户的基础标识信息，不依赖完整微信资料。</p>
      </div>

      <div class="header-actions">
        <el-input
          v-model="keyword"
          placeholder="按昵称 / openid 搜索"
          clearable
          style="width: 280px"
          @keyup.enter="applyFilters"
        />
        <el-select v-model="sort" style="width: 180px" @change="applyFilters">
          <el-option label="最近访问优先" value="last_visit_desc" />
          <el-option label="首次访问优先" value="first_visit_desc" />
        </el-select>
        <el-select v-model="avatarReviewStatus" style="width: 180px" @change="applyFilters">
          <el-option label="全部审核状态" value="" />
          <el-option label="待审核头像" value="pending" />
          <el-option label="已通过头像" value="approved" />
          <el-option label="已驳回头像" value="rejected" />
        </el-select>
        <el-button type="primary" @click="applyFilters">查询</el-button>
      </div>
    </div>

    <section class="content-card table-card">
      <el-table :data="users" v-loading="loading">
        <el-table-column label="头像" min-width="160">
          <template #default="{ row }">
            <div class="avatar-cell">
              <img
                v-if="row.pending_avatar_url || row.avatar_url"
                :src="row.pending_avatar_url || row.avatar_url || ''"
                class="avatar-image"
                alt=""
              />
              <div v-else class="avatar-fallback">无头像</div>
              <span v-if="row.pending_avatar_url" class="avatar-caption">当前显示待审头像</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" min-width="140">
          <template #default="{ row }">
            {{ row.nickname || '未授权昵称' }}
          </template>
        </el-table-column>
        <el-table-column label="头像审核" min-width="220">
          <template #default="{ row }">
            <div class="review-cell">
              <el-tag :type="avatarStatusTagTypeMap[row.avatar_review_status]">
                {{ avatarStatusLabelMap[row.avatar_review_status] }}
              </el-tag>
              <span v-if="row.avatar_reject_reason" class="review-reason">
                {{ row.avatar_reject_reason }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="openid" label="OpenID" min-width="260" />
        <el-table-column prop="unionid" label="UnionID" min-width="220">
          <template #default="{ row }">
            {{ row.unionid || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="first_visit_at" label="首次访问" min-width="180" />
        <el-table-column prop="last_visit_at" label="最近访问" min-width="180" />
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button
                v-if="row.avatar_review_status === 'pending' && row.pending_avatar_url"
                type="success"
                link
                :loading="actionLoadingUserId === row.id"
                @click="handleApproveAvatar(row)"
              >
                通过
              </el-button>
              <el-button
                v-if="row.avatar_review_status === 'pending' && row.pending_avatar_url"
                type="danger"
                link
                :loading="actionLoadingUserId === row.id"
                @click="handleRejectAvatar(row)"
              >
                驳回
              </el-button>
              <span v-if="row.avatar_review_status !== 'pending' || !row.pending_avatar_url" class="muted">
                -
              </span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <span class="muted">共 {{ total }} 条</span>
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
  </section>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header,
.header-actions,
.pagination-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.table-card {
  padding: 14px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

:deep(.el-table) {
  min-width: 1360px;
}

.avatar-cell,
.review-cell,
.action-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-image {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 6px 18px rgba(71, 46, 30, 0.12);
}

.avatar-fallback {
  display: flex;
  width: 56px;
  height: 56px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3e6d8;
  color: #8f6f57;
  font-size: 12px;
}

.avatar-caption,
.review-reason {
  color: #907e6a;
  font-size: 12px;
  line-height: 1.6;
}

.pagination-bar {
  align-items: center;
  margin-top: 16px;
}

.muted {
  color: #907e6a;
  font-size: 13px;
}

@media (max-width: 1024px) {
  .page-header,
  .header-actions,
  .pagination-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
