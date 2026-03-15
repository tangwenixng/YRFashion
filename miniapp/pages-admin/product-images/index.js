const { ensureAdminLogin, redirectToAdminLogin } = require("../../utils/admin-auth")
const {
  deleteAdminProductImage,
  fetchAdminProduct,
  setAdminProductCover,
  updateAdminProductImagesSort,
  uploadAdminProductImage,
} = require("../../utils/admin-api/products")

Page({
  data: {
    productId: null,
    product: null,
    loading: true,
    uploading: false,
    savingSort: false,
    error: "",
  },

  onLoad(query) {
    const productId = Number(query.id || 0)
    this.setData({ productId })
  },

  onShow() {
    ensureAdminLogin()
      .then(() => this.loadProduct())
      .catch(() => redirectToAdminLogin())
  },

  async loadProduct() {
    if (!this.data.productId) {
      this.setData({
        loading: false,
        error: "Missing product id.",
      })
      return
    }

    this.setData({
      loading: true,
      error: "",
    })

    try {
      const product = await fetchAdminProduct(this.data.productId)
      this.setData({
        product,
        loading: false,
      })
      wx.setNavigationBarTitle({
        title: `${product.name} Images`,
      })
    } catch (_error) {
      this.setData({
        loading: false,
        error: "Failed to load product images.",
      })
      wx.showToast({ title: "Load failed", icon: "none" })
    }
  },

  chooseImages() {
    if (!this.data.product) {
      return
    }

    wx.chooseImage({
      count: 9,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success: async ({ tempFilePaths }) => {
        if (!tempFilePaths || !tempFilePaths.length) {
          return
        }

        this.setData({ uploading: true })

        try {
          const startSort = this.data.product.images.length
          for (let index = 0; index < tempFilePaths.length; index += 1) {
            await uploadAdminProductImage(
              this.data.productId,
              tempFilePaths[index],
              startSort + index,
              this.data.product.images.length === 0 && index === 0,
            )
          }
          wx.showToast({ title: "Upload done", icon: "success" })
          this.loadProduct()
        } catch (_error) {
          this.setData({ uploading: false })
          wx.showToast({ title: "Upload failed", icon: "none" })
          return
        }

        this.setData({ uploading: false })
      },
    })
  },

  handleSortInput(event) {
    const imageId = Number(event.currentTarget.dataset.imageId)
    const nextValue = event.detail.value
    const product = this.data.product
    if (!product) {
      return
    }

    const images = product.images.map((image) =>
      image.id === imageId ? Object.assign({}, image, { sort_order: nextValue }) : image,
    )

    this.setData({
      product: Object.assign({}, product, { images }),
    })
  },

  async saveSorts() {
    if (!this.data.product) {
      return
    }

    this.setData({ savingSort: true })
    try {
      const product = await updateAdminProductImagesSort(
        this.data.productId,
        this.data.product.images.map((image) => ({
          id: image.id,
          sort_order: Number(image.sort_order) || 0,
        })),
      )
      this.setData({
        product,
        savingSort: false,
      })
      wx.showToast({ title: "Sort saved", icon: "success" })
    } catch (_error) {
      this.setData({ savingSort: false })
      wx.showToast({ title: "Save failed", icon: "none" })
    }
  },

  async setCover(event) {
    const imageId = Number(event.currentTarget.dataset.imageId)
    try {
      const product = await setAdminProductCover(this.data.productId, imageId)
      this.setData({ product })
      wx.showToast({ title: "Cover updated", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "Update failed", icon: "none" })
    }
  },

  async removeImage(event) {
    const imageId = Number(event.currentTarget.dataset.imageId)
    try {
      const product = await deleteAdminProductImage(this.data.productId, imageId)
      this.setData({ product })
      wx.showToast({ title: "Deleted", icon: "success" })
    } catch (_error) {
      wx.showToast({ title: "Delete failed", icon: "none" })
    }
  },
})
