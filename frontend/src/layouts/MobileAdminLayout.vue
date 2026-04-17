<script setup lang="ts">
import { ChatLineRound, House, Promotion, SwitchButton } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AdminExperienceSwitch from '../components/AdminExperienceSwitch.vue'
import { useAuthStore } from '../stores/auth'
import { resolvePathForExperience, writeAdminExperienceOverride } from '../router/deviceExperience'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentTitle = computed(() => (route.meta.title as string) || '手机后台')
const tabs = [
  { label: '首页', icon: House, path: '/m/home' },
  { label: '商品', icon: Promotion, path: '/m/products' },
  { label: '留言', icon: ChatLineRound, path: '/m/messages' },
]

const activeTab = computed(() => {
  if (route.path.startsWith('/m/products')) {
    return '/m/products'
  }
  if (route.path.startsWith('/m/messages')) {
    return '/m/messages'
  }
  return '/m/home'
})

const switchToDesktop = async () => {
  writeAdminExperienceOverride('force-desktop')
  await router.push(resolvePathForExperience(route.fullPath, 'desktop'))
}

const logout = () => {
  authStore.clearSession()
  void router.push('/m/login')
}
</script>

<template>
  <div class="mobile-admin-layout">
    <header class="mobile-header mobile-card">
      <div>
        <p class="mobile-kicker">YRFashion Mobile</p>
        <h1>{{ currentTitle }}</h1>
      </div>
      <button class="mobile-header-action" type="button" @click="logout">
        <el-icon><SwitchButton /></el-icon>
      </button>
    </header>

    <section class="mobile-toolbar mobile-card">
      <div class="mobile-user-pill">
        <span>{{ authStore.profile?.display_name ?? 'Admin' }}</span>
        <small>{{ authStore.profile?.username }}</small>
      </div>
      <div class="mobile-toolbar-actions">
        <button class="link-button" type="button" @click="switchToDesktop">切到桌面版</button>
        <AdminExperienceSwitch compact />
      </div>
    </section>

    <main class="mobile-shell">
      <router-view />
    </main>

    <nav class="mobile-nav mobile-card">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="mobile-nav-item"
        :class="{ active: activeTab === tab.path }"
        type="button"
        @click="router.push(tab.path)"
      >
        <el-icon><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
.mobile-admin-layout {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 14px calc(96px + env(safe-area-inset-bottom));
}

.mobile-header,
.mobile-toolbar,
.mobile-nav {
  padding: 16px;
}

.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mobile-kicker {
  margin: 0 0 6px;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ink-soft);
}

.mobile-header h1 {
  margin: 0;
  font-family: 'Sora', sans-serif;
  font-size: 24px;
  line-height: 1.1;
}

.mobile-header-action,
.link-button,
.mobile-nav-item {
  font: inherit;
}

.mobile-header-action {
  width: 42px;
  height: 42px;
  border: 0;
  border-radius: 14px;
  background: rgba(47, 106, 88, 0.1);
  color: var(--brand-deep);
}

.mobile-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-user-pill {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mobile-user-pill span {
  font-weight: 700;
}

.mobile-user-pill small {
  color: var(--ink-soft);
}

.mobile-toolbar-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-button {
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--brand);
}

.mobile-shell {
  min-height: 0;
}

.mobile-nav {
  position: fixed;
  left: 14px;
  right: 14px;
  bottom: calc(14px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  z-index: 10;
}

.mobile-nav-item {
  min-height: 54px;
  border: 0;
  border-radius: 18px;
  background: transparent;
  color: var(--ink-soft);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.mobile-nav-item.active {
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.mobile-nav-item :deep(.el-icon) {
  font-size: 18px;
}

.mobile-nav-item span {
  font-size: 12px;
  font-weight: 600;
}
</style>
