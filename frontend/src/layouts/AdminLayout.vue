<script setup lang="ts">
import {
  CollectionTag,
  ChatLineRound,
  Expand,
  Fold,
  House,
  Promotion,
  Setting,
  SwitchButton,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const collapsed = ref(false)
const isPhone = ref(false)
const isTablet = ref(false)
const lastViewportMode = ref<'phone' | 'tablet' | 'desktop'>('desktop')

const PHONE_BREAKPOINT = 767
const TABLET_BREAKPOINT = 1180

const navigationGroups = [
  {
    title: '经营总览',
    items: [
      { index: '/dashboard', label: '概览', icon: House },
    ],
  },
  {
    title: '商品运营',
    items: [
      { index: '/products', label: '商品管理', icon: Promotion },
      { index: '/categories', label: '分类管理', icon: CollectionTag },
      { index: '/messages', label: '留言管理', icon: ChatLineRound },
    ],
  },
  {
    title: '系统支持',
    items: [
      { index: '/accounts', label: '账号管理', icon: UserFilled },
      { index: '/users', label: '用户列表', icon: User },
      { index: '/settings', label: '店铺设置', icon: Setting },
    ],
  },
] as const

const activeMenu = computed(() => {
  if (route.path.startsWith('/products/')) {
    return '/products'
  }
  return route.path
})

const menuCollapsed = computed(() => collapsed.value && !isPhone.value)
const currentTitle = computed(() => (route.meta.title as string) || '管理后台')

const syncViewportState = () => {
  const width = window.innerWidth
  const nextIsPhone = width <= PHONE_BREAKPOINT
  const nextIsTablet = width > PHONE_BREAKPOINT && width <= TABLET_BREAKPOINT
  const nextViewportMode = nextIsPhone ? 'phone' : nextIsTablet ? 'tablet' : 'desktop'

  isPhone.value = nextIsPhone
  isTablet.value = nextIsTablet

  if (nextViewportMode !== lastViewportMode.value) {
    if (nextViewportMode === 'tablet') {
      collapsed.value = true
    } else if (lastViewportMode.value === 'tablet' && nextViewportMode === 'desktop') {
      collapsed.value = false
    }

    lastViewportMode.value = nextViewportMode
  }
}

const handleSelect = (path: string) => {
  void router.push(path)
}

const handleLogout = () => {
  authStore.clearSession()
  void router.push('/login')
}

onMounted(() => {
  syncViewportState()
  window.addEventListener('resize', syncViewportState)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewportState)
})
</script>

<template>
  <div class="admin-layout" :class="{ phone: isPhone, tablet: isTablet, 'tablet-collapsed': isTablet && menuCollapsed }">
    <aside class="sidebar" :class="{ collapsed: menuCollapsed }">
      <div class="brand">
        <p class="brand-mark">YR</p>
        <div v-if="!menuCollapsed" class="brand-copy">
          <strong>YRFashion</strong>
          <span>商品运营后台</span>
        </div>
      </div>

      <div class="sidebar-groups">
        <section v-for="group in navigationGroups" :key="group.title" class="nav-section">
          <p v-if="!menuCollapsed" class="nav-section-title">{{ group.title }}</p>
          <el-menu
            class="sidebar-menu"
            :default-active="activeMenu"
            :collapse="menuCollapsed"
            @select="handleSelect"
          >
            <el-menu-item v-for="item in group.items" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </el-menu-item>
          </el-menu>
        </section>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="topbar-main">
          <button class="collapse-button" type="button" @click="collapsed = !collapsed">
            <el-icon><component :is="menuCollapsed ? Expand : Fold" /></el-icon>
          </button>

          <div class="topbar-copy">
            <strong>{{ currentTitle }}</strong>
          </div>
        </div>

        <div class="topbar-side">
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
  gap: 16px;
  padding: 16px;
}

.sidebar {
  width: 308px;
  height: calc(100vh - 32px);
  height: calc(100dvh - 32px);
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px 18px 18px;
  border: 1px solid var(--line-soft);
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(192, 138, 54, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(252, 251, 248, 0.98), rgba(244, 247, 242, 0.98));
  box-shadow: var(--shadow-md);
  transition: width 0.25s ease;
}

