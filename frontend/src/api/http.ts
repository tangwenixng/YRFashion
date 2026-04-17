import axios from 'axios'

import { apiBaseURL } from './base'
import { adminBasePath } from '../router/base'
import {
  readAdminExperienceOverride,
  resolveAdminLoginRoute,
  resolveExperienceForPath,
  sanitizeRedirectTarget,
} from '../router/deviceExperience'

export const TOKEN_STORAGE_KEY = 'yrfasion-admin-token'

export const http = axios.create({
  baseURL: apiBaseURL,
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const resolveRelativeAdminPath = (pathname: string) => {
  const normalizedBase = adminBasePath === '/' ? '' : adminBasePath.replace(/\/$/, '')
  if (!normalizedBase) {
    return pathname || '/'
  }

  if (pathname.startsWith(normalizedBase)) {
    const strippedPath = pathname.slice(normalizedBase.length)
    return strippedPath.startsWith('/') ? strippedPath : `/${strippedPath}`
  }

  return pathname || '/'
}

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)

      const relativePath = resolveRelativeAdminPath(window.location.pathname)
      const currentSearch = window.location.search || ''
      const currentPath = sanitizeRedirectTarget(`${relativePath}${currentSearch}`) || relativePath
      const currentExperience = resolveExperienceForPath({
        path: relativePath,
        userAgent: window.navigator.userAgent,
        override: readAdminExperienceOverride(),
      })
      const loginPath = resolveAdminLoginRoute(currentExperience)

      if (relativePath !== loginPath) {
        const redirect = sanitizeRedirectTarget(currentPath)
        const search = redirect ? `?redirect=${encodeURIComponent(redirect)}` : ''
        window.location.href = `${adminBasePath.replace(/\/$/, '')}${loginPath}${search}`
      }
    }

    return Promise.reject(error)
  },
)
