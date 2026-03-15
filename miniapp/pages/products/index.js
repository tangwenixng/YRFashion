const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

Page({
  data: {
    categories: [{ id: 0, name: "全部" }],
    activeCategoryId: 0,
    keyword: "",
    draftKeyword: "",
    items: [],
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: true,
    loadingCategories: true,
    loadingMore: false,
    error: "",
  },

  onLoad() {
    this.loadInitialData()
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

  onKeywordInput(event) {
    this.setData({ draftKeyword: event.detail.value })
  },

  submitSearch() {
    const keyword = (this.data.draftKeyword || "").trim()
    if (keyword === this.data.keyword) {
      return
    }

    this.setData({
      keyword,
      items: [],
      page: 1,
      total: 0,
      hasMore: true,
      error: "",
    })
    this.loadProducts({ reset: true })
  },

  clearSearch() {
    if (!this.data.keyword && !this.data.draftKeyword) {
      return
    }

    this.setData({
      keyword: "",
      draftKeyword: "",
      items: [],
      page: 1,
      total: 0,
      hasMore: true,
      error: "",
    })
    this.loadProducts({ reset: true })
  },

  async loadInitialData() {
    this.setData({ loading: true, loadingCategories: true, error: "" })

    try {
      await Promise.all([this.loadCategories(), this.loadProducts({ reset: true })])
    } finally {
      this.setData({ loadingCategories: false })
    }
  },

  async loadCategories() {
    try {
      const response = await request({ url: "/miniapp/categories" })
      this.setData({
        categories: [{ id: 0, name: "全部" }].concat(response.items || []),
      })
    } catch (error) {
      this.setData({
        categories: [{ id: 0, name: "全部" }],
      })
      wx.showToast({ title: "分类加载失败", icon: "none" })
    }
  },

  selectCategory(event) {
    const categoryId = Number(event.currentTarget.dataset.categoryId || 0)
    if (categoryId === this.data.activeCategoryId) {
      return
    }

    this.setData({
      activeCategoryId: categoryId,
      items: [],
      page: 1,
      total: 0,
      hasMore: true,
      error: "",
    })
    this.loadProducts({ reset: true })
  },

  async loadProducts(options = {}) {
    const reset = Boolean(options.reset)
    const nextPage = reset ? 1 : this.data.page
    const query = [`page=${nextPage}`, `page_size=${this.data.pageSize}`]
    if (this.data.activeCategoryId > 0) {
      query.push(`category_id=${this.data.activeCategoryId}`)
    }
    if (this.data.keyword) {
      query.push(`keyword=${encodeURIComponent(this.data.keyword)}`)
    }

    this.setData({
      loading: reset,
      loadingMore: !reset,
      error: reset ? "" : this.data.error,
    })

    try {
      const response = await request({
        url: `/miniapp/products?${query.join("&")}`,
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
