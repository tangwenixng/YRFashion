import type { RouteRecordRaw } from 'vue-router'

import PlaceholderPage from '../views/PlaceholderPage.vue'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: PlaceholderPage,
    meta: {
      title: '登录',
      section: '后台登录',
    },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: PlaceholderPage,
    meta: {
      title: '概览',
      section: '仪表盘',
    },
  },
  {
    path: '/products',
    name: 'products',
    component: PlaceholderPage,
    meta: {
      title: '商品管理',
      section: '商品管理',
    },
  },
  {
    path: '/messages',
    name: 'messages',
    component: PlaceholderPage,
    meta: {
      title: '留言管理',
      section: '留言管理',
    },
  },
  {
    path: '/users',
    name: 'users',
    component: PlaceholderPage,
    meta: {
      title: '用户列表',
      section: '用户列表',
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: PlaceholderPage,
    meta: {
      title: '店铺设置',
      section: '店铺设置',
    },
  },
]
