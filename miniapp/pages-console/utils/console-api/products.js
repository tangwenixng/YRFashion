const { request, uploadFile } = require("../console-http")
const { normalizeMediaUrl } = require("../../../utils/media")

function normalizeProduct(product) {
  if (!product) {
    return product
  }

  const images = Array.isArray(product.images)
    ? product.images.map((image) =>
        Object.assign({}, image, {
          image_url: normalizeMediaUrl(image.image_url),
        }),
      )
    : []

  return Object.assign({}, product, {
    images,
    cover_image_url: images.find((image) => image.is_cover)?.image_url || images[0]?.image_url || "",
  })
}

function fetchConsoleProducts() {
  return request({
    url: "/admin/products",
  }).then((response) => (response.items || []).map(normalizeProduct))
}

function fetchConsoleProduct(productId) {
  return request({
    url: `/admin/products/${productId}`,
  }).then(normalizeProduct)
}

function createConsoleProduct(payload) {
  return request({
    url: "/admin/products",
    method: "POST",
    data: payload,
  }).then(normalizeProduct)
}

function updateConsoleProduct(productId, payload) {
  return request({
    url: `/admin/products/${productId}`,
    method: "PUT",
    data: payload,
  }).then(normalizeProduct)
}

function updateConsoleProductSort(productId, sortOrder) {
  return request({
    url: `/admin/products/${productId}/sort`,
    method: "PUT",
    data: {
      sort_order: sortOrder,
    },
  }).then(normalizeProduct)
}

function uploadConsoleProductImage(productId, filePath, sortOrder, isCover) {
  return uploadFile({
    url: `/admin/products/${productId}/images`,
    filePath,
    formData: {
      sort_order: String(sortOrder || 0),
      is_cover: String(Boolean(isCover)),
    },
  }).then((image) =>
    Object.assign({}, image, {
      image_url: normalizeMediaUrl(image.image_url),
    }),
  )
}

function updateConsoleProductImagesSort(productId, items) {
  return request({
    url: `/admin/products/${productId}/images/sort`,
    method: "PUT",
    data: {
      items,
    },
  }).then(normalizeProduct)
}

function setConsoleProductCover(productId, imageId) {
  return request({
    url: `/admin/products/${productId}/images/${imageId}/cover`,
    method: "POST",
  }).then(normalizeProduct)
}

function deleteConsoleProductImage(productId, imageId) {
  return request({
    url: `/admin/products/${productId}/images/${imageId}`,
    method: "DELETE",
  }).then(normalizeProduct)
}

module.exports = {
  createConsoleProduct,
  deleteConsoleProductImage,
  fetchConsoleProduct,
  fetchConsoleProducts,
  normalizeConsoleProduct: normalizeProduct,
  setConsoleProductCover,
  updateConsoleProduct,
  updateConsoleProductImagesSort,
  updateConsoleProductSort,
  uploadConsoleProductImage,
}
