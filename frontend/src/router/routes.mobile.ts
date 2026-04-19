import type { RouteRecordRaw } from 'vue-router'

export const mobileRoutes: RouteRecordRaw[] = [
  {
    path: '',
    redirect: '/m/home',
  },
  {
    path: 'home',
    name: 'mobile-home',
    component: () => import('../views/mobile/HomeView.vue'),
    meta: {
      title: '手机后台',
      experience: 'mobile',
    },
  },
  {
    path: 'categories',
    name: 'mobile-categories',
    component: () => import('../views/mobile/CategoriesView.vue'),
    meta: {
      title: '分类管理',
      experience: 'mobile',
    },
  },
  {
    path: 'products',
    name: 'mobile-products',
    component: () => import('../views/mobile/ProductsView.vue'),
    meta: {
      title: '商品管理',
      experience: 'mobile',
    },
  },
  {
    path: 'products/create',
    name: 'mobile-product-create',
    component: () => import('../views/mobile/ProductEditorView.vue'),
    meta: {
      title: '新增商品',
      experience: 'mobile',
    },
  },
  {
    path: 'products/:id/edit',
    name: 'mobile-product-edit',
    component: () => import('../views/mobile/ProductEditorView.vue'),
    meta: {
      title: '编辑商品',
      experience: 'mobile',
    },
  },
  {
    path: 'products/:id/images',
    name: 'mobile-product-images',
    component: () => import('../views/mobile/ProductImagesView.vue'),
    meta: {
      title: '图片管理',
      experience: 'mobile',
    },
  },
  {
    path: 'messages',
    name: 'mobile-messages',
    component: () => import('../views/mobile/MessagesView.vue'),
    meta: {
      title: '留言管理',
      experience: 'mobile',
    },
  },
  {
    path: 'messages/:id',
    name: 'mobile-message-detail',
    component: () => import('../views/mobile/MessageDetailView.vue'),
    meta: {
      title: '留言详情',
      experience: 'mobile',
    },
  },
  {
    path: 'settings',
    name: 'mobile-settings',
    component: () => import('../views/mobile/SettingsView.vue'),
    meta: {
      title: '店铺管理',
      experience: 'mobile',
    },
  },
]
