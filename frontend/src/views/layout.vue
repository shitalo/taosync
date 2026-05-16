<template>
	<div class="layout">
		<div class="lay-left" v-show="!isMobile">
			<div class="left-top-logo">
				<div :class="'left-top-logo-in ' + (isCollapse ? 'isCollapse' : '')" @click="toIndex">
					<div class="logo-mark">T</div>
					<div class="logo-copy" v-if="!isCollapse">
						<div class="logo-title">TaoSync</div>
						<div class="logo-subtitle">自动同步台</div>
					</div>
				</div>
			</div>
			<el-menu :default-active="vuex_letfIndex" :router="true" :collapse="isCollapse" class="lay-left-menu">
				<el-menu-item :index="item.index" v-for="item in menuList">
					<i :class="`el-icon-${item.icon}`"></i>
					<span slot="title">{{item.title}}</span>
				</el-menu-item>
			</el-menu>
		</div>
		
		<!-- 移动端抽屉菜单 -->
		<el-drawer
			:visible.sync="drawerVisible"
			:with-header="false"
			:size="isMobile ? '82vw' : 280"
			:modal-append-to-body="true"
			:append-to-body="true"
			direction="ltr">
			<div class="mobile-menu">
				<div class="mobile-menu-logo" @click="toIndex">
					<div class="mobile-logo-mark">T</div>
					<div class="mobile-logo-copy">
						<div class="mobile-logo-title">TaoSync</div>
						<div class="mobile-logo-text">自动同步控制台</div>
					</div>
				</div>
				<div class="mobile-menu-caption">导航菜单</div>
				<el-menu 
					:default-active="vuex_letfIndex" 
					:router="true" 
					@select="handleMenuSelect">
					<el-menu-item :index="item.index" v-for="item in menuList" :key="item.index">
						<i :class="`el-icon-${item.icon}`"></i>
						<span slot="title">{{item.title}}</span>
					</el-menu-item>
				</el-menu>
				<div class="mobile-menu-foot">
					<div class="mobile-menu-foot-label">当前页面</div>
					<div class="mobile-menu-foot-value">{{currentTitle}}</div>
				</div>
			</div>
		</el-drawer>
		<div class="lay-right">
			<div class="lay-right-top">
				<div class="top-left">
					<div class="top-icon can-click" @click="toggleMenu">
						<i :class="isMobile ? 'el-icon-menu' : (isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold')"></i>
					</div>
					<div class="page-heading">
						<div class="page-eyebrow">SYNC CONTROL</div>
						<div class="page-title">{{currentTitle}}</div>
					</div>
				</div>
				<div class="top-right">
					<div class="btn-item can-click" @click="toggleTheme">
						<div class="theme-icon">
							<i :class="vuex_theme === 'dark' ? 'el-icon-sunrise' : 'el-icon-moon'"></i>
						</div>
					</div>
					<div class="btn-item can-click" @click="logout()">
						<div class="top-icon">
							<i class="el-icon-switch-button"></i>
						</div>
						<span>登出</span>
					</div>
				</div>
			</div>
			<div class="lay-right-bottom" v-loading="vuex_loading"
				:style="contentStyle">
				<router-view />
			</div>
			<div class="mobile-bottom-nav" v-if="isMobile">
				<button v-for="item in menuList" :key="item.index" type="button"
					:class="['mobile-nav-item', item.index === vuex_letfIndex ? 'is-active' : '']"
					@click="goMenu(item.index)">
					<i :class="`el-icon-${item.icon}`"></i>
					<span>{{item.title.replace('管理', '').replace('配置', '')}}</span>
				</button>
			</div>
		</div>

	</div>
