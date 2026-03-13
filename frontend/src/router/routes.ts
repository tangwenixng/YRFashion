import type { RouteRecordRaw } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import PlaceholderPage from '../views/PlaceholderPage.vue'
import ProductsView from '../views/ProductsView.vue'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      title: '登录',
      guestOnly: true,
    },
  },
  {
    path: '/',
    component: AdminLayout,
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardView,
        meta: {
          title: '概览',
        },
      },
      {
        path: 'products',
        name: 'products',
        component: ProductsView,
        meta: {
          title: '商品管理',
        },
      },
      {
        path: 'messages',
        name: 'messages',
        component: PlaceholderPage,
        meta: {
          title: '留言管理',
          section: '留言管理',
        },
      },
      {
        path: 'users',
        name: 'users',
        component: PlaceholderPage,
        meta: {
          title: '用户列表',
          section: '用户列表',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: PlaceholderPage,
        meta: {
          title: '店铺设置',
          section: '店铺设置',
        },
      },
    ],
  },
]
