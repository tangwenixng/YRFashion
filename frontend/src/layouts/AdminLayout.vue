<script setup lang="ts">
import {
  CollectionTag,
  ChatLineRound,
  Fold,
  House,
  Promotion,
  Setting,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const collapsed = ref(false)

const menuItems = [
  { index: '/dashboard', label: '概览', icon: House },
  { index: '/categories', label: '分类管理', icon: CollectionTag },
  { index: '/products', label: '商品管理', icon: Promotion },
  { index: '/messages', label: '留言管理', icon: ChatLineRound },
  { index: '/users', label: '用户列表', icon: User },
  { index: '/settings', label: '店铺设置', icon: Setting },
]

const activeMenu = computed(() => route.path)

const handleSelect = (path: string) => {
  void router.push(path)
}

const handleLogout = () => {
  authStore.clearSession()
  void router.push('/login')
}
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand">
        <p class="brand-mark">YR</p>
        <div v-if="!collapsed" class="brand-copy">
          <strong>YRFasion</strong>
          <span>Admin Console</span>
        </div>
      </div>

      <el-menu
        class="sidebar-menu"
        :default-active="activeMenu"
        :collapse="collapsed"
        @select="handleSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <button class="collapse-button" type="button" @click="collapsed = !collapsed">
          <el-icon><Fold /></el-icon>
        </button>

        <div class="topbar-center">
          <p class="topbar-label">RESPONSIVE WEB BACKOFFICE</p>
          <strong>{{ (route.meta.title as string) || '管理后台' }}</strong>
        </div>

        <div class="topbar-user">
          <div class="user-pill">
            <span class="user-avatar">{{ authStore.profile?.display_name?.slice(0, 1) ?? 'A' }}</span>
            <div class="user-meta">
              <strong>{{ authStore.profile?.display_name ?? 'Admin' }}</strong>
              <span>{{ authStore.profile?.username }}</span>
            </div>
          </div>

          <button class="logout-button" type="button" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </button>
        </div>
      </header>

      <main class="page-shell">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: auto 1fr;
}

.sidebar {
  width: 280px;
  padding: 24px 18px;
  border-right: 1px solid rgba(84, 60, 37, 0.12);
  background:
    linear-gradient(180deg, rgba(255, 251, 245, 0.9), rgba(246, 236, 223, 0.96)),
    rgba(255, 255, 255, 0.64);
  backdrop-filter: blur(18px);
  transition: width 0.25s ease;
}

.sidebar.collapsed {
  width: 92px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
  padding: 8px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  margin: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #9c6a43, #543621);
  color: #fff4e6;
  font-family: 'Fraunces', serif;
  font-size: 20px;
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-size: 16px;
  color: #2f241a;
}

.brand-copy span,
.topbar-label,
.user-meta span {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #8d765f;
}

.sidebar-menu {
  border-right: 0;
  background: transparent;
}

:deep(.sidebar-menu .el-menu-item) {
  height: 52px;
  margin-bottom: 8px;
  border-radius: 16px;
  color: #5c4a38;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: rgba(139, 94, 60, 0.12);
  color: #593820;
}

.workspace {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: space-between;
  padding: 20px 28px;
}

.collapse-button,
.logout-button {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 16px;
  background: rgba(255, 249, 240, 0.9);
  color: #4c3522;
  box-shadow: 0 10px 30px rgba(110, 78, 47, 0.1);
  cursor: pointer;
}

.topbar-center {
  flex: 1;
}

.topbar-center strong {
  display: block;
  margin-top: 4px;
  font-family: 'Fraunces', serif;
  font-size: 28px;
  color: #2f241a;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px 8px 10px;
  border-radius: 999px;
  background: rgba(255, 250, 244, 0.86);
  border: 1px solid rgba(117, 86, 53, 0.12);
}

.user-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #7e5534, #bc8a60);
  color: white;
  font-weight: 700;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-meta strong {
  color: #35281d;
  font-size: 14px;
}

.page-shell {
  padding: 8px 28px 28px;
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }

  .topbar {
    padding: 18px 18px 0;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .page-shell {
    padding: 18px;
  }

  .topbar-center {
    width: 100%;
    order: 3;
  }
}
</style>