</template>
<script>
	import {
		logout
	} from "@/api/user";
	export default {
		data() {
			return {
				isCollapse: false,
				isMobile: false,
				drawerVisible: false,
				menuList: [{
						index: '/home',
						title: '作业管理',
						icon: 'data-analysis'
					},{ 
						index: '/engine',
						title: '引擎管理',
						icon: 'receiving'
					},{ 
						index: '/notify',
						title: '通知配置',
						icon: 'bell'
					},
					{
						index: '/setting',
						title: '系统设置',
						icon: 'setting'
					}]
			};
		},
		mounted() {
			this.checkMobile();
			window.addEventListener('resize', this.checkMobile);
		},
		beforeDestroy() {
			window.removeEventListener('resize', this.checkMobile);
		},
		computed: {
			contentStyle() {
				return this.isMobile ? { width: '100vw' } : { width: `calc(100vw - ${this.isCollapse ? 84 : 180}px)` };
			},
			currentTitle() {
				const active = this.menuList.find(item => item.index === this.vuex_letfIndex);
				return active ? active.title : '控制台';
			},
			themeValue: {
				get() {
					return this.vuex_theme === 'dark';
				},
				set(val) {
					// 这个setter实际上不会被直接调用，因为我们使用@change事件处理
				}
			}
		},
		created() {
			this.init();
		},
		watch: {},
		methods: {
			init() {
				this.restoreMenuCollapse();
			},
			restoreMenuCollapse() {
				const saved = localStorage.getItem('taosync_menu_collapsed');
				if (saved !== null) {
					this.isCollapse = saved === '1';
				}
			},
			saveMenuCollapse() {
				localStorage.setItem('taosync_menu_collapsed', this.isCollapse ? '1' : '0');
			},
			checkMobile() {
				this.isMobile = window.innerWidth <= 768;
				if (this.isMobile) {
					this.isCollapse = true;
				} else {
					this.restoreMenuCollapse();
				}
			},
			toggleMenu() {
				if (this.isMobile) {
					this.drawerVisible = !this.drawerVisible;
				} else {
					this.isCollapse = !this.isCollapse;
					this.saveMenuCollapse();
				}
			},
			goMenu(index) {
				if (this.$route.path !== index) {
					this.$router.push(index);
				}
				this.drawerVisible = false;
			},
			handleMenuSelect() {
				// Close drawer after selecting a menu item on mobile
				if (this.isMobile) {
					this.drawerVisible = false;
				}
			},
		logout() {
			logout().then(res => {
				this.$router.push('/login');
				this.$setVuex('vuex_userInfo', null);
			})
		},
			toIndex() {
			if (this.$route.path !== '/home') {
				this.$router.replace('/home');
			}
			if (this.isMobile) {
				this.drawerVisible = false;
			}
		},
		changeTheme(value) {
			// 切换主题：true为深色，false为浅色
			const newTheme = value ? 'dark' : 'light';
			this.$setVuex('vuex_theme', newTheme);
			// 更新body类名
			document.body.className = newTheme;
		},
		toggleTheme() {
			// 点击图标切换主题
			const newTheme = this.vuex_theme === 'dark' ? 'light' : 'dark';
			this.$setVuex('vuex_theme', newTheme);
			// 更新body类名
			document.body.className = newTheme;
		}
		}
	}
