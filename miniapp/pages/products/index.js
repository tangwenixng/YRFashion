const { request } = require("../../utils/http")
const { normalizeProduct } = require("../../utils/media")

const DEFAULT_IMAGE_RATIO = 1.28
const MIN_IMAGE_RATIO = 0.8
const MAX_IMAGE_RATIO = 1.6
const FEATURED_PAGE_SIZE = 4
const CATEGORY_PREVIEW_LIMIT = 9
const imageRatioCache = {}
const ALL_CATEGORY = { id: 0, name: "全部穿搭" }

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

function hasSelectedCategoryId(categoryId) {
  return categoryId !== null && categoryId !== undefined
}

function buildCategoryOptions(items = []) {
  return [ALL_CATEGORY].concat(
    (items || []).map((item) => Object.assign({}, item, { id: Number(item.id) })),
  )
}

function getCategoryName(categories = [], categoryId) {
  if (!hasSelectedCategoryId(categoryId)) {
    return ""
  }

  const currentCategory = categories.find((item) => Number(item.id) === Number(categoryId))
  return currentCategory ? currentCategory.name : ""
}

function getVisibleCategories(categories = [], expanded = false) {
  if (expanded || categories.length <= CATEGORY_PREVIEW_LIMIT) {
    return categories
  }

  return categories.slice(0, CATEGORY_PREVIEW_LIMIT)
}

