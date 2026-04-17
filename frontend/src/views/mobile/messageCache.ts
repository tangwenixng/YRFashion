import type { MessageItem } from '../../api/modules/messages'

const MESSAGE_CACHE_KEY = 'yrfashion-mobile-message-cache'

const readCache = (): Record<string, MessageItem> => {
  if (typeof window === 'undefined') {
    return {}
  }

  try {
    const rawValue = window.sessionStorage.getItem(MESSAGE_CACHE_KEY)
    return rawValue ? (JSON.parse(rawValue) as Record<string, MessageItem>) : {}
  } catch {
    return {}
  }
}

const writeCache = (value: Record<string, MessageItem>) => {
  if (typeof window === 'undefined') {
    return
  }

  window.sessionStorage.setItem(MESSAGE_CACHE_KEY, JSON.stringify(value))
}

export const saveMobileMessageSnapshot = (message: MessageItem) => {
  const currentCache = readCache()
  currentCache[String(message.id)] = message
  writeCache(currentCache)
}

export const readMobileMessageSnapshot = (id: string) => readCache()[id] ?? null

export const removeMobileMessageSnapshot = (id: string) => {
  const currentCache = readCache()
  delete currentCache[id]
  writeCache(currentCache)
}
