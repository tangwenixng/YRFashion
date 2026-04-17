<script setup lang="ts">
import { ArrowLeft, ChatLineRound, House, Promotion, SwitchButton } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

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

const currentTitle = computed(() => (route.meta.title as string) || '手机后台')
const canGoBack = computed(() => route.path !== '/m/home')

const goBack = () => {
  if (canGoBack.value) {
    router.back()
    return
  }

  void router.push('/m/home')
}

const logout = () => {
  authStore.clearSession()
  void router.push('/m/login')
}
</script>

<template>
  <div class="mobile-admin-layout">
    <header class="mobile-topbar">
      <button class="topbar-icon-button" :aria-label="canGoBack ? '返回上一页' : '返回首页'" type="button" @click="goBack">
        <el-icon><ArrowLeft v-if="canGoBack" /><House v-else /></el-icon>
      </button>

      <div class="topbar-title-block">
        <h1>{{ currentTitle }}</h1>
        <p>{{ authStore.profile?.display_name || authStore.profile?.username || 'Admin' }}</p>
      </div>

      <button class="topbar-icon-button accent" aria-label="退出登录" type="button" @click="logout">
        <el-icon><SwitchButton /></el-icon>
      </button>
    </header>

    <main id="mobile-main-content" class="mobile-shell">
      <router-view />
    </main>

    <nav class="mobile-nav" aria-label="手机后台导航">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="mobile-nav-item"
        :class="{ active: activeTab === tab.path }"
        type="button"
        @click="router.push(tab.path)"
      >
        <span class="mobile-nav-icon">
          <el-icon><component :is="tab.icon" /></el-icon>
        </span>
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
  padding: 10px 10px calc(90px + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, #f3f4ef 0%, #eaeee7 42%, #e5eae2 100%);
  overscroll-behavior-y: contain;
}

.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) 40px;
  align-items: center;
  gap: 10px;
  padding: 8px 2px 2px;
  backdrop-filter: blur(10px);
}

.topbar-title-block {
  min-width: 0;
}

.topbar-title-block h1,
.topbar-title-block p {
  margin: 0;
}

.topbar-title-block h1 {
  font-size: 26px;
  line-height: 1.05;
  color: #1f2320;
  letter-spacing: -0.02em;
}

.topbar-title-block p {
  margin-top: 4px;
  font-size: 12px;
  color: #727a73;
}

.topbar-icon-button {
  width: 40px;
  height: 40px;
  border: 1px solid rgba(34, 50, 44, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  color: #2f3a34;
  display: grid;
  place-items: center;
  box-shadow: 0 8px 20px rgba(21, 30, 26, 0.05);
}

.topbar-icon-button.accent {
  background: #f3f7f1;
  color: var(--brand-deep);
}

.topbar-icon-button :deep(.el-icon),
.mobile-nav-icon :deep(.el-icon) {
  font-size: 18px;
}

.mobile-shell {
  min-height: 0;
}

.mobile-nav {
  position: fixed;
  left: 10px;
  right: 10px;
  bottom: calc(10px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 8px;
  border-radius: 16px;
  background: rgba(24, 36, 31, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 18px 34px rgba(17, 24, 21, 0.2);
  backdrop-filter: blur(18px);
  z-index: 20;
}

.mobile-nav-item {
  min-height: 54px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: rgba(247, 243, 236, 0.66);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: color 180ms ease, background 180ms ease, transform 180ms ease;
}

.mobile-nav-item.active {
  background: #f6efe5;
  color: #1f2925;
}

.mobile-nav-icon {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
}

.mobile-nav-item span:last-child {
  font-size: 11px;
  font-weight: 700;
}
</style>
