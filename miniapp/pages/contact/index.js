const { request } = require("../../utils/http")

Page({
  data: {
    contact: null,
    loading: true,
    error: "",
  },

  onLoad() {
    this.loadContact()
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

  goToAdminLogin() {
    wx.navigateTo({
      url: "/pages-admin/login/index",
    })
  },
})
