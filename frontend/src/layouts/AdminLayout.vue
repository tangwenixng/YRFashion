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
const isMobile = ref(false)

const MOBILE_BREAKPOINT = 900

const navigationGroups = [
  {
    title: '经营总览',
    items: [
      { index: '/dashboard', label: '概览', icon: House, badge: '看板' },
    ],
  },
  {
    title: '商品运营',
    items: [
      { index: '/products', label: '商品管理', icon: Promotion, badge: '核心' },
      { index: '/categories', label: '分类管理', icon: CollectionTag, badge: '结构' },
      { index: '/messages', label: '留言管理', icon: ChatLineRound, badge: '转化' },
    ],
  },
  {
    title: '系统支持',
    items: [
      { index: '/accounts', label: '账号管理', icon: UserFilled, badge: '权限' },
      { index: '/users', label: '用户列表', icon: User, badge: '访客' },
      { index: '/settings', label: '店铺设置', icon: Setting, badge: '配置' },
    ],
  },
] as const

const pageMetaMap: Record<string, { eyebrow: string; summary: string; highlights: string[] }> = {
  '/dashboard': {
    eyebrow: '经营概览',
    summary: '把商品规模、咨询趋势和用户活跃放在一个稳定的总览入口中。',
    highlights: ['总览优先', '数据聚合'],
  },
  '/accounts': {
    eyebrow: '后台权限',
    summary: '集中维护运营账号、状态和密码安全，避免后台权限散落。',
    highlights: ['权限收口', '账号安全'],
  },
  '/categories': {
    eyebrow: '商品结构',
    summary: '先把分类层级整理清楚，再处理商品上新和前台展示顺序。',
    highlights: ['分类清晰', '结构先行'],
  },
  '/products': {
    eyebrow: '商品编排',
    summary: '围绕上新、状态切换、拖拽排序和图文维护建立高频操作主路径。',
    highlights: ['上新主线', '筛选优先'],
  },
  '/messages': {
    eyebrow: '咨询处理',
    summary: '让留言筛选、回复和商品关联保持在同一条运营链路里。',
    highlights: ['咨询转化', '回复闭环'],
  },
  '/users': {
    eyebrow: '用户观察',
    summary: '快速查看小程序访客和咨询用户，为选品和内容调整提供线索。',
    highlights: ['用户画像', '行为线索'],
  },
  '/settings': {
    eyebrow: '店铺参数',
    summary: '统一管理店铺展示、提醒和基础配置，保证后台运行稳定。',
    highlights: ['配置统一', '交付稳定'],
  },
}

const activeMenu = computed(() => {
  if (route.path.startsWith('/products/')) {
    return '/products'
  }
  return route.path
})

const menuCollapsed = computed(() => collapsed.value && !isMobile.value)
const currentTitle = computed(() => (route.meta.title as string) || '管理后台')
const currentPageMeta = computed(() => pageMetaMap[activeMenu.value] ?? pageMetaMap['/dashboard'])

