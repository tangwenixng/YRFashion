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
        error: "Missing message id.",
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
          error: "Message not found.",
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
        error: "Failed to load message detail.",
      })
      wx.showToast({ title: "Load failed", icon: "none" })
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
      wx.showToast({ title: "Marked read", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "Action failed", icon: "none" })
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
      wx.showToast({ title: "Marked unread", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "Action failed", icon: "none" })
    }
  },

  async submitReply() {
    const replyContent = this.data.replyContent.trim()
    if (!this.data.message) {
      return
    }
    if (!replyContent) {
      wx.showToast({ title: "Reply cannot be empty", icon: "none" })
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
      wx.showToast({ title: "Reply sent", icon: "success" })
    } catch (_error) {
      this.setData({ saving: false })
      wx.showToast({ title: "Reply failed", icon: "none" })
    }
  },
})
