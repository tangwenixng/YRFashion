const { API_BASE_URL } = require("./config")

const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api$/, "")

function normalizeMediaUrl(url) {
  if (!url || typeof url !== "string") {
    return ""
  }

  if (/^https?:\/\//.test(url)) {
    return url
  }

  if (url.startsWith("//")) {
    return `https:${url}`
  }

  if (url.startsWith("/")) {
    return `${MEDIA_BASE_URL}${url}`
  }

  return `${MEDIA_BASE_URL}/${url}`
}

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
    cover_image_url: normalizeMediaUrl(product.cover_image_url),
    images,
  })
}

function normalizeHome(home) {
  if (!home) {
    return home
  }

  return Object.assign({}, home, {
    homepage_banner_urls: Array.isArray(home.homepage_banner_urls)
      ? home.homepage_banner_urls.map(normalizeMediaUrl)
      : [],
    featured_products: Array.isArray(home.featured_products)
      ? home.featured_products.map(normalizeProduct)
      : [],
  })
}

module.exports = {
  normalizeHome,
  normalizeMediaUrl,
  normalizeProduct,
}
