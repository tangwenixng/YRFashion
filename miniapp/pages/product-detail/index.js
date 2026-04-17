const { getAccessToken } = require("../../utils/auth")
const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

const MESSAGE_POLL_INTERVAL = 15000
const DEFAULT_HERO_HEIGHT = 960
const MIN_HERO_HEIGHT = 720
const MAX_HERO_HEIGHT = 1280
const HERO_HORIZONTAL_PADDING = 32 * 2
const HERO_CONTENT_WIDTH_RPX = 750 - HERO_HORIZONTAL_PADDING
const imageHeightCache = {}

function buildNavigationState(navTitle = "") {
  const systemInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
  const statusBarHeight = Number(systemInfo.statusBarHeight || 20)
  const windowWidth = Number(systemInfo.windowWidth || 375)
  let navBarHeight = 44
  let navRightSpaceWidth = 96

  if (wx.getMenuButtonBoundingClientRect) {
    const menuButtonRect = wx.getMenuButtonBoundingClientRect()
    if (menuButtonRect && menuButtonRect.width) {
      navBarHeight = menuButtonRect.height + (menuButtonRect.top - statusBarHeight) * 2
      navRightSpaceWidth = menuButtonRect.width + (windowWidth - menuButtonRect.right) * 2
    }
  }

  return {
    navTitle,
    statusBarHeight,
    navBarHeight,
    navBarTotalHeight: statusBarHeight + navBarHeight,
    navRightSpaceWidth,
  }
}

const STATUS_META_MAP = {
  unread: {
    label: "待查看",
    tone: "pending",
  },
  read: {
    label: "已查看",
    tone: "read",
  },
  replied: {
    label: "已回复",
    tone: "replied",
  },
}

function formatDateTime(value) {
  if (!value) {
    return ""
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, "0")
  const day = `${date.getDate()}`.padStart(2, "0")
  const hour = `${date.getHours()}`.padStart(2, "0")
  const minute = `${date.getMinutes()}`.padStart(2, "0")
  return `${year}-${month}-${day} ${hour}:${minute}`
}

function formatTime(value) {
  if (!value) {
    return ""
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ""
  }

  const hour = `${date.getHours()}`.padStart(2, "0")
  const minute = `${date.getMinutes()}`.padStart(2, "0")
  return `${hour}:${minute}`
}

function normalizeMessage(message) {
  const statusMeta = STATUS_META_MAP[message.status] || {
    label: "已提交",
    tone: "pending",
  }

  return Object.assign({}, message, {
    status_label: statusMeta.label,
    status_tone: statusMeta.tone,
    created_at_text: formatDateTime(message.created_at),
    created_at_short_text: formatTime(message.created_at),
    reply_at_text: formatDateTime(message.reply_at),
    reply_at_short_text: formatTime(message.reply_at),
    has_reply: Boolean(message.reply_content),
  })
}

function buildMessageMap(messages) {
  return messages.reduce((result, item) => {
    result[item.id] = item
    return result
  }, {})
}

