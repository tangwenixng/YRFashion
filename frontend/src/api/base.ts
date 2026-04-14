import { adminBasePath } from '../router/base'

const trimTrailingSlash = (value: string) => value.replace(/\/$/, '')

const normalizeAbsoluteLikeBaseURL = (value: string) => {
  const trimmed = value.trim()
  if (!trimmed) {
    return ''
  }

  if (/^https?:\/\//.test(trimmed)) {
    return trimTrailingSlash(trimmed)
  }

  if (trimmed === '/') {
    return ''
  }

  if (trimmed.startsWith('/')) {
    return trimTrailingSlash(trimmed)
  }

  return `/${trimmed.replace(/^\/+|\/+$/g, '')}`
}

const resolveAdminScopedPath = (suffix: string) => {
  if (adminBasePath === '/') {
    return suffix
  }

  return `${trimTrailingSlash(adminBasePath)}${suffix}`
}

const configuredApiBaseURL = (import.meta.env.VITE_API_BASE_URL || '').trim()
const defaultApiBaseURL = resolveAdminScopedPath('/api')

export const apiBaseURL = normalizeAbsoluteLikeBaseURL(configuredApiBaseURL || defaultApiBaseURL)
export const mediaBaseURL = apiBaseURL.replace(/\/api$/, '')

export const resolveMediaUrl = (value: string | null) => {
  if (!value) {
    return null
  }

  if (/^https?:\/\//.test(value)) {
    return value
  }

  if (!mediaBaseURL) {
    return value.startsWith('/') ? value : `/${value.replace(/^\/+/, '')}`
  }

  if (value.startsWith('/')) {
    if (value === mediaBaseURL || value.startsWith(`${mediaBaseURL}/`)) {
      return value
    }
    return `${mediaBaseURL}${value}`
  }

  return `${mediaBaseURL}/${value.replace(/^\/+/, '')}`
}
