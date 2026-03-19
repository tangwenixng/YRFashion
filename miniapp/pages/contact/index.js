const { request } = require("../../utils/http")

const CONSOLE_ENTRY_TAP_THRESHOLD = 10
const CONSOLE_ENTRY_TAP_INTERVAL = 1500

Page({
  data: {
    contact: null,
    loading: true,
    error: "",
  },

  onLoad() {
    this.consoleEntryTapCount = 0
    this.consoleEntryTapTimer = null
    this.loadContact()
  },

  onUnload() {
    this.resetConsoleEntryTapState()
  },

  async loadContact() {
    this.setData({ loading: true, error: "" })
    try {
      const contact = await request({ url: "/miniapp/shop/contact" })
      this.setData({ contact, loading: false, error: "" })
    } catch (_error) {
      this.setData({ loading: false, error: "联系方式加载失败，请稍后重试。" })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  handleCall() {
    const phone = this.data.contact && this.data.contact.contact_phone
    if (!phone) {
      wx.showToast({ title: "暂未设置联系电话", icon: "none" })
      return
    }
    wx.makePhoneCall({ phoneNumber: phone })
  },

  handleCopyWechat() {
    const wechatId = this.data.contact && this.data.contact.wechat_id
    if (!wechatId) {
      wx.showToast({ title: "暂未设置微信号", icon: "none" })
      return
    }
    wx.setClipboardData({ data: wechatId })
  },

  goToMessageHistory() {
    wx.navigateTo({
      url: "/pages/message-history/index",
    })
  },

  handleConsoleEntryTap() {
    if (this.consoleEntryTapTimer) {
      clearTimeout(this.consoleEntryTapTimer)
    }

    this.consoleEntryTapCount = (this.consoleEntryTapCount || 0) + 1

    if (this.consoleEntryTapCount >= CONSOLE_ENTRY_TAP_THRESHOLD) {
      this.resetConsoleEntryTapState()
      this.goToConsoleLogin()
      return
    }

    this.consoleEntryTapTimer = setTimeout(() => {
      this.resetConsoleEntryTapState()
    }, CONSOLE_ENTRY_TAP_INTERVAL)
  },

  resetConsoleEntryTapState() {
    this.consoleEntryTapCount = 0
    if (this.consoleEntryTapTimer) {
      clearTimeout(this.consoleEntryTapTimer)
      this.consoleEntryTapTimer = null
    }
  },

  goToConsoleLogin() {
    wx.showToast({
      title: "正在进入工作台",
      icon: "none",
      duration: 1200,
    })
    wx.navigateTo({
      url: "/pages-console/login/index",
    })
  },
})