Page({
  data: {
    productId: null,
    product: null,
    heroCurrent: 0,
    heroHeight: DEFAULT_HERO_HEIGHT,
    heroHeights: [],
    messages: [],
    messagesLoading: false,
    messagesError: "",
    messagesLastUpdatedText: "",
    hasMiniappSession: false,
    hasUnreadReplies: false,
    loading: true,
    error: "",
  },

  onLoad(query) {
    this.messagePollTimer = null
    this.messagesRequesting = false
    this.hasShownOnce = false
    this.setData({
      productId: Number(query.id || 0),
      ...buildNavigationState("穿搭详情"),
    })
    this.loadProduct(this.data.productId)
  },

  onShow() {
    if (!this.data.productId) {
      return
    }

    if (!this.hasShownOnce) {
      this.hasShownOnce = true
      this.loadMessageHistory({ silent: true, background: true })
    } else {
      this.loadProduct(this.data.productId, { background: true, silent: true })
    }

    this.startMessagePolling()
  },

  onHide() {
    this.stopMessagePolling()
  },

  onUnload() {
    this.stopMessagePolling()
  },

  startMessagePolling() {
    this.stopMessagePolling()
    if (!this.data.productId || !getAccessToken()) {
      return
    }

    this.messagePollTimer = setInterval(() => {
      this.loadMessageHistory({ silent: true, background: true })
    }, MESSAGE_POLL_INTERVAL)
  },

  stopMessagePolling() {
    if (this.messagePollTimer) {
      clearInterval(this.messagePollTimer)
      this.messagePollTimer = null
    }
  },

  reloadProduct() {
    this.loadProduct(this.data.productId)
  },

  async loadProduct(productId = this.data.productId, options = {}) {
    const background = Boolean(options.background && this.data.product)
    const silent = Boolean(options.silent)

    if (!background) {
      this.setData({ loading: true, error: "" })
    }

    try {
      const product = normalizeProduct(await request({ url: `/miniapp/products/${productId}` }))
      const heroHeights = await this.buildHeroHeights(product.images || [])
      this.setData({
        product,
        navTitle: product.name || "穿搭详情",
        heroCurrent: 0,
        heroHeight: heroHeights[0] || DEFAULT_HERO_HEIGHT,
        heroHeights,
        loading: false,
        error: "",
      })
      this.loadMessageHistory({ silent: true, background: true })
    } catch (error) {
      if (background && error && error.statusCode === 404) {
        this.stopMessagePolling()
        this.setData({
          product: null,
          messages: [],
          hasUnreadReplies: false,
          messagesLastUpdatedText: "",
          loading: false,
          error: "穿搭已下架或不存在。",
        })
        return
      }

      if (!background) {
        this.setData({ loading: false, error: "穿搭详情加载失败，请稍后重试。" })
      }
      if (!silent) {
        wx.showToast({ title: "加载失败", icon: "none" })
      }
    }
  },

  async loadMessageHistory(options = {}) {
    if (!this.data.productId || this.messagesRequesting) {
      return
    }

    const token = getAccessToken()
    if (!token) {
      this.stopMessagePolling()
      this.setData({
        hasMiniappSession: false,
        hasUnreadReplies: false,
        messages: [],
        messagesLoading: false,
        messagesError: "",
        messagesLastUpdatedText: "",
      })
      return
    }

    const shouldShowLoading = !options.background
    this.messagesRequesting = true
    this.setData({
      hasMiniappSession: true,
      messagesLoading: shouldShowLoading,
      messagesError: "",
    })

    try {
      const response = await request({
        url: `/miniapp/products/${this.data.productId}/messages`,
      })

      const nextMessages = response.items.map(normalizeMessage)
      const previousMessageMap = buildMessageMap(this.data.messages)
      const hasNewReply = nextMessages.some((item) => {
        const previous = previousMessageMap[item.id]
        return item.has_reply && (!previous || !previous.has_reply)
      })

      this.setData({
        messages: nextMessages,
        messagesLoading: false,
        messagesError: "",
        messagesLastUpdatedText: formatTime(new Date()),
        hasUnreadReplies: hasNewReply || nextMessages.some((item) => item.status === "replied"),
      })

      if (hasNewReply) {
        wx.showToast({ title: "有新回复了", icon: "none" })
      }

      this.startMessagePolling()
    } catch (error) {
      this.setData({
        messagesLoading: false,
        messagesError: "留言记录加载失败，请稍后重试。",
      })
      if (!options.silent) {
        wx.showToast({ title: "留言记录加载失败", icon: "none" })
      }
    } finally {
      this.messagesRequesting = false
    }
  },

  handleConsult() {
    const product = this.data.product
    if (!product) {
      return
    }

    const productName = encodeURIComponent(product.name)
    wx.navigateTo({
      url: `/pages/message/index?productId=${product.id}&productName=${productName}`,
    })
  },

  goToContact() {
    wx.navigateTo({ url: "/pages/contact/index" })
  },

  goBack() {
    if (getCurrentPages().length > 1) {
      wx.navigateBack({ delta: 1 })
      return
    }
    this.goHome()
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" })
  },

  goToMessageHistory() {
    const product = this.data.product
    if (!product) {
      return
    }

    const productName = encodeURIComponent(product.name)
    wx.navigateTo({
      url: `/pages/message-history/index?productId=${product.id}&productName=${productName}`,
    })
  },

  previewImage(event) {
    const product = this.data.product
    const current = event.currentTarget.dataset.imageUrl
    const urls = product && Array.isArray(product.images)
      ? product.images.map((item) => item.image_url).filter(Boolean)
      : []

    if (!current || !urls.length) {
      return
    }

    wx.previewImage({
      current,
      urls,
    })
  },

  handleHeroChange(event) {
    const heroCurrent = Number(event.detail.current || 0)
    this.setData({
      heroCurrent,
      heroHeight: this.data.heroHeights[heroCurrent] || DEFAULT_HERO_HEIGHT,
    })
  },

  async buildHeroHeights(images = []) {
    if (!images.length) {
      return [DEFAULT_HERO_HEIGHT]
    }

    return Promise.all(
      images.map((item) => this.getImageDisplayHeight(item.image_url)),
    )
  },

  getImageDisplayHeight(url) {
    if (!url) {
      return Promise.resolve(DEFAULT_HERO_HEIGHT)
    }

    if (imageHeightCache[url]) {
      return Promise.resolve(imageHeightCache[url])
    }

    return new Promise((resolve) => {
      wx.getImageInfo({
        src: url,
        success: (result) => {
          const height = this.normalizeHeroHeight(result)
          imageHeightCache[url] = height
          resolve(height)
        },
        fail: () => {
          imageHeightCache[url] = DEFAULT_HERO_HEIGHT
          resolve(DEFAULT_HERO_HEIGHT)
        },
      })
    })
  },

  normalizeHeroHeight(imageInfo = {}) {
    const width = Number(imageInfo.width || 0)
    const height = Number(imageInfo.height || 0)
    if (!width || !height) {
      return DEFAULT_HERO_HEIGHT
    }

    const heightRpx = (height / width) * HERO_CONTENT_WIDTH_RPX
    return Math.round(Math.min(Math.max(heightRpx, MIN_HERO_HEIGHT), MAX_HERO_HEIGHT))
  },

  goToRelatedDetail(event) {
    const productId = Number(event.currentTarget.dataset.productId || 0)
    if (!productId) {
      return
    }

    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },

  onShareAppMessage() {
    const product = this.data.product
    if (!product) {
      return {
        title: "伊人Fashion 穿搭馆",
        path: "/pages/home/index",
      }
    }

    return {
      title: product.name,
      path: `/pages/product-detail/index?id=${product.id}`,
      imageUrl: product.cover_image_url || undefined,
    }
  },
})
