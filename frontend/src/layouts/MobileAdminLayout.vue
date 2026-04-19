<script setup lang="ts">
import { ChatLineRound, House, Promotion, Setting } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { label: '首页', icon: House, path: '/m/home' },
  { label: '商品', icon: Promotion, path: '/m/products' },
  { label: '留言', icon: ChatLineRound, path: '/m/messages' },
  { label: '店铺管理', icon: Setting, path: '/m/settings' },
]

const activeTab = computed(() => {
  if (route.path.startsWith('/m/products')) {
    return '/m/products'
  }
  if (route.path.startsWith('/m/messages')) {
    return '/m/messages'
  }
  if (route.path.startsWith('/m/settings')) {
    return '/m/settings'
  }
  if (route.path === '/m/home' || route.path === '/m') {
    return '/m/home'
  }
  return ''
})

const activeTabLabel = computed(() => {
  const routeTitle = typeof route.meta.title === 'string' ? route.meta.title : ''
  return routeTitle || tabs.find((tab) => tab.path === activeTab.value)?.label || '首页'
})
</script>

<template>
  <div class="mobile-admin-layout">
    <header class="mobile-titlebar" aria-label="当前页面栏目">
      <span class="mobile-titlebar-text">{{ activeTabLabel }}</span>
    </header>

    <main id="mobile-main-content" class="mobile-shell">
      <router-view />
    </main>

    <nav class="mobile-nav" aria-label="手机后台底部导航">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="mobile-nav-item"
        :class="{ active: activeTab === tab.path }"
        type="button"
        :aria-label="tab.label"
        @click="router.push(tab.path)"
      >
        <span class="mobile-nav-icon">
          <el-icon><component :is="tab.icon" /></el-icon>
        </span>
        <span class="sr-only">{{ tab.label }}</span>
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
  padding: max(10px, env(safe-area-inset-top)) 10px calc(90px + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, #f3f4ef 0%, #eaeee7 42%, #e5eae2 100%);
  overscroll-behavior-y: contain;
}

.mobile-titlebar {
  position: sticky;
  top: max(6px, env(safe-area-inset-top));
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 24px;
  padding: 2px 2px 0;
}

.mobile-titlebar-text {
  color: #222823;
  font-size: 20px;
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.mobile-shell {
  min-height: 0;
}

.mobile-nav {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(14px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  padding: 7px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(244, 246, 241, 0.64));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    0 10px 26px rgba(24, 36, 31, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(24px) saturate(1.35);
  -webkit-backdrop-filter: blur(24px) saturate(1.35);
  z-index: 20;
}

.mobile-nav-item {
  min-height: 50px;
  border: 0;
  border-radius: 16px;
  background: transparent;
  color: rgba(66, 78, 72, 0.68);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 180ms ease, background 180ms ease, transform 180ms ease, box-shadow 180ms ease;
}

.mobile-nav-item.active {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 240, 228, 0.92));
  color: #1f2925;
  box-shadow:
    0 6px 16px rgba(90, 78, 52, 0.14),
    inset 0 0 0 1px rgba(255, 255, 255, 0.72);
}

.mobile-nav-icon {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
}

.mobile-nav-icon :deep(.el-icon) {
  font-size: 18px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
