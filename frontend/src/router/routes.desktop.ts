import type { RouteRecordRaw } from 'vue-router'

export const desktopRoutes: RouteRecordRaw[] = [
  {
    path: 'dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: {
      title: '概览',
      experience: 'desktop',
    },
  },
  {
    path: 'accounts',
    name: 'accounts',
    component: () => import('../views/AccountsView.vue'),
    meta: {
      title: '账号管理',
      experience: 'desktop',
    },
  },
  {
    path: 'categories',
    name: 'categories',
    component: () => import('../views/CategoriesView.vue'),
    meta: {
      title: '分类管理',
      experience: 'desktop',
    },
  },
  {
    path: 'products',
    name: 'products',
    component: () => import('../views/ProductsView.vue'),
    meta: {
      title: '商品管理',
      experience: 'desktop',
    },
  },
  {
    path: 'products/create',
    name: 'product-create',
    component: () => import('../views/ProductEditorView.vue'),
    meta: {
      title: '新增商品',
      experience: 'desktop',
    },
  },
  {
    path: 'products/:id/edit',
    name: 'product-edit',
    component: () => import('../views/ProductEditorView.vue'),
    meta: {
      title: '编辑商品',
      experience: 'desktop',
    },
  },
  {
    path: 'messages',
    name: 'messages',
    component: () => import('../views/MessagesView.vue'),
    meta: {
      title: '留言管理',
      experience: 'desktop',
    },
  },
  {
    path: 'users',
    name: 'users',
    component: () => import('../views/UsersView.vue'),
    meta: {
      title: '用户列表',
      experience: 'desktop',
    },
  },
  {
    path: 'settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: {
      title: '店铺设置',
      experience: 'desktop',
    },
  },
]
