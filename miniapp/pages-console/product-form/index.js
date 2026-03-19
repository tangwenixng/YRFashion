const { ensureConsoleLogin, redirectToConsoleLogin } = require("../utils/console-auth")
const { fetchConsoleCategories } = require("../utils/console-api/categories")
const {
  createConsoleProduct,
  fetchConsoleProduct,
  updateConsoleProduct,
} = require("../utils/console-api/products")

const STATUS_OPTIONS = [
  { value: "draft", label: "草稿" },
  { value: "published", label: "已发布" },
  { value: "archived", label: "已归档" },
]

function buildCategoryOptions(categories) {
  return [{ id: null, name: "未分类" }].concat(
    (categories || []).map((item) => ({
      id: item.id,
      name: item.status === "active" ? item.name : `${item.name}（已停用）`,
    })),
  )
}

function goBackToProducts() {
  wx.navigateBack({
    fail: () => {
      wx.reLaunch({
        url: "/pages-console/products/index",
      })
    },
  })
}

Page({
  data: {
    productId: null,
    loading: true,
    saving: false,
    categoryOptions: [{ id: null, name: "未分类" }],
    categoryIndex: 0,
    statusOptions: STATUS_OPTIONS,
    statusIndex: 0,
    name: "",
    description: "",
    tagsText: "",
    sortOrder: "0",
  },

  onLoad(query) {
    const productId = Number(query.id || 0) || null
    this.setData({ productId })
    wx.setNavigationBarTitle({
      title: productId ? "编辑展示" : "新增展示",
    })
  },

  onShow() {
    ensureConsoleLogin()
      .then(() => this.loadPage())
      .catch(() => redirectToConsoleLogin())
  },

  async loadPage() {
    this.setData({ loading: true })

    try {
      const [categories, product] = await Promise.all([
        fetchConsoleCategories(),
        this.data.productId ? fetchConsoleProduct(this.data.productId) : Promise.resolve(null),
      ])

      const categoryOptions = buildCategoryOptions(categories)
      const categoryIndex = categoryOptions.findIndex((item) => item.id === (product ? product.category_id : null))
      const statusIndex = STATUS_OPTIONS.findIndex((item) => item.value === (product ? product.status : "draft"))

      this.setData({
        loading: false,
        categoryOptions,
        categoryIndex: categoryIndex >= 0 ? categoryIndex : 0,
        statusIndex: statusIndex >= 0 ? statusIndex : 0,
        name: product ? product.name : "",
        description: product ? product.description : "",
        tagsText: product ? product.tags.join(", ") : "",
        sortOrder: product ? String(product.sort_order) : "0",
      })
    } catch (_error) {
      this.setData({ loading: false })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  handleNameInput(event) {
    this.setData({ name: event.detail.value })
  },

  handleDescriptionInput(event) {
    this.setData({ description: event.detail.value })
  },

  handleTagsInput(event) {
    this.setData({ tagsText: event.detail.value })
  },

  handleSortInput(event) {
    this.setData({ sortOrder: event.detail.value })
  },

  handleCategoryChange(event) {
    this.setData({
      categoryIndex: Number(event.detail.value),
    })
  },

  handleStatusChange(event) {
    this.setData({
      statusIndex: Number(event.detail.value),
    })
  },

  async submit() {
    const name = this.data.name.trim()
    if (!name) {
      wx.showToast({ title: "请填写展示名称", icon: "none" })
      return
    }

    const selectedCategory = this.data.categoryOptions[this.data.categoryIndex] || this.data.categoryOptions[0]
    const selectedStatus = this.data.statusOptions[this.data.statusIndex] || this.data.statusOptions[0]

    const payload = {
      name,
      category_id: selectedCategory.id,
      description: this.data.description.trim(),
      tags: this.data.tagsText
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      status: selectedStatus.value,
      sort_order: Number(this.data.sortOrder) || 0,
    }

    this.setData({ saving: true })

    try {
      if (this.data.productId) {
        await updateConsoleProduct(this.data.productId, payload)
        wx.showToast({ title: "保存成功", icon: "success" })
        setTimeout(() => {
          goBackToProducts()
        }, 300)
      } else {
        const product = await createConsoleProduct(payload)
        this.setData({ saving: false })
        wx.showModal({
          title: "展示已创建",
          content: "现在去上传图片吗？",
          confirmText: "去上传",
          cancelText: "稍后",
          success: (result) => {
            if (result.confirm) {
              wx.redirectTo({
                url: `/pages-console/product-images/index?id=${product.id}`,
              })
              return
            }

            goBackToProducts()
          },
        })
        return
      }
    } catch (_error) {
      wx.showToast({ title: "保存失败", icon: "none" })
    }

    this.setData({ saving: false })
  },
})
