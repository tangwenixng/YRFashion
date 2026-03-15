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
      this.setData({ loading: false, error: "Failed to load contact info." })
      wx.showToast({ title: "Load failed", icon: "none" })
    }
  },

  handleCall() {
    const phone = this.data.contact && this.data.contact.contact_phone
    if (!phone) {
      wx.showToast({ title: "No phone number", icon: "none" })
      return
    }
    wx.makePhoneCall({ phoneNumber: phone })
  },

  handleCopyWechat() {
    const wechatId = this.data.contact && this.data.contact.wechat_id
    if (!wechatId) {
      wx.showToast({ title: "No WeChat ID", icon: "none" })
      return
    }
    wx.setClipboardData({ data: wechatId })
  },

  goToAdminLogin() {
    wx.navigateTo({
      url: "/pages-admin/login/index",
    })
  },
})
