const { clearConsoleSession, ensureConsoleLogin, getConsoleProfile, redirectToConsoleLogin } = require("../utils/console-auth")
const { fetchConsoleMessages } = require("../utils/console-api/messages")
const { fetchConsoleProducts } = require("../utils/console-api/products")

Page({
  data: {
    profile: null,
    loading: true,
    productCount: 0,
    unreadMessageCount: 0,
    repliedMessageCount: 0,
  },

  onShow() {
    ensureConsoleLogin()
      .then(() => {
        this.loadHome()
      })
      .catch(() => {
        redirectToConsoleLogin()
      })
  },

  async loadHome() {
    this.setData({
      loading: true,
      profile: getConsoleProfile(),
    })

    try {
      const [products, messages] = await Promise.all([
        fetchConsoleProducts(),
        fetchConsoleMessages(),
      ])

      const unreadMessageCount = messages.filter((item) => item.status === "unread").length
      const repliedMessageCount = messages.filter((item) => item.status === "replied").length

      this.setData({
        loading: false,
        profile: getConsoleProfile(),
        productCount: products.length,
        unreadMessageCount,
        repliedMessageCount,
      })
    } catch (_error) {
      this.setData({ loading: false })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  goToProducts() {
    wx.navigateTo({
      url: "/pages-console/products/index",
    })
  },

  goToMessages() {
    wx.navigateTo({
      url: "/pages-console/messages/index",
    })
  },

  logout() {
    clearConsoleSession()
    wx.reLaunch({
      url: "/pages-console/login/index",
    })
  },
})
