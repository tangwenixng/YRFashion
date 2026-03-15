const { clearAdminSession, ensureAdminLogin, getAdminProfile, redirectToAdminLogin } = require("../../utils/admin-auth")
const { fetchAdminMessages } = require("../../utils/admin-api/messages")
const { fetchAdminProducts } = require("../../utils/admin-api/products")

Page({
  data: {
    profile: null,
    loading: true,
    productCount: 0,
    unreadMessageCount: 0,
    repliedMessageCount: 0,
  },

  onShow() {
    ensureAdminLogin()
      .then(() => {
        this.loadHome()
      })
      .catch(() => {
        redirectToAdminLogin()
      })
  },

  async loadHome() {
    this.setData({
      loading: true,
      profile: getAdminProfile(),
    })

    try {
      const [products, messages] = await Promise.all([
        fetchAdminProducts(),
        fetchAdminMessages(),
      ])

      const unreadMessageCount = messages.filter((item) => item.status === "unread").length
      const repliedMessageCount = messages.filter((item) => item.status === "replied").length

      this.setData({
        loading: false,
        profile: getAdminProfile(),
        productCount: products.length,
        unreadMessageCount,
        repliedMessageCount,
      })
    } catch (_error) {
      this.setData({ loading: false })
      wx.showToast({ title: "Load failed", icon: "none" })
    }
  },

  goToProducts() {
    wx.navigateTo({
      url: "/pages-admin/products/index",
    })
  },

  goToMessages() {
    wx.navigateTo({
      url: "/pages-admin/messages/index",
    })
  },

  logout() {
    clearAdminSession()
    wx.reLaunch({
      url: "/pages-admin/login/index",
    })
  },
})
