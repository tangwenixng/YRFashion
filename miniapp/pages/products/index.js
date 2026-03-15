const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

Page({
  data: {
    items: [],
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: true,
    loadingMore: false,
    error: "",
  },

  onLoad() {
    this.loadProducts({ reset: true })
  },

  onPullDownRefresh() {
    this.loadProducts({ reset: true })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadProducts()
    }
  },

  reloadProducts() {
    this.loadProducts({ reset: true })
  },

  async loadProducts(options = {}) {
    const reset = Boolean(options.reset)
    const nextPage = reset ? 1 : this.data.page
    this.setData({
      loading: reset,
      loadingMore: !reset,
      error: reset ? "" : this.data.error,
    })

    try {
      const response = await request({
        url: `/miniapp/products?page=${nextPage}&page_size=${this.data.pageSize}`,
      })

      this.setData({
        items: reset
          ? response.items.map(normalizeProduct)
          : this.data.items.concat(response.items.map(normalizeProduct)),
        page: response.page + 1,
        total: response.total,
        hasMore: response.has_more,
        loading: false,
        loadingMore: false,
        error: "",
      })
    } catch (error) {
      this.setData({
        loading: false,
        loadingMore: false,
        error: "穿搭展示加载失败，请稍后重试。",
      })
      wx.showToast({ title: "加载失败", icon: "none" })
    } finally {
      wx.stopPullDownRefresh()
    }
  },

  goToDetail(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },
})
