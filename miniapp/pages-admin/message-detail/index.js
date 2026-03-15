const { ensureAdminLogin, redirectToAdminLogin } = require("../../utils/admin-auth")
const { formatDateTime, getMessageStatusLabel } = require("../../utils/admin-format")
const {
  fetchAdminMessages,
  markAdminMessageRead,
  markAdminMessageUnread,
  replyAdminMessage,
} = require("../../utils/admin-api/messages")

function decorateMessage(message) {
  const userDisplay = message.miniapp_user_nickname || message.miniapp_user_openid

  return Object.assign({}, message, {
    avatar_initial: (userDisplay || "?").slice(0, 1),
    created_at_text: formatDateTime(message.created_at),
    read_at_text: formatDateTime(message.read_at),
    reply_at_text: formatDateTime(message.reply_at),
    status_label: getMessageStatusLabel(message.status),
    user_display: userDisplay,
  })
}

Page({
  data: {
    messageId: null,
    message: null,
    replyContent: "",
    loading: true,
    saving: false,
    error: "",
  },

  onLoad(query) {
    this.setData({
      messageId: Number(query.id || 0) || null,
    })
  },

  onShow() {
    ensureAdminLogin()
      .then(() => this.loadDetail())
      .catch(() => redirectToAdminLogin())
  },

  async loadDetail() {
    if (!this.data.messageId) {
      this.setData({
        loading: false,
        error: "缺少咨询记录编号。",
      })
      return
    }

    this.setData({
      loading: true,
      error: "",
    })

    try {
      const items = await fetchAdminMessages()
      const current = items.find((item) => item.id === this.data.messageId)
      if (!current) {
        this.setData({
          loading: false,
          error: "未找到对应咨询记录。",
        })
        return
      }

      const message = decorateMessage(current)
      this.setData({
        loading: false,
        message,
        replyContent: message.reply_content || "",
      })
    } catch (_error) {
      this.setData({
        loading: false,
        error: "咨询详情加载失败。",
      })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  handleReplyInput(event) {
    this.setData({
      replyContent: event.detail.value,
    })
  },

  async markRead() {
    if (!this.data.message) {
      return
    }
    try {
      const message = await markAdminMessageRead(this.data.message.id)
      this.setData({
        message: decorateMessage(message),
      })
      wx.showToast({ title: "已标记为已读", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "操作失败", icon: "none" })
    }
  },

  async markUnread() {
    if (!this.data.message) {
      return
    }
    try {
      const message = await markAdminMessageUnread(this.data.message.id)
      this.setData({
        message: decorateMessage(message),
      })
      wx.showToast({ title: "已标记为未读", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "操作失败", icon: "none" })
    }
  },

  async submitReply() {
    const replyContent = this.data.replyContent.trim()
    if (!this.data.message) {
      return
    }
    if (!replyContent) {
      wx.showToast({ title: "回复内容不能为空", icon: "none" })
      return
    }

    this.setData({ saving: true })
    try {
      const message = await replyAdminMessage(this.data.message.id, replyContent)
      this.setData({
        saving: false,
        message: decorateMessage(message),
        replyContent: message.reply_content || replyContent,
      })
      wx.showToast({ title: "回复已发送", icon: "success" })
    } catch (_error) {
      this.setData({ saving: false })
      wx.showToast({ title: "回复失败", icon: "none" })
    }
  },
})
