const path = require('path')
module.exports = {
  configureWebpack: {
    resolve: {
      modules: [path.resolve(__dirname, '../src'), 'node_modules']
    }
  }
}



