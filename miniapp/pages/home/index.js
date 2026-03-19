const { request } = require("../../utils/http")
const { normalizeHome } = require("../../utils/media")

const DEFAULT_IMAGE_RATIO = 1.28
const MIN_IMAGE_RATIO = 0.8
const MAX_IMAGE_RATIO = 1.6
const imageRatioCache = {}

Page({
  data: {
    home: null,
    featuredColumns: [],
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
      const featuredColumns = await this.buildFeaturedColumns(home.featured_products || [])
      this.setData({
        home,
        featuredColumns,
        loading: false,
        error: "",
      })
    } catch (error) {
      this.setData({
        loading: false,
        error: "首页加载失败，请稍后重试。",
        featuredColumns: [],
      })
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

  async buildFeaturedColumns(products = []) {
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
