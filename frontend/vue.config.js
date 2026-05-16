module.exports = {
	productionSourceMap: false,
	configureWebpack: {
		optimization: {
			splitChunks: {
				chunks: 'all',
				cacheGroups: {
					elementUI: {
						name: 'chunk-element-ui',
						test: /[\\/]node_modules[\\/]element-ui[\\/]/,
						priority: 30
					},
					echarts: {
						name: 'chunk-echarts',
						test: /[\\/]node_modules[\\/]echarts[\\/]/,
						priority: 25
					},
					vendors: {
						name: 'chunk-vendors',
						test: /[\\/]node_modules[\\/]/,
						priority: 10
					}
				}
			}
		}
	},
	devServer: {
		host: '0.0.0.0',
		port: 80,
		open: true,
		proxy: {
			[process.env.VUE_APP_BASE_API]: {
				target: `http://127.0.0.1:8023/svr`,
				// target: `http://192.168.31.2:8023/svr`,
				changeOrigin: true,
				pathRewrite: {
					['^' + process.env.VUE_APP_BASE_API]: ''
				}
			}
		},
		disableHostCheck: true
	},
}
