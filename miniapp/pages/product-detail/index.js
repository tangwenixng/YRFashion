const { getAccessToken } = require("../../utils/auth")
const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

const STATUS_LABEL_MAP = {
  unread: "待店主查看",
  read: "店主已查看",
  replied: "店主已回复",
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
  return Object.assign({}, message, {
    status_label: STATUS_LABEL_MAP[message.status] || "已提交",
    created_at_text: formatDateTime(message.created_at),
    reply_at_text: formatDateTime(message.reply_at),
  })
}

Page({
  data: {
    productId: null,
    product: null,
    messages: [],
    messagesLoading: false,
    messagesError: "",
    hasMiniappSession: false,
    loading: true,
    error: "",
  },

  onLoad(query) {
    const productId = Number(query.id || 0)
    this.setData({ productId })
    this.loadProduct(productId)
  },

  onShow() {
    if (this.data.productId) {
      this.loadMessageHistory({ silent: true })
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
      this.loadMessageHistory({ silent: true })
    } catch (error) {
      this.setData({ loading: false, error: "商品详情加载失败，请稍后重试。" })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  async loadMessageHistory(options = {}) {
    if (!this.data.productId) {
      return
    }

    const token = getAccessToken()
    if (!token) {
      this.setData({
        hasMiniappSession: false,
        messages: [],
        messagesLoading: false,
        messagesError: "",
      })
      return
    }

    this.setData({
      hasMiniappSession: true,
      messagesLoading: true,
      messagesError: "",
    })

    try {
      const response = await request({
        url: `/miniapp/products/${this.data.productId}/messages`,
      })
      this.setData({
        messages: response.items.map(normalizeMessage),
        messagesLoading: false,
        messagesError: "",
      })
    } catch (error) {
      this.setData({
        messagesLoading: false,
        messagesError: "留言记录加载失败，请稍后重试。",
      })
      if (!options.silent) {
        wx.showToast({ title: "留言记录加载失败", icon: "none" })
      }
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
        title: "YRFasion",
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
