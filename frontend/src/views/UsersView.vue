<script setup lang="ts">
import { ref } from 'vue'

import { fetchMiniappUsers, type MiniappUserItem } from '../api/modules/users'

const loading = ref(false)
const keyword = ref('')
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
        <el-button type="primary" @click="applyFilters">查询</el-button>
      </div>
    </div>

    <section class="content-card table-card">
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="nickname" label="昵称" min-width="140">
          <template #default="{ row }">
            {{ row.nickname || '未授权昵称' }}
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
}

.pagination-bar {
  align-items: center;
  margin-top: 16px;
}

.muted {
  color: #907e6a;
  font-size: 13px;
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
