const { ensureConsoleLogin, redirectToConsoleLogin } = require("../utils/console-auth")
const { getProductStatusLabel } = require("../utils/console-format")
const {
  fetchConsoleProducts,
  updateConsoleProduct,
  updateConsoleProductSort,
} = require("../utils/console-api/products")

function decorateProduct(product) {
  return Object.assign({}, product, {
    status_label: getProductStatusLabel(product.status),
  })
}

function applyFilters(items, keyword, statusFilter) {
  const normalizedKeyword = (keyword || "").trim().toLowerCase()

  return items.filter((item) => {
    const matchKeyword =
      !normalizedKeyword ||
      item.name.toLowerCase().includes(normalizedKeyword) ||
      (item.category_name || "").toLowerCase().includes(normalizedKeyword)

    const matchStatus = statusFilter === "all" || item.status === statusFilter
    return matchKeyword && matchStatus
  })
}

Page({
  data: {
    allItems: [],
    items: [],
    loading: true,
    error: "",
    keyword: "",
    statusFilter: "all",
    statusTabs: [
      { value: "all", label: "全部" },
      { value: "published", label: "已发布" },
      { value: "draft", label: "草稿" },
      { value: "archived", label: "已归档" },
    ],
  },

  onShow() {
    ensureConsoleLogin()
      .then(() => this.loadProducts())
      .catch(() => redirectToConsoleLogin())
  },

  onPullDownRefresh() {
    this.loadProducts()
  },

  async loadProducts() {
    this.setData({
      loading: true,
      error: "",
    })

    try {
      const items = (await fetchConsoleProducts()).map(decorateProduct)
      this.setData({
        allItems: items,
        items: applyFilters(items, this.data.keyword, this.data.statusFilter),
        loading: false,
      })
    } catch (_error) {
      this.setData({
        loading: false,
        error: "展示列表加载失败。",
      })
      wx.showToast({ title: "加载失败", icon: "none" })
    } finally {
      wx.stopPullDownRefresh()
    }
  },

  handleKeywordInput(event) {
    const keyword = event.detail.value
    this.setData({
      keyword,
      items: applyFilters(this.data.allItems, keyword, this.data.statusFilter),
    })
  },

  switchStatus(event) {
    const statusFilter = event.currentTarget.dataset.status
    this.setData({
      statusFilter,
      items: applyFilters(this.data.allItems, this.data.keyword, statusFilter),
    })
  },

  openCreate() {
    wx.navigateTo({
      url: "/pages-console/product-form/index",
    })
  },

  openEdit(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({
      url: `/pages-console/product-form/index?id=${productId}`,
    })
  },

  openImages(event) {
    const productId = event.currentTarget.dataset.productId
    wx.navigateTo({
      url: `/pages-console/product-images/index?id=${productId}`,
    })
  },

  handleSortInput(event) {
    const productId = Number(event.currentTarget.dataset.productId)
    const nextValue = event.detail.value
    const updateItem = (item) =>
      item.id === productId ? Object.assign({}, item, { sort_order: nextValue }) : item

    const allItems = this.data.allItems.map(updateItem)
    this.setData({
      allItems,
      items: applyFilters(allItems, this.data.keyword, this.data.statusFilter),
    })
  },

  async saveSort(event) {
    const productId = Number(event.currentTarget.dataset.productId)
    const product = this.data.allItems.find((item) => item.id === productId)
    if (!product) {
      return
    }

    try {
      await updateConsoleProductSort(productId, Number(product.sort_order) || 0)
      wx.showToast({ title: "排序已更新", icon: "success" })
      this.loadProducts()
    } catch (_error) {
      wx.showToast({ title: "保存失败", icon: "none" })
    }
  },

  async toggleStatus(event) {
    const productId = Number(event.currentTarget.dataset.productId)
    const product = this.data.allItems.find((item) => item.id === productId)
    if (!product) {
      return
    }

    const nextStatus = product.status === "published" ? "draft" : "published"

    try {
      await updateConsoleProduct(productId, {
        name: product.name,
        category_id: product.category_id,
        description: product.description,
        tags: product.tags,
        status: nextStatus,
        sort_order: Number(product.sort_order) || 0,
      })
      wx.showToast({
        title: nextStatus === "published" ? "已发布" : "已下架",
        icon: "success",
      })
      this.loadProducts()
    } catch (_error) {
      wx.showToast({ title: "状态更新失败", icon: "none" })
    }
  },
})
