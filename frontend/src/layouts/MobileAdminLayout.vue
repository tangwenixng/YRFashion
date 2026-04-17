<script setup lang="ts">
import { ArrowLeft, ChatLineRound, House, Promotion, SwitchButton } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AdminExperienceSwitch from '../components/AdminExperienceSwitch.vue'
import { resolvePathForExperience, writeAdminExperienceOverride } from '../router/deviceExperience'
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
const currentSubtitle = computed(() => {
  if (route.path.startsWith('/m/products')) {
    return '单列卡片 + 就近操作，更适合手机浏览器处理商品。'
  }
  if (route.path.startsWith('/m/messages')) {
    return '优先未读留言与快捷回复，减少来回跳转。'
  }
  return '把高频运营动作压缩到手机里也依然顺手。'
})
const canGoBack = computed(() => route.path !== '/m/home')

const goBack = () => {
  if (canGoBack.value) {
    router.back()
  }
}

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
    <header class="shell-hero">
      <div class="hero-top-row">
        <button v-if="canGoBack" class="hero-icon-button subtle" type="button" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <span v-else class="mobile-overline">YRFashion Mobile</span>

        <button class="hero-icon-button" type="button" @click="logout">
          <el-icon><SwitchButton /></el-icon>
        </button>
      </div>

      <div class="hero-copy">
        <p class="hero-kicker">{{ authStore.profile?.display_name ?? 'Store Admin' }}</p>
        <h1>{{ currentTitle }}</h1>
        <p>{{ currentSubtitle }}</p>
      </div>

      <div class="hero-meta-row">
        <div class="hero-profile-chip">
          <strong>{{ authStore.profile?.username ?? 'admin' }}</strong>
          <span>手机后台已启用</span>
        </div>
        <button class="desktop-switch-button" type="button" @click="switchToDesktop">切到桌面版</button>
      </div>

      <AdminExperienceSwitch light />
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
  gap: 16px;
  padding: 14px 14px calc(108px + env(safe-area-inset-bottom));
  background:
    radial-gradient(circle at top left, rgba(192, 138, 54, 0.18), transparent 24%),
    linear-gradient(180deg, #f6f4ee, #ecefe8 34%, #e7ece4 100%);
  overscroll-behavior-y: contain;
}

.shell-hero {
  padding: 18px 18px 16px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.08), transparent 28%),
    linear-gradient(155deg, var(--mobile-shell-dark), var(--mobile-shell-deep));
  box-shadow: 0 26px 48px rgba(19, 31, 27, 0.24);
  color: #f7f3ec;
}

.hero-top-row,
.hero-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.hero-copy {
  margin: 16px 0 18px;
}

.hero-kicker {
  margin: 0 0 8px;
  color: rgba(247, 243, 236, 0.72);
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 0;
  font-family: 'Playfair Display', serif;
  font-size: clamp(28px, 9vw, 38px);
  line-height: 0.98;
  letter-spacing: -0.04em;
}

.hero-copy p {
  margin: 12px 0 0;
  color: rgba(247, 243, 236, 0.8);
  line-height: 1.7;
}

.hero-profile-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-profile-chip strong {
  font-size: 15px;
}

.hero-profile-chip span {
  color: rgba(247, 243, 236, 0.68);
  font-size: 12px;
}

.hero-icon-button,
.desktop-switch-button,
.mobile-nav-item {
  font: inherit;
}

.hero-icon-button {
  width: 46px;
  height: 46px;
  border: 0;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff7ef;
  display: grid;
  place-items: center;
}

.hero-icon-button.subtle {
  background: rgba(255, 255, 255, 0.05);
}

.hero-icon-button :deep(.el-icon) {
  font-size: 18px;
}

.desktop-switch-button {
  min-height: 44px;
  padding: 0 16px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(241, 231, 215, 0.98));
  color: #1f2925;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(18, 25, 22, 0.18);
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
  padding: 10px;
  border-radius: 28px;
  background: rgba(24, 36, 31, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 22px 40px rgba(17, 24, 21, 0.24);
  backdrop-filter: blur(20px);
  z-index: 20;
}

.mobile-nav-item {
  min-height: 58px;
  border: 0;
  border-radius: 20px;
  background: transparent;
  color: rgba(247, 243, 236, 0.62);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition:
    color 180ms ease,
    background 180ms ease,
    transform 180ms ease,
    box-shadow 180ms ease;
}

.mobile-nav-item:hover,
.mobile-nav-item:focus-visible {
  transform: translateY(-1px);
}

.mobile-nav-item.active {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(244, 236, 224, 0.98));
  color: #1f2925;
  box-shadow: 0 12px 24px rgba(18, 25, 22, 0.16);
}

.mobile-nav-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
}

.mobile-nav-item :deep(.el-icon) {
  font-size: 18px;
}

.mobile-nav-item span:last-child {
  font-size: 12px;
  font-weight: 700;
}
</style>
