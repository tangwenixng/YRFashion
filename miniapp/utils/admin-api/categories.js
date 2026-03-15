const { request } = require("../admin-http")

function fetchAdminCategories() {
  return request({
    url: "/admin/categories",
  }).then((response) => response.items || [])
}

module.exports = {
  fetchAdminCategories,
}