</script>
<style lang="scss" scoped>
	.layout {
		position: fixed;
		inset: 0;
		display: flex;
		background:
			radial-gradient(circle at 80% 10%, var(--brand-soft), transparent 28rem),
			var(--bg-primary);
		color: var(--text-primary);

		.lay-left {
			width: auto;
			background: linear-gradient(180deg, var(--menu-bg), var(--bg-primary));
			border-right: 1px solid var(--border-color);
			box-shadow: 10px 0 34px rgba(0, 0, 0, .14);
			z-index: 3;

			.left-top-logo {
				height: 82px;
				display: flex;
				align-items: center;
				justify-content: center;
				padding: 0 12px;

				.left-top-logo-in {
					width: 156px;
					height: 54px;
					box-sizing: border-box;
					cursor: pointer;
					display: flex;
					align-items: center;
					gap: 10px;
					padding: 8px;
					border: 1px solid var(--border-light);
					border-radius: 20px;
					background: var(--surface-soft);
					transition: all .24s ease;
				}

				.logo-mark {
					width: 36px;
					height: 36px;
					border-radius: 13px;
					display: flex;
					align-items: center;
					justify-content: center;
					flex-shrink: 0;
					background: linear-gradient(135deg, var(--brand), var(--accent));
					color: #fffaf1;
					font-size: 21px;
					font-weight: 900;
				}

				.logo-title {
					font-size: 17px;
					font-weight: 900;
					line-height: 1;
				}

				.logo-subtitle {
					margin-top: 4px;
					font-size: 11px;
					color: var(--text-muted);
					letter-spacing: .16em;
				}

				.isCollapse {
					width: 54px;
					justify-content: center;
				}
			}

			.lay-left-menu {
				height: calc(100% - 82px);
				background: transparent;
			}

			.lay-left-menu:not(.el-menu--collapse) {
				width: 180px;
			}
		}

		.lay-right {
			width: 100%;
			height: 100%;
			min-width: 0;

			.lay-right-top {
				height: 72px;
				display: flex;
				justify-content: space-between;
				align-items: center;
				padding: 0 18px 0 8px;
				box-sizing: border-box;
				border-bottom: 1px solid var(--border-color);
				background: color-mix(in srgb, var(--bg-secondary) 78%, transparent);
				backdrop-filter: blur(16px);

				.top-icon {
					height: 46px;
					width: 46px;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 22px;
					border-radius: 16px;
				}

				.can-click {
					cursor: pointer;
					transition: background .18s ease, color .18s ease, transform .18s ease;
				}

				.can-click:hover {
					background-color: var(--brand-soft);
					color: var(--brand-strong);
					transform: translateY(-1px);
				}

				.top-left,
				.top-right,
				.btn-item {
					display: flex;
					align-items: center;
				}

				.page-heading {
					margin-left: 6px;
				}

				.page-eyebrow {
					font-size: 10px;
					font-weight: 900;
					letter-spacing: .22em;
					color: var(--brand);
				}

				.page-title {
					margin-top: 3px;
					font-size: 21px;
					font-weight: 900;
				}

				.top-right {
					gap: 10px;

					.btn-item {
						gap: 4px;
						padding: 0 12px;
						height: 42px;
						border: 1px solid var(--border-color);
						border-radius: 999px;
						background: var(--surface-soft);
						font-weight: 800;
					}
				}
			}

			.lay-right-bottom {
				height: calc(100% - 72px);
				overflow-y: auto;
				transition: width .3s ease-in-out;
			}
		}

		.mobile-menu {
			height: 100%;
			background: linear-gradient(180deg, var(--menu-bg), var(--bg-primary));

			.mobile-menu-logo {
				padding: 26px 20px;
				display: flex;
				align-items: center;
				justify-content: center;
				border-bottom: 1px solid var(--border-color);
				cursor: pointer;

				.mobile-logo-in {
					width: 142px;
					height: auto;
					display: block;
					object-fit: contain;
				}
			}

			::v-deep .el-menu {
				border-right: none;
				background: transparent;
			}
		}
	}

	@media (max-width: 768px) {
		.layout {
			.lay-right {
				.lay-right-top {
					height: 64px;
					padding-right: 10px;

					.page-heading {
						margin-left: 2px;
					}

					.page-eyebrow {
						display: none;
					}

					.page-title {
						font-size: 18px;
					}

					.top-right {
						gap: 6px;

						.btn-item {
							width: 42px;
							padding: 0;
							justify-content: center;

							span {
								display: none;
							}
						}
					}
				}

				.lay-right-bottom {
					height: calc(100% - 64px);
				}
			}
		}
	}

	/* mobile-shell-polish */
	.layout {
		.lay-right {
			position: relative;
		}
	}

	@media (max-width: 768px) {
		.layout {
			background: var(--bg-primary);

			.lay-right {
				.lay-right-top {
					height: calc(64px + env(safe-area-inset-top));
					padding: env(safe-area-inset-top) 10px 0 10px;
					border-bottom: 1px solid var(--border-color);
					background:
						radial-gradient(circle at 8% 0%, var(--brand-soft), transparent 12rem),
						color-mix(in srgb, var(--bg-secondary) 90%, transparent);
					box-shadow: 0 10px 28px rgba(0, 0, 0, .08);
					backdrop-filter: blur(18px);

					.top-left {
						min-width: 0;
						flex: 1;
					}

					.top-icon {
						width: 42px;
						height: 42px;
						font-size: 20px;
						border: 1px solid var(--border-color);
						background: var(--surface-soft);
						box-shadow: 0 8px 18px rgba(0, 0, 0, .07);
					}

					.page-heading {
						min-width: 0;
						margin-left: 10px;
					}

					.page-title {
						max-width: 42vw;
						overflow: hidden;
						text-overflow: ellipsis;
						white-space: nowrap;
						font-size: 20px;
						letter-spacing: -.04em;
					}

					.top-right {
						gap: 8px;
						flex-shrink: 0;

						.btn-item {
							width: 42px;
							height: 42px;
							padding: 0;
							border-radius: 16px;
							border: 1px solid var(--border-color);
							background: var(--surface-soft);
							box-shadow: 0 8px 18px rgba(0, 0, 0, .07);
						}

						.btn-item .top-icon {
							border: none;
							background: transparent;
							box-shadow: none;
						}
					}
				}

				.lay-right-bottom {
					height: calc(100% - 64px - env(safe-area-inset-top));
					padding-bottom: calc(86px + env(safe-area-inset-bottom));
					box-sizing: border-box;
					overflow-y: auto;
					overflow-x: hidden;
				}
			}
		}

		.mobile-bottom-nav {
			position: absolute;
			left: 12px;
			right: 12px;
			bottom: calc(10px + env(safe-area-inset-bottom));
			z-index: 12;
			display: grid;
			grid-template-columns: repeat(4, minmax(0, 1fr));
			gap: 6px;
			padding: 8px;
			border: 1px solid var(--border-color);
			border-radius: 26px;
			background: color-mix(in srgb, var(--bg-secondary) 92%, transparent);
			box-shadow: 0 18px 46px rgba(0, 0, 0, .22);
			backdrop-filter: blur(18px);
		}

		.mobile-nav-item {
			appearance: none;
			border: none;
			min-width: 0;
			height: 52px;
			border-radius: 19px;
			background: transparent;
			color: var(--text-muted);
			font-family: inherit;
			font-weight: 900;
			font-size: 11px;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			gap: 4px;
			-webkit-tap-highlight-color: transparent;
			transition: background .18s ease, color .18s ease, transform .18s ease;
		}

		.mobile-nav-item i {
			font-size: 19px;
		}

		.mobile-nav-item span {
			max-width: 100%;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		.mobile-nav-item.is-active {
			background: linear-gradient(135deg, var(--brand), var(--brand-strong));
			color: #fffaf1;
			box-shadow: 0 10px 22px rgba(169, 79, 34, .2);
		}

		.mobile-nav-item:active {
			transform: scale(.96);
		}

		.mobile-menu {
			display: flex;
			flex-direction: column;
			height: 100%;
			padding: max(18px, env(safe-area-inset-top)) 14px max(14px, env(safe-area-inset-bottom));
			box-sizing: border-box;
			background:
				radial-gradient(circle at 20% 0%, var(--brand-soft), transparent 14rem),
				linear-gradient(180deg, var(--menu-bg), var(--bg-primary));
		}

		.mobile-menu .mobile-menu-logo {
			padding: 12px;
			justify-content: flex-start;
			gap: 12px;
			min-height: auto;
			border: 1px solid var(--border-color);
			border-radius: 24px;
			background: var(--surface-soft);
		}

		.mobile-logo-mark {
			width: 42px;
			height: 42px;
			border-radius: 16px;
			display: flex;
			align-items: center;
			justify-content: center;
			background: linear-gradient(135deg, var(--brand), var(--accent));
			color: #fffaf1;
			font-size: 23px;
			font-weight: 900;
			flex: 0 0 auto;
		}

		.mobile-logo-title {
			font-size: 20px;
			font-weight: 900;
			line-height: 1;
			color: var(--text-primary);
		}

		.mobile-logo-text {
			margin-top: 6px;
			font-size: 12px;
			font-weight: 800;
			letter-spacing: .08em;
			color: var(--text-muted);
		}

		.mobile-menu-caption {
			margin: 20px 10px 8px;
			font-size: 11px;
			font-weight: 900;
			letter-spacing: .2em;
			color: var(--brand);
		}

		.mobile-menu ::v-deep .el-menu {
			background: transparent;
		}

		.mobile-menu ::v-deep .el-menu-item {
			height: 52px;
			line-height: 52px;
			margin: 8px 0;
			border-radius: 18px;
			font-size: 15px;
			font-weight: 900;
		}

		.mobile-menu ::v-deep .el-menu-item i {
			font-size: 20px;
			margin-right: 10px;
		}

		.mobile-menu-foot {
			margin-top: auto;
			padding: 14px;
			border: 1px solid var(--border-color);
			border-radius: 22px;
			background: var(--surface-soft);
		}

		.mobile-menu-foot-label {
			font-size: 11px;
			font-weight: 900;
			letter-spacing: .16em;
			color: var(--text-muted);
		}

		.mobile-menu-foot-value {
			margin-top: 6px;
			font-size: 18px;
			font-weight: 900;
			color: var(--text-primary);
		}
	}

	@media (max-width: 380px) {
		.layout .lay-right .lay-right-top .page-title {
			max-width: 34vw;
			font-size: 18px;
		}

		.mobile-bottom-nav {
			left: 8px;
			right: 8px;
			bottom: calc(8px + env(safe-area-inset-bottom));
			padding: 6px;
			border-radius: 22px;
		}

		.mobile-nav-item {
			height: 48px;
			font-size: 10px;
		}
	}
</style>



