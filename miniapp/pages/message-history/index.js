const { request } = require("../../utils/http")

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
  })
}

Page({
  data: {
    productId: 0,
    productName: "",
    page: 1,
    pageSize: 10,
    total: 0,
    items: [],
    loading: true,
    error: "",
  },

  onLoad(query) {
    const productId = Number(query.productId || 0)
    const productName = query.productName ? decodeURIComponent(query.productName) : ""
    this.setData({
      productId,
      productName,
    })
    this.loadMessages()
  },

  onPullDownRefresh() {
    this.loadMessages()
  },

  reloadMessages() {
    this.loadMessages()
  },

  async loadMessages() {
    const query = [`page=1`, `page_size=${this.data.pageSize}`]
    if (this.data.productId) {
      query.push(`product_id=${this.data.productId}`)
    }

    this.setData({
      loading: true,
      error: "",
    })

    try {
      const response = await request({
        url: `/miniapp/messages?${query.join("&")}`,
        requireAuth: true,
      })
      this.setData({
        items: (response.items || []).map(normalizeMessage),
        page: response.page || 1,
        total: response.total || 0,
        loading: false,
        error: "",
      })
    } catch (error) {
      this.setData({
        loading: false,
        error: "留言记录加载失败，请稍后重试。",
      })
      wx.showToast({ title: "加载失败", icon: "none" })
    } finally {
      wx.stopPullDownRefresh()
    }
  },

  goToDetail(event) {
    const productId = Number(event.currentTarget.dataset.productId || 0)
    if (!productId) {
      return
    }

    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },
})
