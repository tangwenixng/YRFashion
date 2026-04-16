const { request } = require("../../utils/http")
const { normalizeHome, normalizeProduct } = require("../../utils/media")

const DEFAULT_IMAGE_RATIO = 1.28
const MIN_IMAGE_RATIO = 0.8
const MAX_IMAGE_RATIO = 1.6
const imageRatioCache = {}

Page({
  data: {
    home: null,
    heroBannerUrl: "",
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
    loadingHome: true,
    loadingProducts: true,
    loadingMore: false,
    homeError: "",
    productsError: "",
  },

  onLoad() {
    this.loadInitialData()
  },

  onPullDownRefresh() {
    this.loadInitialData({ refresh: true })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore && !this.data.loadingProducts) {
      this.loadProducts()
    }
  },

  async loadInitialData(options = {}) {
    const refresh = Boolean(options.refresh)

    await Promise.all([
      this.loadHome({
        showLoading: !refresh || !this.data.home,
        silent: refresh,
      }),
      this.loadCategories({ silent: refresh }),
      this.loadProducts({
        reset: true,
        showLoading: !refresh || !this.data.items.length,
        silent: refresh,
      }),
    ])

    wx.stopPullDownRefresh()
  },

  async loadHome(options = {}) {
    const showLoading = options.showLoading !== false
    const hasHome = Boolean(this.data.home)

    if (showLoading) {
      this.setData({
        loadingHome: true,
        homeError: hasHome ? "" : this.data.homeError,
      })
    }

    try {
      const home = normalizeHome(await request({ url: "/miniapp/home" }))
      this.setData({
        home,
        heroBannerUrl: (home.homepage_banner_urls && home.homepage_banner_urls[0]) || "",
        loadingHome: false,
        homeError: "",
      })
    } catch (error) {
      this.setData({
        heroBannerUrl: hasHome ? this.data.heroBannerUrl : "",
        loadingHome: false,
        homeError: hasHome ? "" : "首页加载失败，请稍后重试。",
      })
      if (!options.silent) {
        wx.showToast({ title: "首页加载失败", icon: "none" })
      }
    }
  },

  async loadCategories(options = {}) {
    try {
      const response = await request({ url: "/miniapp/categories" })
      this.setData({
        categories: [{ id: 0, name: "全部" }].concat(response.items || []),
      })
    } catch (error) {
      this.setData({
        categories: [{ id: 0, name: "全部" }],
      })
      if (!options.silent) {
        wx.showToast({ title: "分类加载失败", icon: "none" })
      }
    }
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
      productsError: "",
    })
    this.loadProducts({ reset: true, showLoading: true })
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
      productsError: "",
    })
    this.loadProducts({ reset: true, showLoading: true })
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
      productsError: "",
    })
    this.loadProducts({ reset: true, showLoading: true })
  },

  reloadProducts() {
    this.loadProducts({ reset: true, showLoading: true })
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
      loadingProducts: reset ? showLoading : this.data.loadingProducts,
      loadingMore: reset ? false : true,
      productsError: reset ? "" : this.data.productsError,
    })

    try {
      const response = await request({
        url: `/miniapp/products?${query.join("&")}`,
      })
      const nextItems = reset
        ? (response.items || []).map(normalizeProduct)
        : this.data.items.concat((response.items || []).map(normalizeProduct))
      const productColumns = await this.buildProductColumns(nextItems)

      this.setData({
        items: nextItems,
        productColumns,
        page: Number(response.page || nextPage) + 1,
        total: Number(response.total || 0),
        hasMore: Boolean(response.has_more),
        loadingProducts: false,
        loadingMore: false,
        productsError: "",
      })
    } catch (error) {
      this.setData({
        loadingProducts: false,
        loadingMore: false,
        productsError: hasItems && reset ? "" : "穿搭展示加载失败，请稍后重试。",
      })
      if (!options.silent) {
        wx.showToast({ title: "加载失败", icon: "none" })
      }
    }
  },

  scrollToFeed() {
    wx.pageScrollTo({
      selector: "#feed-section",
      duration: 320,
      fail: () => {},
    })
  },

  goToProductDetail(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({ url: `/pages/product-detail/index?id=${productId}` })
  },

  goToContact() {
    wx.navigateTo({ url: "/pages/contact/index" })
  },

  previewBanner(event) {
    const current = event.currentTarget.dataset.imageUrl || ""
    const urls = this.data.home && Array.isArray(this.data.home.homepage_banner_urls)
      ? this.data.home.homepage_banner_urls.filter(Boolean)
      : []

    if (!current || !urls.length) {
      return
    }

    wx.previewImage({
      current,
      urls,
    })
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