const syncViewportState = () => {
  isMobile.value = window.innerWidth <= MOBILE_BREAKPOINT
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
  <div class="admin-layout">
    <aside class="sidebar" :class="{ collapsed: menuCollapsed }">
      <div class="brand">
        <p class="brand-mark">YR</p>
        <div v-if="!menuCollapsed" class="brand-copy">
          <strong>YRFashion</strong>
          <span>商品运营后台</span>
        </div>
      </div>

      <div v-if="!menuCollapsed" class="sidebar-overview">
        <span class="sidebar-overview-label">商品型导航骨架</span>
        <strong>让商品、分类和咨询成为后台主路径</strong>
        <p>把高频运营动作放前面，减少在不同页面之间来回跳转的成本。</p>
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
              <em v-if="!menuCollapsed" class="menu-badge">{{ item.badge }}</em>
            </el-menu-item>
          </el-menu>
        </section>
      </div>

      <div v-if="!menuCollapsed" class="sidebar-footnote">
        <span class="sidebar-footnote-label">{{ currentPageMeta.eyebrow }}</span>
        <strong>{{ currentTitle }}</strong>
        <p>{{ currentPageMeta.summary }}</p>
        <div class="sidebar-footnote-tags">
          <span v-for="highlight in currentPageMeta.highlights" :key="highlight">{{ highlight }}</span>
        </div>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="topbar-main">
          <button class="collapse-button" type="button" @click="collapsed = !collapsed">
            <el-icon><component :is="menuCollapsed ? Expand : Fold" /></el-icon>
          </button>

          <div class="topbar-copy">
            <p class="topbar-label">{{ currentPageMeta.eyebrow }}</p>
            <strong>{{ currentTitle }}</strong>
            <p class="topbar-summary">{{ currentPageMeta.summary }}</p>
          </div>
        </div>

        <div class="topbar-side">
          <div class="topbar-highlights">
            <span v-for="highlight in currentPageMeta.highlights" :key="highlight" class="highlight-pill">
              {{ highlight }}
            </span>
          </div>

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
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px 18px 18px;
  border: 1px solid var(--line-soft);
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(192, 138, 54, 0.16), transparent 26%),
    linear-gradient(180deg, rgba(252, 251, 248, 0.96), rgba(241, 245, 239, 0.96));
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
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
.sidebar-overview-label,
.nav-section-title,
.topbar-label,
.sidebar-footnote-label,
.user-meta span {
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7a877f;
}

.sidebar-overview,
.sidebar-footnote {
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(57, 76, 64, 0.1);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.58), rgba(255, 255, 255, 0.3)),
    rgba(248, 250, 246, 0.76);
}

.sidebar-overview strong,
.sidebar-footnote strong {
  display: block;
  margin-top: 10px;
  color: var(--ink-strong);
  font-size: 18px;
  line-height: 1.4;
}

.sidebar-overview p,
.sidebar-footnote p {
  margin: 8px 0 0;
  color: var(--ink-soft);
  font-size: 14px;
  line-height: 1.7;
}

.sidebar-groups {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
  padding-right: 4px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-section-title {
  margin: 0;
  padding: 0 12px;
}

.sidebar-menu {
  border-right: 0;
  background: transparent;
}

:deep(.sidebar-menu .el-menu) {
  border-right: 0;
}

:deep(.sidebar-menu .el-menu-item) {
  height: 56px;
  margin-bottom: 6px;
  border-radius: 18px;
  color: #42544b;
  padding-right: 14px;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(47, 106, 88, 0.16), rgba(192, 138, 54, 0.12));
  color: var(--brand-deep);
}

:deep(.sidebar-menu .el-menu-item .el-icon) {
  font-size: 18px;
}

.menu-badge {
  margin-left: auto;
  padding: 4px 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  color: var(--brand-deep);
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
}

.sidebar-footnote-tags,
.topbar-highlights {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sidebar-footnote-tags {
  margin-top: 14px;
}

.sidebar-footnote-tags span,
.highlight-pill {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--brand-wash);
  color: var(--brand-deep);
  font-size: 13px;
  font-weight: 700;
}

.workspace {
  min-width: 0;
  min-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  border: 1px solid var(--line-soft);
  border-radius: 32px;
  background: rgba(248, 250, 246, 0.68);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(20px);
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 24px 28px 22px;
  border-bottom: 1px solid rgba(57, 76, 64, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0));
}

.topbar-main,
.topbar-side {
  display: flex;
  align-items: center;
  gap: 14px;
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
  margin-top: 6px;
  font-family: 'Sora', sans-serif;
  font-size: clamp(28px, 3vw, 34px);
  color: var(--ink-strong);
}

.topbar-summary {
  margin: 8px 0 0;
  color: var(--ink-soft);
  font-size: 14px;
  line-height: 1.7;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px 8px 10px;
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

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
    gap: 0;
    padding: 0;
  }

  .sidebar {
    position: static;
    width: auto;
    height: auto;
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    border-top: 0;
    box-shadow: none;
  }

  .topbar {
    padding: 20px 18px 18px;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .workspace {
    min-height: auto;
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .page-shell {
    padding: 18px;
  }

  .topbar-main,
  .topbar-side {
    width: 100%;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .topbar-copy strong {
    font-size: 26px;
  }
}
</style>
