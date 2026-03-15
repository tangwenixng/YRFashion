const { ensureAdminLogin, redirectToAdminLogin } = require("../../utils/admin-auth")
const { formatDateTime, getMessageStatusLabel } = require("../../utils/admin-format")
const {
  fetchAdminMessages,
  markAdminMessageRead,
  markAdminMessageUnread,
} = require("../../utils/admin-api/messages")

function decorateMessage(message) {
  const userDisplay = message.miniapp_user_nickname || message.miniapp_user_openid

  return Object.assign({}, message, {
    avatar_initial: (userDisplay || "?").slice(0, 1),
    created_at_text: formatDateTime(message.created_at),
    status_label: getMessageStatusLabel(message.status),
    user_display: userDisplay,
  })
}

Page({
  data: {
    statusFilter: "all",
    statusTabs: [
      { value: "all", label: "全部" },
      { value: "unread", label: "未读" },
      { value: "read", label: "已读" },
      { value: "replied", label: "已回复" },
    ],
    items: [],
    loading: true,
    error: "",
  },

  onShow() {
    ensureAdminLogin()
      .then(() => this.loadMessages())
      .catch(() => redirectToAdminLogin())
  },

  async loadMessages() {
    this.setData({
      loading: true,
      error: "",
    })

    try {
      const status = this.data.statusFilter === "all" ? "" : this.data.statusFilter
      const items = await fetchAdminMessages(status)
      this.setData({
        items: items.map(decorateMessage),
        loading: false,
      })
    } catch (_error) {
      this.setData({
        loading: false,
        error: "咨询列表加载失败。",
      })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  switchStatus(event) {
    this.setData({
      statusFilter: event.currentTarget.dataset.status,
    })
    this.loadMessages()
  },

  openDetail(event) {
    const messageId = event.currentTarget.dataset.messageId
    wx.navigateTo({
      url: `/pages-admin/message-detail/index?id=${messageId}`,
    })
  },

  async markRead(event) {
    const messageId = Number(event.currentTarget.dataset.messageId)
    try {
      await markAdminMessageRead(messageId)
      wx.showToast({ title: "已标记为已读", icon: "success" })
      this.loadMessages()
    } catch (_error) {
      wx.showToast({ title: "操作失败", icon: "none" })
    }
  },

  async markUnread(event) {
    const messageId = Number(event.currentTarget.dataset.messageId)
    try {
      await markAdminMessageUnread(messageId)
      wx.showToast({ title: "已标记为未读", icon: "success" })
      this.loadMessages()
    } catch (_error) {
      wx.showToast({ title: "操作失败", icon: "none" })
    }
  },
})
