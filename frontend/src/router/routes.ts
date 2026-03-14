import type { RouteRecordRaw } from 'vue-router'

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
    },
  },
  {
    path: '/',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: {
          title: '概览',
        },
      },
      {
        path: 'categories',
        name: 'categories',
        component: () => import('../views/CategoriesView.vue'),
        meta: {
          title: '分类管理',
        },
      },
      {
        path: 'products',
        name: 'products',
        component: () => import('../views/ProductsView.vue'),
        meta: {
          title: '商品管理',
        },
      },
      {
        path: 'messages',
        name: 'messages',
        component: () => import('../views/MessagesView.vue'),
        meta: {
          title: '留言管理',
        },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('../views/UsersView.vue'),
        meta: {
          title: '用户列表',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/SettingsView.vue'),
        meta: {
          title: '店铺设置',
        },
      },
    ],
  },
]