Page({
  data: {
    categories: buildCategoryOptions(),
    visibleCategories: getVisibleCategories(buildCategoryOptions()),
    isCategoryExpanded: false,
    categoryToggleVisible: false,
    activeCategoryId: null,
    activeCategoryName: "",
    hasSelectedCategory: false,
    items: [],
    productColumns: [],
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: false,
    loadingCategories: true,
    loadingMore: false,
    error: "",
  },

  onLoad() {
    this.hasShownOnce = false
    this.productRequestToken = 0
    this.setData(buildNavigationState("分类选择"))
    this.loadInitialData()
  },

  onShow() {
    if (!this.hasShownOnce) {
      this.hasShownOnce = true
      return
    }

    this.loadInitialData({ silent: true, showLoading: false })
  },

  onPullDownRefresh() {
    this.loadInitialData()
  },

  onReachBottom() {
    if (this.data.hasSelectedCategory && this.data.hasMore && !this.data.loadingMore && !this.data.loading) {
      this.loadProducts()
    }
  },

  async loadInitialData(options = {}) {
    this.setData({
      loadingCategories: true,
      error: options.silent ? this.data.error : "",
    })

    try {
      await this.loadCategories({ silent: options.silent })
      this.setData({ loadingCategories: false })
      await this.loadProducts({
        reset: true,
        showLoading: options.showLoading !== false,
        silent: options.silent,
      })
    } finally {
      this.setData({ loadingCategories: false })
      wx.stopPullDownRefresh()
    }
  },

  async loadCategories(options = {}) {
    try {
      const response = await request({ url: "/miniapp/categories" })
      const categories = buildCategoryOptions(response.items || [])
      let activeCategoryId = this.data.activeCategoryId

      if (hasSelectedCategoryId(activeCategoryId)) {
        const categoryExists = categories.some((item) => Number(item.id) === Number(activeCategoryId))
        if (!categoryExists) {
          activeCategoryId = null
        }
      }

      const hasSelectedCategory = hasSelectedCategoryId(activeCategoryId)
      const shouldExpand = this.data.isCategoryExpanded
        || categories.length <= CATEGORY_PREVIEW_LIMIT
        || (hasSelectedCategory && categories.some((item, index) => Number(item.id) === Number(activeCategoryId) && index >= CATEGORY_PREVIEW_LIMIT))

      this.setData({
        categories,
        visibleCategories: getVisibleCategories(categories, shouldExpand),
        isCategoryExpanded: shouldExpand,
        categoryToggleVisible: categories.length > CATEGORY_PREVIEW_LIMIT,
        activeCategoryId,
        activeCategoryName: getCategoryName(categories, activeCategoryId),
        hasSelectedCategory,
        items: hasSelectedCategory ? this.data.items : [],
        productColumns: hasSelectedCategory ? this.data.productColumns : [],
        total: hasSelectedCategory ? this.data.total : 0,
        hasMore: hasSelectedCategory ? this.data.hasMore : true,
      })
    } catch (error) {
      if (!options.silent) {
        wx.showToast({ title: "分类加载失败", icon: "none" })
      }
    }
  },

  selectCategory(event) {
    const categoryId = Number(event.currentTarget.dataset.categoryId)
    if (categoryId === this.data.activeCategoryId) {
      return
    }

    this.setData({
      activeCategoryId: categoryId,
      activeCategoryName: event.currentTarget.dataset.categoryName || getCategoryName(this.data.categories, categoryId),
      hasSelectedCategory: true,
      items: [],
      productColumns: [],
      page: 1,
      total: 0,
      hasMore: true,
      loadingMore: false,
      error: "",
    })
    this.loadProducts({ reset: true })
  },

  clearSelection() {
    if (!this.data.hasSelectedCategory) {
      return
    }

    this.productRequestToken += 1
    this.setData({
      visibleCategories: getVisibleCategories(this.data.categories),
      isCategoryExpanded: false,
      categoryToggleVisible: this.data.categories.length > CATEGORY_PREVIEW_LIMIT,
      activeCategoryId: null,
      activeCategoryName: "",
      hasSelectedCategory: false,
      items: [],
      productColumns: [],
      page: 1,
      total: 0,
      hasMore: true,
      loading: false,
      loadingMore: false,
      error: "",
    })
    this.loadProducts({ reset: true, showLoading: false, silent: true })
  },

  toggleCategoryExpand() {
    const isCategoryExpanded = !this.data.isCategoryExpanded
    this.setData({
      isCategoryExpanded,
      visibleCategories: getVisibleCategories(this.data.categories, isCategoryExpanded),
    })
  },

  reloadProducts() {
    if (!this.data.hasSelectedCategory) {
      this.loadInitialData()
      return
    }
    this.loadProducts({ reset: true })
  },

  async loadProducts(options = {}) {
    const isCategoryMode = this.data.hasSelectedCategory
    const reset = Boolean(options.reset)
    const showLoading = options.showLoading !== false
    const nextPage = reset ? 1 : this.data.page
    const pageSize = isCategoryMode ? this.data.pageSize : FEATURED_PAGE_SIZE
    const query = [`page=${nextPage}`, `page_size=${pageSize}`]
    const hasItems = this.data.items.length > 0
    const requestToken = ++this.productRequestToken

    if (isCategoryMode && Number(this.data.activeCategoryId) > 0) {
      query.push(`category_id=${this.data.activeCategoryId}`)
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

      if (requestToken !== this.productRequestToken) {
        return
      }

      const normalizedItems = (response.items || []).map(normalizeProduct)
      const nextItems = reset ? normalizedItems : this.data.items.concat(normalizedItems)
      const productColumns = await this.buildProductColumns(nextItems)

      if (requestToken !== this.productRequestToken) {
        return
      }

      this.setData({
        items: nextItems,
        productColumns,
        page: Number(response.page || nextPage) + 1,
        total: Number(response.total || 0),
        hasMore: isCategoryMode ? Boolean(response.has_more) : false,
        loading: false,
        loadingMore: false,
        error: "",
      })
    } catch (error) {
      if (requestToken !== this.productRequestToken) {
        return
      }

      this.setData({
        loading: false,
        loadingMore: false,
        error: hasItems && reset ? "" : (isCategoryMode ? "分类结果加载失败，请稍后重试。" : "精选穿搭加载失败，请稍后重试。"),
      })
      if (!options.silent) {
        wx.showToast({ title: "加载失败", icon: "none" })
      }
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
