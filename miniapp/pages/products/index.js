const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

const DEFAULT_IMAGE_RATIO = 1.28
const MIN_IMAGE_RATIO = 0.8
const MAX_IMAGE_RATIO = 1.6
const imageRatioCache = {}

function buildNavigationState(navTitle = "") {
  const systemInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
  const statusBarHeight = Number(systemInfo.statusBarHeight || 20)
  const windowWidth = Number(systemInfo.windowWidth || 375)
  let navBarHeight = 44
  let navRightSpaceWidth = 96

  if (wx.getMenuButtonBoundingClientRect) {
    const menuButtonRect = wx.getMenuButtonBoundingClientRect()
    if (menuButtonRect && menuButtonRect.width) {
      navBarHeight = menuButtonRect.height + (menuButtonRect.top - statusBarHeight) * 2
      navRightSpaceWidth = menuButtonRect.width + (windowWidth - menuButtonRect.right) * 2
    }
  }

  return {
    navTitle,
    statusBarHeight,
    navBarHeight,
    navBarTotalHeight: statusBarHeight + navBarHeight,
    navRightSpaceWidth,
  }
}

Page({
  data: {
    categories: [{ id: 0, name: "全部" }],
    activeCategoryId: 0,
    keyword: "",
    draftKeyword: "",
    items: [],
    productColumns: [],
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
    this.hasShownOnce = false
    this.setData(buildNavigationState("穿搭分享"))
    this.loadInitialData()
  },

  onShow() {
    if (!this.hasShownOnce) {
      this.hasShownOnce = true
      return
    }

    this.loadProducts({
      reset: true,
      showLoading: false,
      silent: true,
    })
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
      productColumns: [],
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
      productColumns: [],
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
      productColumns: [],
      page: 1,
      total: 0,
      hasMore: true,
      error: "",
    })
    this.loadProducts({ reset: true })
  },

  async loadProducts(options = {}) {
    const reset = Boolean(options.reset)
    const showLoading = options.showLoading !== false
    const nextPage = reset ? 1 : this.data.page
    const query = [`page=${nextPage}`, `page_size=${this.data.pageSize}`]
    const hasItems = this.data.items.length > 0
    if (this.data.activeCategoryId > 0) {
      query.push(`category_id=${this.data.activeCategoryId}`)
    }
    if (this.data.keyword) {
      query.push(`keyword=${encodeURIComponent(this.data.keyword)}`)
    }

    this.setData({
      loading: reset ? showLoading : this.data.loading,
      loadingMore: !reset,
      error: reset ? "" : this.data.error,
    })

    try {
      const response = await request({
        url: `/miniapp/products?${query.join("&")}`,
      })
      const nextItems = reset
        ? response.items.map(normalizeProduct)
        : this.data.items.concat(response.items.map(normalizeProduct))
      const productColumns = await this.buildProductColumns(nextItems)

      this.setData({
        items: nextItems,
        productColumns,
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
        error: hasItems && reset ? "" : "穿搭展示加载失败，请稍后重试。",
      })
      if (!options.silent) {
        wx.showToast({ title: "加载失败", icon: "none" })
      }
    } finally {
      wx.stopPullDownRefresh()
    }
  },

  goToDetail(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" })
  },

  goBack() {
    if (getCurrentPages().length > 1) {
      wx.navigateBack({ delta: 1 })
      return
    }
    this.goHome()
  },

  async buildProductColumns(products = []) {
    const columns = [[], []]
    const columnHeights = [0, 0]

    const items = await Promise.all(
      products.map(async (product) => {
        const imageRatio = await this.getImageRatio(product.cover_image_url)
        return Object.assign({}, product, { imageRatio })
      }),
    )

    items.forEach((product) => {
      const columnIndex = columnHeights[0] <= columnHeights[1] ? 0 : 1
      columns[columnIndex].push(product)
      columnHeights[columnIndex] += product.imageRatio + 0.62
    })

    return columns.filter((column) => column.length)
  },

  getImageRatio(url) {
    if (!url) {
      return Promise.resolve(DEFAULT_IMAGE_RATIO)
    }

    if (imageRatioCache[url]) {
      return Promise.resolve(imageRatioCache[url])
    }

    return new Promise((resolve) => {
      wx.getImageInfo({
        src: url,
        success: (result) => {
          const ratio = this.normalizeImageRatio(result)
          imageRatioCache[url] = ratio
          resolve(ratio)
        },
        fail: () => {
          imageRatioCache[url] = DEFAULT_IMAGE_RATIO
          resolve(DEFAULT_IMAGE_RATIO)
        },
      })
    })
  },

  normalizeImageRatio(imageInfo = {}) {
    const width = Number(imageInfo.width || 0)
    const height = Number(imageInfo.height || 0)
    if (!width || !height) {
      return DEFAULT_IMAGE_RATIO
    }

    const ratio = height / width
    return Math.min(Math.max(ratio, MIN_IMAGE_RATIO), MAX_IMAGE_RATIO)
  },
})
