const { request } = require("../console-http")

function fetchConsoleCategories() {
  return request({
    url: "/admin/categories",
  }).then((response) => response.items || [])
}

module.exports = {
  fetchConsoleCategories,
}
