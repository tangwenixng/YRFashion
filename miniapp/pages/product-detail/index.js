const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

Page({
  data: {
    productId: null,
    product: null,
    loading: true,
    error: "",
  },

  onLoad(query) {
    const productId = Number(query.id || 0)
    this.setData({ productId })
    this.loadProduct(productId)
  },

  reloadProduct() {
    this.loadProduct(this.data.productId)
  },

  async loadProduct(productId = this.data.productId) {
    this.setData({ loading: true, error: "" })
    try {
      const product = normalizeProduct(await request({ url: `/miniapp/products/${productId}` }))
      this.setData({ product, loading: false, error: "" })
      wx.setNavigationBarTitle({ title: product.name })
    } catch (error) {
      this.setData({ loading: false, error: "商品详情加载失败，请稍后重试。" })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  handleConsult() {
    const product = this.data.product
    if (!product) {
      return
    }
    const productName = encodeURIComponent(product.name)
    wx.navigateTo({
      url: `/pages/message/index?productId=${product.id}&productName=${productName}`,
    })
  },

  goToContact() {
    wx.navigateTo({ url: "/pages/contact/index" })
  },

  onShareAppMessage() {
    const product = this.data.product
    if (!product) {
      return {
        title: "YRFasion",
        path: "/pages/home/index",
      }
    }

    return {
      title: product.name,
      path: `/pages/product-detail/index?id=${product.id}`,
      imageUrl: product.cover_image_url || undefined,
    }
  },
})
