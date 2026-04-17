// 这些是后台路由的一级路径段，用来判断当前 URL 中哪一段开始进入后台真实路由。
// 如果前面还带了额外前缀，例如 /yr-admin-gate-9x2k/login，就可以据此反推出隐藏入口前缀。
const topLevelRouteSegments = new Set([
  'login',
  'home',
  'dashboard',
  'accounts',
  'categories',
  'products',
  'messages',
  'users',
  'settings',
])

const mobileRouteNamespace = 'm'

// 统一将后台入口前缀整理为 /xxx/ 这种格式，便于同时给 vue-router history 和登录跳转复用。
const normalizeBasePath = (value: string) => {
  const trimmed = value.trim()
  if (!trimmed || trimmed === '/') {
    return '/'
  }

  return `/${trimmed.replace(/^\/+|\/+$/g, '')}/`
}

// 根据当前浏览器地址推断后台挂载前缀。
// 例如 /yr-admin-gate-9x2k/login 会得到 /yr-admin-gate-9x2k/；
// 如果地址本身就是 /login 或 /dashboard，则说明后台仍挂在根路径。
export const resolveAdminBasePath = (pathname: string) => {
  const cleanPathname = pathname.split('?')[0] || '/'
  const segments = cleanPathname.split('/').filter(Boolean)

  if (!segments.length) {
    return '/'
  }

  const routeSegmentIndex = segments.findIndex((segment, index) => {
    if (topLevelRouteSegments.has(segment)) {
      return true
    }

    if (segment !== mobileRouteNamespace) {
      return false
    }

    const nextSegment = segments[index + 1]
    return !nextSegment || topLevelRouteSegments.has(nextSegment)
  })
  if (routeSegmentIndex === 0) {
    return '/'
  }

  if (routeSegmentIndex > 0) {
    return normalizeBasePath(segments.slice(0, routeSegmentIndex).join('/'))
  }

  return normalizeBasePath(segments.join('/'))
}

// 浏览器环境下按当前地址动态推断；非浏览器环境降级为根路径，避免直接访问 window 报错。
export const adminBasePath =
  typeof window === 'undefined'
    ? '/'
    : resolveAdminBasePath(window.location.pathname)

// 登录页路径始终基于当前后台前缀拼接，避免 401 回跳时丢失隐藏入口。
export const adminLoginPath = `${adminBasePath}login`
