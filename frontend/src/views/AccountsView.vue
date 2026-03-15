<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import {
  createAdminAccount,
  fetchAdminAccounts,
  resetAdminAccountPassword,
  updateAdminAccount,
  type AdminAccountItem,
} from '../api/modules/accounts'
import { changeAdminPassword } from '../api/modules/auth'

const loading = ref(false)
const accounts = ref<AdminAccountItem[]>([])
const createVisible = ref(false)
const passwordVisible = ref(false)
const resettingAccount = ref<AdminAccountItem | null>(null)

const createForm = reactive({
  username: '',
  display_name: '',
  password: '',
  status: 'active' as 'active' | 'disabled',
})

const changePasswordForm = reactive({
  current_password: '',
  new_password: '',
})

const resetPasswordForm = reactive({
  new_password: '',
})

const loadAccounts = async () => {
  loading.value = true
  try {
    accounts.value = await fetchAdminAccounts()
  } finally {
    loading.value = false
  }
}

const submitCreate = async () => {
  await createAdminAccount({
    username: createForm.username.trim(),
    display_name: createForm.display_name.trim(),
    password: createForm.password,
    status: createForm.status,
  })
  ElMessage.success('后台账号已创建')
  createVisible.value = false
  createForm.username = ''
  createForm.display_name = ''
  createForm.password = ''
  createForm.status = 'active'
  await loadAccounts()
}

const toggleStatus = async (account: AdminAccountItem) => {
  await updateAdminAccount(account.id, {
    status: account.status === 'active' ? 'disabled' : 'active',
  })
  ElMessage.success(account.status === 'active' ? '账号已停用' : '账号已启用')
  await loadAccounts()
}

const openResetPassword = (account: AdminAccountItem) => {
  resettingAccount.value = account
  resetPasswordForm.new_password = ''
  passwordVisible.value = true
}

const submitResetPassword = async () => {
  if (!resettingAccount.value) {
    return
  }
  await resetAdminAccountPassword(resettingAccount.value.id, resetPasswordForm.new_password)
  ElMessage.success('账号密码已重置')
  passwordVisible.value = false
  await loadAccounts()
}

const submitOwnPasswordChange = async () => {
  await changeAdminPassword({
    current_password: changePasswordForm.current_password,
    new_password: changePasswordForm.new_password,
  })
  ElMessage.success('当前账号密码已修改')
  changePasswordForm.current_password = ''
  changePasswordForm.new_password = ''
}

void loadAccounts()
</script>

<template>
  <section class="accounts-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">账号管理</h1>
        <p class="page-subtitle">维护后台登录账号，并支持当前账号修改密码。</p>
      </div>

      <div class="header-actions">
        <el-button plain @click="loadAccounts">刷新</el-button>
        <el-button type="primary" @click="createVisible = true">新增账号</el-button>
      </div>
    </div>

    <section class="content-card table-card">
      <el-table :data="accounts" v-loading="loading">
        <el-table-column prop="username" label="用户名" min-width="160" />
        <el-table-column prop="display_name" label="显示名" min-width="160" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最近登录" min-width="180" />
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button plain @click="toggleStatus(row)">
                {{ row.status === 'active' ? '停用' : '启用' }}
              </el-button>
              <el-button plain @click="openResetPassword(row)">重置密码</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="content-card form-card">
      <h2 class="section-title">修改当前账号密码</h2>
      <div class="password-grid">
        <el-input v-model="changePasswordForm.current_password" type="password" show-password placeholder="当前密码" />
        <el-input v-model="changePasswordForm.new_password" type="password" show-password placeholder="新密码，至少 8 位" />
        <el-button type="primary" @click="submitOwnPasswordChange">修改密码</el-button>
      </div>
    </section>

    <el-dialog v-model="createVisible" title="新增后台账号" width="560px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" />
        </el-form-item>
        <el-form-item label="显示名">
          <el-input v-model="createForm.display_name" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="createForm.status">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordVisible" title="重置账号密码" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="目标账号">
          <el-input :model-value="resettingAccount?.username ?? ''" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="resetPasswordForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.accounts-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header,
.header-actions,
.row-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.table-card,
.form-card {
  padding: 14px;
}

.section-title {
  margin: 0 0 14px;
  color: #35281d;
  font-size: 18px;
}

.password-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(180px, 1fr) minmax(220px, 1fr) auto;
}

@media (max-width: 900px) {
  .page-header,
  .header-actions {
    flex-direction: column;
  }

  .password-grid {
    grid-template-columns: 1fr;
  }
}
</style>
