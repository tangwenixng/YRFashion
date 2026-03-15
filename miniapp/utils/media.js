const { API_BASE_URL } = require("./config")

const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api$/, "")
const MINIAPP_COPY_REPLACEMENTS = [
  [/商品列表/g, "穿搭展示"],
  [/浏览全部商品/g, "查看穿搭"],
  [/主推商品/g, "本周推荐"],
  [/商品详情/g, "穿搭详情"],
  [/商品/g, "穿搭"],
  [/时装馆/g, "穿搭馆"],
]

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

function sanitizeAuditCopy(value) {
  if (!value || typeof value !== "string") {
    return value
  }

  return MINIAPP_COPY_REPLACEMENTS.reduce(
    (result, [pattern, replacement]) => result.replace(pattern, replacement),
    value,
  )
}

function normalizeHome(home) {
  if (!home) {
    return home
  }

  return Object.assign({}, home, {
    shop_name: sanitizeAuditCopy(home.shop_name),
    shop_intro: sanitizeAuditCopy(home.shop_intro),
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
