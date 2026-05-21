<template>
	<div class="menuRefresh">
		&nbsp;
		<div class="refreshLabel" v-show="needShow > 1">{{refreshText}}</div>
		<el-switch v-model="refreshStatus" v-show="needShow > 1" @change="refreshChange"></el-switch>
		<i :class="`${isBusy ? 'el-icon-loading' : 'el-icon-refresh-right'} icon-btn`" @click="refreshData" v-show="needShow > 0"></i>
	</div>
</template>

	<script>
	export default {
		name: 'MenuRefresh',
		props: {
			loading: {
				type: Boolean,
				default: false
			},
			busy: {
				type: Boolean,
				default: false
			},
			autoRefresh: {
				type: Boolean,
				default: true
			},
			freshInterval: {
				type: Number,
				default: 3119
			},
			needShow: {
				type: Number,
				default: 2 // 0-不显示，1-只显示刷新按钮，2-显示全部
			},
			refreshText: {
				type: String,
				default: '自动刷新'
			},
			persistKey: {
				type: String,
				default: ''
			},
			feedbackMinDuration: {
				type: Number,
				default: 360
			}
		},
		computed: {
			remoteBusy() {
				return this.loading || this.busy;
			},
			isBusy() {
				return this.remoteBusy || this.instantBusy;
			}
		},
		data() {
			return {
				refreshStatus: true,
				timer: null,
				instantBusy: false,
				instantBusyTimer: null,
				instantBusyShownAt: 0
			};
		},
		watch: {
			remoteBusy(val) {
				if (val) {
					this.beginInstantBusy();
				} else {
					this.finishInstantBusy();
				}
			}
		},
		created() {
			this.refreshStatus = this.getInitialRefreshStatus();
			if (this.refreshStatus) {
				this.startRefresh();
			} else {
				this.$emit('getData');
			}
		},
		beforeDestroy() {
			this.destroy();
			this.clearInstantBusy();
		},
		methods: {
			getInitialRefreshStatus() {
				if (!this.persistKey || !window.localStorage) {
					return this.autoRefresh;
				}

				try {
					const savedStatus = window.localStorage.getItem(this.persistKey);
					if (savedStatus === '1' || savedStatus === 'true') {
						return true;
					}
					if (savedStatus === '0' || savedStatus === 'false') {
						return false;
					}
				} catch (e) {
					return this.autoRefresh;
				}

				return this.autoRefresh;
			},
			persistRefreshStatus(val) {
				if (!this.persistKey || !window.localStorage) {
					return;
				}

				try {
					window.localStorage.setItem(this.persistKey, val ? '1' : '0');
				} catch (e) {}
			},
			refreshChange(val) {
				this.refreshStatus = val;
				this.persistRefreshStatus(val);
				if (val) {
					this.startRefresh();
				} else {
					this.destroy();
				}
			},
			refreshData() {
				if (!this.isBusy) {
					this.beginInstantBusy();
					this.$emit('getData', {
						trigger: 'manual'
					});
					this.$nextTick(() => {
						if (!this.remoteBusy) {
							this.finishInstantBusy();
						}
					});
				}
			},
			startRefresh() {
				this.destroy();
				this.beginInstantBusy();
				this.$emit('getData');
				this.$nextTick(() => {
					if (!this.remoteBusy) {
						this.finishInstantBusy();
					}
				});
				this.timer = setInterval(() => {
					if (!this.remoteBusy) {
						this.beginInstantBusy();
						this.$emit('getData');
						this.$nextTick(() => {
							if (!this.remoteBusy) {
								this.finishInstantBusy();
							}
						});
					}
				}, this.freshInterval);
			},
			destroy() {
				if (this.timer) {
					clearInterval(this.timer);
					this.timer = null;
				}
			},
			clearInstantBusy() {
				if (this.instantBusyTimer) {
					clearTimeout(this.instantBusyTimer);
					this.instantBusyTimer = null;
				}
				this.instantBusy = false;
				this.instantBusyShownAt = 0;
			},
			beginInstantBusy() {
				if (this.instantBusy) {
					if (this.instantBusyTimer) {
						clearTimeout(this.instantBusyTimer);
						this.instantBusyTimer = null;
					}
					return;
				}
				this.instantBusy = true;
				this.instantBusyShownAt = Date.now();
			},
			finishInstantBusy() {
				if (!this.instantBusy) {
					return;
				}
				if (this.instantBusyTimer) {
					clearTimeout(this.instantBusyTimer);
					this.instantBusyTimer = null;
				}
				const shownDuration = Date.now() - this.instantBusyShownAt;
				const wait = Math.max(0, this.feedbackMinDuration - shownDuration);
				this.instantBusyTimer = setTimeout(() => {
					if (!this.remoteBusy) {
						this.instantBusy = false;
						this.instantBusyShownAt = 0;
					}
					this.instantBusyTimer = null;
				}, wait);
			}
		}
	}
</script>

<style lang="scss" scoped>
	.menuRefresh {
		display: flex;
		align-items: center;

		.refreshLabel {
			font-size: 18px;
			margin-right: 8px;
		}

		.icon-btn {
			font-size: 28px;
			margin-left: 24px;
		}

		.el-icon-refresh-right {
			cursor: pointer;
			color: var(--link-color);
			transition: color 0.2s ease;
			
			&:hover {
				color: var(--link-hover-color);
			}
		}

		.el-icon-loading {
			cursor: not-allowed;
		}
	}
</style>