.sidebar.collapsed {
  width: 102px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  margin: 0;
  border-radius: 18px;
  background: linear-gradient(145deg, var(--brand), var(--brand-deep));
  color: #f7f7f3;
  font-family: 'Sora', sans-serif;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 16px 28px rgba(29, 67, 56, 0.24);
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-size: 16px;
  color: var(--ink-strong);
  font-family: 'Sora', sans-serif;
}

.brand-copy span,
.nav-section-title,
.user-meta span {
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7a877f;
}

.sidebar-groups {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
  padding-right: 4px;
  padding-top: 10px;
  border-top: 1px solid rgba(57, 76, 64, 0.08);
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-section-title {
  margin: 0;
  padding: 0 12px;
  font-size: 11px;
}

.sidebar-menu {
  border-right: 0;
  background: transparent;
}

:deep(.sidebar-menu .el-menu) {
  border-right: 0;
}

:deep(.sidebar-menu .el-menu-item) {
  height: 52px;
  margin-bottom: 4px;
  border-radius: 16px;
  color: #42544b;
  padding-right: 12px;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(47, 106, 88, 0.16), rgba(192, 138, 54, 0.12));
  color: var(--brand-deep);
}

:deep(.sidebar-menu .el-menu-item .el-icon) {
  font-size: 18px;
}

.workspace {
  min-width: 0;
  min-height: calc(100vh - 32px);
  min-height: calc(100dvh - 32px);
  display: flex;
  flex-direction: column;
  border: 1px solid var(--line-soft);
  border-radius: 32px;
  background: rgba(248, 250, 246, 0.96);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 28px;
  border-bottom: 1px solid rgba(57, 76, 64, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0));
}

.topbar-main,
.topbar-side {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-main {
  min-width: 0;
  flex: 1;
}

.collapse-button,
.logout-button {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(57, 76, 64, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--brand-deep);
  box-shadow: 0 10px 24px rgba(33, 50, 42, 0.08);
  cursor: pointer;
}

.topbar-copy {
  min-width: 0;
}

.topbar-copy strong {
  display: block;
  font-family: 'Sora', sans-serif;
  font-size: clamp(24px, 2.6vw, 30px);
  color: var(--ink-strong);
  line-height: 1.15;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 12px 7px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(57, 76, 64, 0.1);
}

.user-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--brand), var(--accent-gold));
  color: white;
  font-weight: 700;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-meta strong {
  color: var(--ink-strong);
  font-size: 14px;
}

.page-shell {
  padding: 16px 28px 28px;
}

.admin-layout.tablet {
  gap: 12px;
  padding: 12px;
}

.admin-layout.tablet .sidebar {
  height: calc(100vh - 24px);
  height: calc(100dvh - 24px);
}

.admin-layout.tablet .workspace {
  min-height: calc(100vh - 24px);
  min-height: calc(100dvh - 24px);
}

.admin-layout.tablet .topbar {
  padding: 16px 20px;
}

.admin-layout.tablet .page-shell {
  padding: 14px 20px 20px;
}

.admin-layout.tablet.tablet-collapsed {
  grid-template-columns: 104px minmax(0, 1fr);
}

.admin-layout.tablet.tablet-collapsed .sidebar {
  width: 104px;
  padding: 18px 12px;
}

.admin-layout.tablet.tablet-collapsed .brand {
  justify-content: center;
  padding: 0;
}

.admin-layout.tablet.tablet-collapsed .sidebar-groups {
  gap: 8px;
  padding-top: 8px;
  padding-right: 0;
}

.admin-layout.tablet.tablet-collapsed :deep(.sidebar-menu .el-menu-item) {
  justify-content: center;
  padding: 0;
}

.admin-layout.tablet.tablet-collapsed .topbar-copy strong {
  font-size: 30px;
}

@media (max-width: 767px) {
  .admin-layout.phone {
    grid-template-columns: 1fr;
    gap: 0;
    padding: 0;
  }

  .admin-layout.phone .sidebar {
    position: static;
    width: auto;
    height: auto;
    gap: 10px;
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    border-top: 0;
    box-shadow: none;
  }

  .admin-layout.phone .topbar {
    padding: 16px 18px;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .admin-layout.phone .workspace {
    min-height: auto;
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .admin-layout.phone .page-shell {
    padding: 18px;
  }

  .admin-layout.phone .topbar-main,
  .admin-layout.phone .topbar-side {
    width: 100%;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .admin-layout.phone .topbar-copy strong {
    font-size: 24px;
  }
}
</style>
