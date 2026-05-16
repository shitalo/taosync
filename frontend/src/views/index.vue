<template>
	<div class="index-home-main">
		<div class="index-loading-card">
			<div class="index-loading-mark">
				<span>T</span>
			</div>
			<div class="index-loading-copy">
				<div class="index-loading-title">正在进入 TaoSync</div>
				<div class="index-loading-text">{{ err }}</div>
			</div>
			<div class="index-loading-bar">
				<span></span>
			</div>
		</div>
	</div>
</template>

<script>
	import Cookies from 'js-cookie';
	import {
		user
	} from '@/api/user';
	export default {
		name: 'Index',
		data() {
			return {
				err: '正在确认登录状态，请稍等'
			};
		},
		created() {
			this.init();
		},
		methods: {
			init() {
				try {
					if (!Cookies.get(this.vuex_cookieName)) {
						this.to('/login');
					} else {
						this.getInfo();
					}
				} catch (err) {
					this.err = err;
				}
			},
			getInfo() {
				user().then(res => {
					this.$setVuex('vuex_userInfo', res.data);
					this.to('/home');
				}).catch(err => {
					Cookies.remove(this.vuex_cookieName);
					this.to('/login');
				})
			},
			to(path) {
				this.$router.replace(path);
			}
		}
	}
</script>

<style scoped>
	.index-home-main {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		box-sizing: border-box;
		background:
			radial-gradient(circle at 18% 12%, var(--brand-soft, rgba(236, 139, 74, .18)), transparent 18rem),
			radial-gradient(circle at 82% 8%, rgba(109, 124, 255, .12), transparent 20rem),
			var(--bg-primary, #f7f3ea);
		color: var(--text-primary, #2f2a25);
		animation: indexPageFade .28s ease-out both;
	}

	.index-loading-card {
		width: min(420px, 100%);
		padding: 28px;
		border: 1px solid var(--border-color, rgba(132, 108, 88, .16));
		border-radius: 30px;
		background: color-mix(in srgb, var(--bg-secondary, #fffaf1) 90%, transparent);
		box-shadow: 0 28px 80px rgba(32, 27, 22, .14);
		backdrop-filter: blur(18px);
		animation: indexCardIn .38s cubic-bezier(.22, 1, .36, 1) both;
	}

	.index-loading-mark {
		width: 58px;
		height: 58px;
		border-radius: 22px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--brand, #c36a32), var(--accent, #e0a85e));
		color: #fffaf1;
		box-shadow: 0 16px 30px rgba(169, 79, 34, .22);
	}

	.index-loading-mark span {
		font-size: 30px;
		font-weight: 900;
		line-height: 1;
	}

	.index-loading-copy {
		margin-top: 20px;
	}

	.index-loading-title {
		font-size: 24px;
		font-weight: 900;
		letter-spacing: -.04em;
	}

	.index-loading-text {
		margin-top: 8px;
		color: var(--text-muted, #7b7167);
		font-size: 14px;
		font-weight: 800;
		line-height: 1.7;
	}

	.index-loading-bar {
		position: relative;
		height: 8px;
		margin-top: 24px;
		overflow: hidden;
		border-radius: 999px;
		background: var(--surface-soft, rgba(255, 255, 255, .68));
	}

	.index-loading-bar span {
		position: absolute;
		inset: 0 auto 0 0;
		width: 42%;
		border-radius: inherit;
		background: linear-gradient(90deg, var(--brand, #c36a32), var(--accent, #e0a85e));
		animation: indexLoadingBar 1.15s ease-in-out infinite;
	}

	@keyframes indexPageFade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes indexCardIn {
		from {
			opacity: 0;
			transform: translateY(10px) scale(.985);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	@keyframes indexLoadingBar {
		0% {
			transform: translateX(-110%);
		}
		55% {
			transform: translateX(85%);
		}
		100% {
			transform: translateX(240%);
		}
	}
</style>
