<script setup lang="ts">
import { ChatLineRound, House, Promotion } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'


const route = useRoute()
const router = useRouter()

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

</script>

<template>
  <div class="mobile-admin-layout">

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
  gap: 10px;
  padding: max(10px, env(safe-area-inset-top)) 10px calc(90px + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, #f3f4ef 0%, #eaeee7 42%, #e5eae2 100%);
  overscroll-behavior-y: contain;
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
