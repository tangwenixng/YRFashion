import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { adminBasePath } from './base'
import {
  readAdminExperienceOverride,
  resolveAdminHomeRoute,
  resolveAdminLoginRoute,
  resolveExperienceForPath,
  sanitizeRedirectTarget,
} from './deviceExperience'
import { routes } from './routes'

export const router = createRouter({
  history: createWebHistory(adminBasePath),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    await authStore.initialize()
  }

  const userAgent = typeof navigator === 'undefined' ? '' : navigator.userAgent
  const override = readAdminExperienceOverride()
  const currentExperience = resolveExperienceForPath({
    path: to.path,
    userAgent,
    override,
  })

  if (to.path === '/login' && !authStore.isAuthenticated && currentExperience === 'mobile') {
    return {
      path: '/m/login',
      query: to.query,
      hash: to.hash,
      replace: true,
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    const loginTarget = resolveAdminLoginRoute(currentExperience)
    const redirectTarget = sanitizeRedirectTarget(to.fullPath)
    return {
      path: loginTarget,
      query: redirectTarget ? { redirect: redirectTarget } : undefined,
      replace: true,
    }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    const redirectTarget = sanitizeRedirectTarget(
      typeof to.query.redirect === 'string' ? to.query.redirect : undefined,
    )
    return redirectTarget || resolveAdminHomeRoute(currentExperience)
  }

  return true
})

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : '管理后台'
  document.title = `${title} | YRFasion Admin`
})
