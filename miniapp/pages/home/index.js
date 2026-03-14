const { request } = require("../../utils/http")
const { normalizeHome } = require("../../utils/media")

Page({
  data: {
    home: null,
    loading: true,
    error: "",
  },

  onLoad() {
    this.loadHome()
  },

  onPullDownRefresh() {
    this.loadHome({ refresh: true })
  },

  async loadHome(options = {}) {
    if (!options.refresh) {
      this.setData({ loading: true, error: "" })
    }

    try {
      const home = normalizeHome(await request({ url: "/miniapp/home" }))
      this.setData({ home, loading: false, error: "" })
    } catch (error) {
      this.setData({ loading: false, error: "首页加载失败，请稍后重试。" })
      if (!options.silent) {
        wx.showToast({ title: "首页加载失败", icon: "none" })
      }
    } finally {
      wx.stopPullDownRefresh()
    }
  },

  goToProducts() {
    wx.navigateTo({ url: "/pages/products/index" })
  },

  goToProductDetail(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },

  goToContact() {
    wx.navigateTo({ url: "/pages/contact/index" })
  },
})
