<script setup lang="ts">
import { computed, ref } from 'vue'

import { fetchMiniappUsers, type MiniappUserItem } from '../api/modules/users'

const loading = ref(false)
const keyword = ref('')
const users = ref<MiniappUserItem[]>([])

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await fetchMiniappUsers()
  } finally {
    loading.value = false
  }
}

const visibleUsers = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) {
    return users.value
  }

  return users.value.filter((user) => {
    return [user.nickname, user.openid, user.unionid].some((value) =>
      String(value ?? '')
        .toLowerCase()
        .includes(text),
    )
  })
})

void loadUsers()
</script>

<template>
  <section class="users-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">用户列表</h1>
        <p class="page-subtitle">这里记录的是小程序访问用户的基础标识信息，不依赖完整微信资料。</p>
      </div>

      <el-input v-model="keyword" placeholder="按昵称 / openid 搜索" clearable style="width: 280px" />
    </div>

    <section class="content-card table-card">
      <el-table :data="visibleUsers" v-loading="loading">
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
    </section>
  </section>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.table-card {
  padding: 14px;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
