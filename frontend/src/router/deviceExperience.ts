export type AdminExperience = 'mobile' | 'desktop'
export type AdminExperienceOverride = 'auto' | 'force-mobile' | 'force-desktop'

export const ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY = 'yrfashion-admin-experience-override'
export const mobileAdminNamespace = '/m'

const mobileUserAgentPattern =
  /\b(iPhone|iPod|Android.+Mobile|Mobile Safari|Mobile\/|Windows Phone|webOS|BlackBerry)\b/i

const neutralEntryPaths = new Set(['/', '/login'])

export const isLikelyMobileUserAgent = (userAgent: string) => mobileUserAgentPattern.test(userAgent)

export const readAdminExperienceOverride = (): AdminExperienceOverride => {
  if (typeof window === 'undefined') {
    return 'auto'
  }

  const storedValue = window.localStorage.getItem(ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY)
  if (storedValue === 'force-mobile' || storedValue === 'force-desktop' || storedValue === 'auto') {
    return storedValue
  }
  return 'auto'
}

export const writeAdminExperienceOverride = (override: AdminExperienceOverride) => {
  if (typeof window === 'undefined') {
    return
  }

  if (override === 'auto') {
    window.localStorage.removeItem(ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY)
    return
  }

  window.localStorage.setItem(ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY, override)
}

export const clearAdminExperienceOverride = () => {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.removeItem(ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY)
}

export const isNeutralAdminEntry = (path: string) => neutralEntryPaths.has(path)

export const isMobileAdminPath = (path: string) =>
  path === mobileAdminNamespace || path.startsWith(`${mobileAdminNamespace}/`)

export const detectRouteExperience = (path: string): AdminExperience | null => {
  if (isNeutralAdminEntry(path)) {
    return null
  }

  return isMobileAdminPath(path) ? 'mobile' : 'desktop'
}

export const resolveAdminExperience = (input: {
  userAgent: string
  override: AdminExperienceOverride
}): AdminExperience => {
  if (input.override === 'force-mobile') {
    return 'mobile'
  }

  if (input.override === 'force-desktop') {
    return 'desktop'
  }

  return isLikelyMobileUserAgent(input.userAgent) ? 'mobile' : 'desktop'
}

export const resolveExperienceForPath = (input: {
  path: string
  userAgent: string
  override: AdminExperienceOverride
}): AdminExperience => detectRouteExperience(input.path) ?? resolveAdminExperience(input)

export const resolveAdminLoginRoute = (experience: AdminExperience) =>
  experience === 'mobile' ? '/m/login' : '/login'

export const resolveAdminHomeRoute = (experience: AdminExperience) =>
  experience === 'mobile' ? '/m/home' : '/dashboard'

export const sanitizeRedirectTarget = (value?: string | null) => {
  if (!value || !value.startsWith('/')) {
    return ''
  }

  if (value.startsWith('//')) {
    return ''
  }

  return value
}

const extractPathname = (value: string) => value.split('?')[0] || '/'
const extractSearch = (value: string) => {
  const questionMarkIndex = value.indexOf('?')
  return questionMarkIndex >= 0 ? value.slice(questionMarkIndex) : ''
}

export const resolvePathForExperience = (path: string, targetExperience: AdminExperience) => {
  const safePath = sanitizeRedirectTarget(path) || '/'
  const pathname = extractPathname(safePath)
  const search = extractSearch(safePath)

  if (targetExperience === 'mobile') {
    if (pathname === '/' || pathname === '/login') {
      return `/m/login${search}`
    }
    if (pathname === '/dashboard') {
      return `/m/home${search}`
    }
    if (pathname === '/products/create') {
      return `/m/products/create${search}`
    }

    const productEditMatch = pathname.match(/^\/products\/(\d+)\/edit$/)
    if (productEditMatch) {
      return `/m/products/${productEditMatch[1]}/edit${search}`
    }

    if (pathname === '/products') {
      return `/m/products${search}`
    }

    if (pathname === '/categories') {
      return `/m/categories${search}`
    }

    if (pathname === '/messages') {
      return `/m/messages${search}`
    }

    if (pathname === '/settings') {
      return `/m/settings${search}`
    }

    return isMobileAdminPath(pathname) ? safePath : `/m/home`
  }

  if (pathname === '/m' || pathname === '/m/login') {
    return `/login${search}`
  }
  if (pathname === '/m/home') {
    return `/dashboard${search}`
  }
  if (pathname === '/m/products' || pathname === '/m/products/create') {
    return pathname.replace('/m', '') + search
  }

  const mobileProductEditMatch = pathname.match(/^\/m\/products\/(\d+)\/(edit|images)$/)
  if (mobileProductEditMatch) {
    return `/products/${mobileProductEditMatch[1]}/edit${search}`
  }

  const mobileMessageDetailMatch = pathname.match(/^\/m\/messages\/\d+$/)
  if (mobileMessageDetailMatch) {
    return `/messages${search}`
  }

  if (pathname === '/m/messages') {
    return `/messages${search}`
  }

  if (pathname === '/m/categories') {
    return `/categories${search}`
  }

  if (pathname === '/m/settings') {
    return `/settings${search}`
  }

  return isMobileAdminPath(pathname) ? '/dashboard' : safePath
}
