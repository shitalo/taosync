<template>
	<div class="taskCurrentEcharts" ref="taskCurrentEcharts"></div>
</template>

<script>
	import * as echarts from "echarts";
	import {
		parseSize
	} from "@/utils/utils";
	export default {
		name: 'DlEcharts',
		props: {
			taskCurrent: {
				type: Object,
				default: {}
			}
		},
		data() {
			return {
				chart: null,
				observer: null
			};
		},
		watch: {
			taskCurrent(newVal, oldVal) {
				if (JSON.stringify(oldVal) != JSON.stringify(newVal)) {
					this.$nextTick(() => {
						// 数据变化时只更新配置，不重新创建图表
						if (this.chart) {
							this.updateChartOption();
						} else {
							this.initChart();
						}
					});
				}
			},
			vuex_theme() {
				// 主题变化时重新初始化图表
				this.$nextTick(() => {
					if (this.chart) {
						this.chart.dispose();
						this.chart = null;
					}
					this.initChart();
				});
			}
		},
		created() {
			this.$nextTick(() => {
				this.initChart();
				this.initResizeObserver();
			});
		},
		beforeDestroy() {
			this.destroy();
		},
		methods: {
			destroy() {
				if (this.chart) {
					this.chart.dispose();
					this.chart = null;
				}
				if (this.observer) {
					this.observer.disconnect();
					this.observer = null;
				}
			},
			initResizeObserver() {
				const element = this.$refs.taskCurrentEcharts;
				this.observer = new ResizeObserver(entries => {
					for (const entry of entries) {
						this.resize();
					}
				});
				this.observer.observe(element);
			},
			getChartTheme() {
				// 根据当前主题返回 ECharts 主题名称
				return this.vuex_theme || 'dark';
			},
			getChartColors() {
				// 根据主题返回颜色配置
				const isDark = this.vuex_theme === 'dark';
				if (isDark) {
					// 深色主题颜色：等待中、进行中、成功、失败、其他
					return [
						'rgb(79, 89, 104)',    // 等待中 - 灰色
						'rgb(64, 158, 255)',   // 进行中 - 蓝色
						'rgb(103, 194, 58)',   // 成功 - 绿色
						'rgb(245, 108, 108)',  // 失败 - 红色
						'rgb(230, 162, 60)'    // 其他 - 橙色
					];
				} else {
					// 浅色主题颜色：使用更柔和的颜色
					return [
						'rgb(144, 147, 153)',  // 等待中 - 灰色
						'rgb(64, 158, 255)',   // 进行中 - 蓝色
						'rgb(103, 194, 58)',   // 成功 - 绿色
						'rgb(245, 108, 108)',  // 失败 - 红色
						'rgb(230, 162, 60)'    // 其他 - 橙色
					];
				}
			},
			getTextColor() {
				// 根据主题返回文本颜色
				const isDark = this.vuex_theme === 'dark';
				return isDark ? '#FFFFFF' : '#303133';
			},
			getChartOption() {
				// 准备数据
				const keyVal = {
					wait: '等待中',
					running: '进行中',
					success: '成功',
					fail: '失败',
					other: '其他'
				};
				let d0 = [];
				Object.entries(keyVal).forEach(([key, val]) => {
					d0.push({
						name: val,
						value: this.taskCurrent.num ? this.taskCurrent.num[key] : 0
					})
				})
				let d1 = [];
				Object.entries(keyVal).forEach(([key, val]) => {
					d1.push({
						name: val,
						value: this.taskCurrent.size ? this.taskCurrent.size[key] : 0
					})
				})
				
				// 获取当前主题配置
				const theme = this.getChartTheme();
				const colors = this.getChartColors();
				const textColor = this.getTextColor();
				
				// ECharts 配置
				return {
					color: colors,
					backgroundColor: 'transparent',
					textStyle: {
						color: textColor
					},
					tooltip: {
						trigger: 'item',
						backgroundColor: theme === 'dark' ? 'rgba(25, 27, 44, 0.95)' : 'rgba(255, 255, 255, 0.95)',
						borderColor: theme === 'dark' ? '#474856' : '#dcdfe6',
						textStyle: {
							color: textColor
						}
					},
					legend: {
						top: '5%',
						left: 'center',
						textStyle: {
							color: textColor
						}
					},
					series: [{
						name: '文件及目录数量',
						type: 'pie',
						radius: ['75%', '90%'],
						center: ['50%', '86%'],
						startAngle: 180,
						endAngle: 360,
						label: {
							color: textColor
						},
						labelLine: {
							lineStyle: {
								color: textColor
							}
						},
						data: d0
					}, {
						name: '文件大小',
						type: 'pie',
						radius: [0, '65%'],
						center: ['50%', '86%'],
						startAngle: 180,
						endAngle: 360,
						label: {
							position: 'inside',
							color: textColor
						},
						tooltip: {
							valueFormatter: (value) => parseSize(value)
						},
						data: d1
					}]
				};
			},
			initChart() {
				// 如果图表已存在，先销毁
				if (this.chart) {
					this.chart.dispose();
					this.chart = null;
				}
				
				// 获取当前主题
				const theme = this.getChartTheme();
				
				// 使用当前主题初始化图表
				this.chart = echarts.init(this.$refs.taskCurrentEcharts, theme);
				
				// 设置配置
				const option = this.getChartOption();
				this.chart.setOption(option);
			},
			updateChartOption() {
				// 更新图表配置（用于数据变化时）
				if (this.chart) {
					const option = this.getChartOption();
					this.chart.setOption(option);
				}
			},
			resize() {
				if (this.chart) {
					this.chart.resize();
				}
			}
		}
	}
</script>

<style lang="scss" scoped>
	.taskCurrentEcharts {}
</style>