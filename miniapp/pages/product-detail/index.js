const { getAccessToken } = require("../../utils/auth")
const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

const MESSAGE_POLL_INTERVAL = 15000

const STATUS_META_MAP = {
  unread: {
    label: "待店主查看",
    tone: "pending",
  },
  read: {
    label: "店主已查看",
    tone: "read",
  },
  replied: {
    label: "店主已回复",
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

function normalizeMessage(message) {
  const statusMeta = STATUS_META_MAP[message.status] || {
    label: "已提交",
    tone: "pending",
  }

  return Object.assign({}, message, {
    status_label: statusMeta.label,
    status_tone: statusMeta.tone,
    created_at_text: formatDateTime(message.created_at),
    reply_at_text: formatDateTime(message.reply_at),
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
    this.setData({
      productId: Number(query.id || 0),
    })
    this.loadProduct(this.data.productId)
  },

  onShow() {
    if (!this.data.productId) {
      return
    }
    this.loadMessageHistory({ silent: true, background: true })
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

  async loadProduct(productId = this.data.productId) {
    this.setData({ loading: true, error: "" })
    try {
      const product = normalizeProduct(await request({ url: `/miniapp/products/${productId}` }))
      this.setData({ product, loading: false, error: "" })
      wx.setNavigationBarTitle({ title: product.name })
      this.loadMessageHistory({ silent: true, background: true })
    } catch (error) {
      this.setData({ loading: false, error: "穿搭详情加载失败，请稍后重试。" })
      wx.showToast({ title: "加载失败", icon: "none" })
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
        messagesLastUpdatedText: formatDateTime(new Date()),
        hasUnreadReplies: hasNewReply || nextMessages.some((item) => item.status === "replied"),
      })

      if (hasNewReply) {
        wx.showToast({ title: "店主已回复你的留言", icon: "none" })
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
