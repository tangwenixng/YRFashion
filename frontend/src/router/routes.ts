import type { RouteRecordRaw } from 'vue-router'

import { desktopRoutes } from './routes.desktop'
import { mobileRoutes } from './routes.mobile'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: {
      title: '登录',
      guestOnly: true,
      neutralEntry: true,
      experience: 'desktop',
    },
  },
  {
    path: '/m/login',
    name: 'mobile-login',
    component: () => import('../views/LoginView.vue'),
    meta: {
      title: '手机登录',
      guestOnly: true,
      experience: 'mobile',
    },
  },
  {
    path: '/',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: {
      requiresAuth: true,
      experience: 'desktop',
    },
    children: desktopRoutes,
  },
  {
    path: '/m',
    component: () => import('../layouts/MobileAdminLayout.vue'),
    meta: {
      requiresAuth: true,
      experience: 'mobile',
    },
    children: mobileRoutes,
  },
]
