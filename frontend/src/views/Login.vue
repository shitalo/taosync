<template>
	<div :class="['login', `theme-${vuex_theme}`]">
		<div class="login-orbit" aria-hidden="true">
			<span></span><span></span><span></span>
		</div>
		<div class="login-copy">
			<div class="copy-kicker">LOCAL SYNC STATION</div>
			<h1>把同步任务交给桃桃。</h1>
			<p>连接 OpenList 引擎，编排作业、通知与任务流水，在一个轻量控制台里完成日常同步。</p>
		</div>
		<button type="button" class="theme-toggle" @click="toggleTheme" :aria-label="vuex_theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'">
			<i :class="vuex_theme === 'dark' ? 'el-icon-sunrise' : 'el-icon-moon'"></i>
		</button>
		<div class="loginArea">
			<div class="logo">
				<div class="logo-badge">T</div>
				<div>
					<div class="logo-main">TaoSync</div>
					<div class="logo-sub">桃桃的自动同步工具</div>
				</div>
			</div>
			<div class="title">欢迎回来</div>
			<div class="subtitle">登录后管理你的同步作业</div>
			<el-form :model="loginForm" :rules="rules" ref="loginForm" label-width="0">
				<el-form-item prop="userName">
					<el-input class="input" placeholder="请输入用户名" prefix-icon="el-icon-user"
						v-model="loginForm.userName"></el-input>
				</el-form-item>
				<el-form-item prop="passwd">
					<el-input placeholder="请输入密码" prefix-icon="el-icon-lock" v-model="loginForm.passwd" show-password
						@keyup.enter.native="login"></el-input>
				</el-form-item>
			</el-form>
			<div class="foget" @click="fogetPwd">忘记密码？</div>
			<el-button class="login-button" size="medium" type="primary" :loading="loading"
				@click="login">登录</el-button>
		</div>
		<el-dialog :close-on-click-modal="false" :visible.sync="showPwd" :append-to-body="true" title="重置密码"
			:width="dialogWidth" custom-class="tao-dialog tao-form-dialog login-reset-dialog" :before-close="closePwd">
			<div>
				<el-form :model="pwdForm" :rules="pwdRules" ref="resetForm" label-width="80px">
					<el-form-item prop="userName" label="用户名">
						<el-input class="input" placeholder="请输入用户名" v-model="pwdForm.userName"></el-input>
					</el-form-item><el-form-item prop="key" label="加密秘钥">
						<el-input class="input" placeholder="在[程序同级]或[docker挂载]目录[data/secret.key]文件中复制全部"
							v-model="pwdForm.key"></el-input>
					</el-form-item>
					<el-form-item prop="passwd" label="新密码">
						<el-input placeholder="请输入新密码" v-model="pwdForm.passwd" show-password></el-input>
					</el-form-item>
					<el-form-item prop="passwd2" label="确认密码">
						<el-input placeholder="请确认新密码" v-model="pwdForm.passwd2" show-password></el-input>
					</el-form-item>
				</el-form>
			</div>
			<span slot="footer" class="dialog-footer">
				<el-button @click="closePwd">取 消</el-button>
				<el-button type="primary" @click="fogetSubmit" :loading="loading">确 定</el-button>
			</span>
		</el-dialog>
	</div>
</template>

<script>
	import Cookies from 'js-cookie';
	import {
		login,
		resetPwd
	} from "@/api/user";
	export default {
		name: 'Login',
		data() {
			var validatePass2 = (rule, value, callback) => {
				if (value == '' || value == null) {
					callback(new Error('请再次输入新密码'));
				} else if (value !== this.pwdForm.passwd) {
					callback(new Error('两次输入密码不一致!'));
				} else {
					callback();
				}
			};
			return {
				loginForm: {
					userName: null,
					passwd: null
				},
				loading: false,
				rules: {
					userName: [{
						required: true,
						message: '请输入用户名',
						trigger: 'blur'
					}],
					passwd: [{
						required: true,
						message: '请输入密码',
						trigger: 'blur'
					}]
				},
				pwdRules: {
					userName: [{
						required: true,
						message: '请输入用户名',
						trigger: 'blur'
					}],
					key: [{
						required: true,
						message: '请输入key',
						trigger: 'blur'
					}],
					passwd: [{
						required: true,
						message: '请输入新密码',
						trigger: 'blur'
					}],
					passwd2: [{
						validator: validatePass2,
						trigger: 'blur'
					}]
				},
				showPwd: false,
				pwdForm: {
					userName: null,
					key: null,
					passwd: null,
					passwd2: null
				}
			};
		},
		computed: {
			vuex_theme() {
				return this.$store.state.vuex_theme;
			},
			dialogWidth() {
				return window.innerWidth <= 768 ? '90%' : '560px';
			}
		},
		watch: {
			vuex_theme: {
				immediate: true,
				handler(theme) {
					document.body.className = theme;
				}
			}
		},
		methods: {
			login() {
				this.$refs.loginForm.validate((valid) => {
					if (valid) {
						Cookies.remove(this.vuex_cookieName);
						this.loading = true;
						login(this.loginForm).then(res => {
							this.$setVuex('vuex_userInfo', res.data);
							this.$router.replace('/home');
							this.loading = false;
						}).catch(err => {
							this.loading = false;

						})
					} else {
						return false;
					}
				});
			},
			toggleTheme() {
				// 切换主题
				const newTheme = this.vuex_theme === 'dark' ? 'light' : 'dark';
				this.$setVuex('vuex_theme', newTheme);
			},
			fogetPwd() {
				this.showPwd = true;
			},
			closePwd() {
				this.showPwd = false;
				this.pwdForm = {
					userName: null,
					key: null,
					passwd: null,
					passwd2: null
				}
			},
			fogetSubmit() {
				this.$refs.resetForm.validate((valid) => {
					if (valid) {
						this.loading = true;
						resetPwd(this.pwdForm).then(res => {
							this.closePwd();
							this.$message({
								message: '密码重置成功，请使用新密码登录',
								type: 'success'
							});
							this.loading = false;
						}).catch(err => {
							this.loading = false;
						})
					} else {
						return false;
					}
				});
			}
		}
	}
</script>
<style lang="scss" scoped>
	.login {
		--login-shell-start: color-mix(in srgb, var(--bg-primary) 88%, black);
		--login-shell-end: color-mix(in srgb, var(--bg-tertiary) 92%, black);
		--login-frame-border: var(--border-color);
		--login-orbit-fill: var(--brand-soft);
		--login-panel-bg: linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		--login-panel-shadow: var(--shadow-soft);
		--login-panel-border: var(--border-color);
		--login-panel-inner: var(--border-light);
		--login-toggle-bg: color-mix(in srgb, var(--surface-soft) 84%, transparent);
		--login-toggle-hover: color-mix(in srgb, var(--brand-soft) 92%, transparent);
		--login-copy-text: var(--text-secondary);
		--login-input-bg: color-mix(in srgb, var(--bg-input) 94%, var(--bg-secondary));
		--login-input-border: var(--border-light);
		--login-input-hover: color-mix(in srgb, var(--brand-soft) 38%, var(--border-light));
		--login-input-shadow: 0 0 0 4px color-mix(in srgb, var(--brand-soft) 68%, transparent);
		--login-dialog-ribbon: linear-gradient(180deg, var(--brand), var(--accent));
		position: fixed;
		inset: 0;
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(360px, 520px);
		align-items: center;
		gap: clamp(28px, 6vw, 90px);
		padding: clamp(22px, 5vw, 72px);
		box-sizing: border-box;
		background-image: none !important;
		background:
			radial-gradient(circle at 18% 20%, var(--brand-soft), transparent 32rem),
			radial-gradient(circle at 72% 78%, var(--login-orbit-fill), transparent 30rem),
			linear-gradient(135deg, var(--login-shell-start), var(--login-shell-end));
		overflow: hidden;

		&.theme-dark {
			--login-shell-start: #06090d;
			--login-shell-end: #10161d;
			--login-frame-border: rgba(231, 219, 195, .1);
			--login-orbit-fill: rgba(150, 179, 138, .09);
			--login-panel-bg:
				linear-gradient(180deg, rgba(248, 236, 214, .04), transparent 26%),
				linear-gradient(145deg, rgba(23, 28, 34, .96), rgba(17, 22, 27, .98));
			--login-panel-shadow: 0 28px 70px rgba(0, 0, 0, .42);
			--login-panel-border: rgba(231, 219, 195, .12);
			--login-panel-inner: rgba(231, 219, 195, .08);
			--login-toggle-bg: rgba(23, 28, 34, .78);
			--login-toggle-hover: rgba(219, 126, 62, .18);
			--login-copy-text: #c7b9a4;
			--login-input-bg: rgba(13, 18, 24, .88);
			--login-input-border: rgba(231, 219, 195, .14);
			--login-input-hover: rgba(240, 161, 91, .4);
			--login-input-shadow: 0 0 0 4px rgba(219, 126, 62, .12);
		}

		&.theme-light {
			--login-shell-start: #f3ebdf;
			--login-shell-end: #e7dbc9;
			--login-frame-border: rgba(91, 62, 35, .1);
			--login-orbit-fill: rgba(111, 141, 94, .18);
			--login-panel-bg:
				linear-gradient(180deg, rgba(255, 255, 255, .48), transparent 26%),
				linear-gradient(145deg, rgba(255, 250, 241, .96), rgba(245, 239, 229, .98));
			--login-panel-shadow: 0 24px 62px rgba(87, 63, 37, .14);
			--login-panel-border: rgba(91, 62, 35, .12);
			--login-panel-inner: rgba(91, 62, 35, .08);
			--login-toggle-bg: rgba(255, 250, 241, .84);
			--login-toggle-hover: rgba(199, 107, 46, .12);
			--login-copy-text: #655443;
			--login-input-bg: rgba(255, 252, 246, .94);
			--login-input-border: rgba(91, 62, 35, .14);
			--login-input-hover: rgba(169, 79, 34, .28);
			--login-input-shadow: 0 0 0 4px rgba(199, 107, 46, .1);
		}

		&::before {
			content: "";
			position: absolute;
			inset: clamp(14px, 2vw, 28px);
			border: 1px solid var(--login-frame-border);
			border-radius: clamp(26px, 4vw, 52px);
			pointer-events: none;
		}

		&::after {
			content: "";
			position: absolute;
			inset: 0;
			background:
				linear-gradient(90deg, rgba(5, 8, 12, .66) 0%, rgba(5, 8, 12, .38) 42%, rgba(5, 8, 12, .08) 64%, transparent 100%),
				radial-gradient(circle at 12% 18%, rgba(0, 0, 0, .34), transparent 32rem),
				radial-gradient(circle at 82% 90%, rgba(0, 0, 0, .2), transparent 24rem);
			opacity: 0;
			pointer-events: none;
			transition: opacity .24s ease;
		}

		&.theme-dark::after {
			opacity: 1;
		}

		.login-orbit {
			position: absolute;
			left: 8vw;
			bottom: 8vh;
			width: min(44vw, 560px);
			aspect-ratio: 1;
			border: 1px solid rgba(231, 219, 195, .08);
			border-radius: 50%;
			opacity: .64;
			filter: saturate(.9);
			pointer-events: none;

			span {
				position: absolute;
				border-radius: 50%;
				border: 1px solid var(--border-light);
			}

			span:nth-child(1) {
				inset: 14%;
			}

			span:nth-child(2) {
				inset: 30%;
				background: color-mix(in srgb, var(--brand-soft) 78%, transparent);
			}

			span:nth-child(3) {
				width: 14px;
				height: 14px;
				top: 18%;
				right: 23%;
				background: var(--brand);
				border: none;
				box-shadow: 0 0 0 10px var(--brand-soft);
			}
		}

		.login-copy {
			position: relative;
			z-index: 1;
			max-width: 620px;
			align-self: end;
			padding: 28px 34px 8vh 0;
			color: var(--text-primary);

			&::before {
				content: "";
				position: absolute;
				inset: -20px 90px 28px -28px;
				border-radius: 34px;
				background:
					linear-gradient(145deg, rgba(10, 14, 18, .7), rgba(10, 14, 18, .28)),
					radial-gradient(circle at top left, rgba(219, 126, 62, .08), transparent 40%);
				border: 1px solid rgba(231, 219, 195, .08);
				box-shadow: 0 22px 64px rgba(0, 0, 0, .24);
				backdrop-filter: blur(10px);
				opacity: 0;
				pointer-events: none;
				transition: opacity .24s ease;
			}
		}

		&.theme-dark .login-copy::before {
			opacity: 1;
		}

		.login-copy {
			.copy-kicker,
			h1,
			p {
				position: relative;
				z-index: 1;
			}

			.copy-kicker {
				font-size: 12px;
				font-weight: 900;
				letter-spacing: .28em;
				color: var(--brand);
			}

			h1 {
				margin: 18px 0 18px;
				font-size: clamp(42px, 7vw, 86px);
				line-height: .95;
				letter-spacing: -.06em;
				max-width: 9em;
			}

			p {
				margin: 0;
				max-width: 520px;
				font-size: clamp(16px, 1.5vw, 20px);
				line-height: 1.8;
				color: var(--login-copy-text);
			}
		}

		.theme-toggle {
			appearance: none;
			position: absolute;
			top: clamp(24px, 4vw, 44px);
			right: clamp(24px, 4vw, 44px);
			width: 46px;
			height: 46px;
			padding: 0;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 16px;
			border: 1px solid var(--login-panel-border);
			background: var(--login-toggle-bg);
			box-shadow: 0 10px 30px rgba(0, 0, 0, .12);
			font-size: 24px;
			cursor: pointer;
			color: var(--brand);
			transition: transform .24s ease, background .24s ease, box-shadow .24s ease;
			z-index: 2;
			transform: translateY(0) rotate(0deg);

			&:focus-visible {
				outline: none;
				box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-soft) 70%, transparent), 0 10px 30px rgba(0, 0, 0, .12);
			}

			&:active {
				transform: scale(.96);
			}

			i {
				pointer-events: none;
			}

			@media (hover: hover) and (pointer: fine) {
				&:hover {
					transform: translateY(-2px) rotate(-8deg);
					background: var(--login-toggle-hover);
				}
			}

			@media (hover: none) {
				&:hover {
					transform: translateY(0) rotate(0deg);
					background: var(--login-toggle-bg);
				}
			}
		}

		.loginArea {
			position: relative;
			z-index: 1;
			width: min(100%, 500px);
			box-sizing: border-box;
			padding: clamp(28px, 4vw, 52px);
			border: 1px solid var(--login-panel-border);
			border-radius: 34px;
			background: var(--login-panel-bg) !important;
			box-shadow: var(--login-panel-shadow);
			backdrop-filter: blur(14px);
			color: var(--text-primary);
			overflow: hidden;

			&::before {
				content: "";
				position: absolute;
				inset: 0;
				border-radius: inherit;
				background:
					radial-gradient(circle at top right, var(--brand-soft), transparent 32%),
					radial-gradient(circle at bottom left, color-mix(in srgb, var(--accent) 14%, transparent), transparent 30%);
				opacity: .92;
				pointer-events: none;
			}

			&::after {
				content: "";
				position: absolute;
				inset: 12px;
				border-radius: 24px;
				border: 1px solid var(--login-panel-inner);
				pointer-events: none;
			}

			.logo {
				display: flex;
				align-items: center;
				gap: 14px;
				margin-bottom: clamp(34px, 5vw, 54px);
			}

			.logo-badge {
				width: 54px;
				height: 54px;
				border-radius: 18px;
				display: flex;
				align-items: center;
				justify-content: center;
				background: linear-gradient(135deg, var(--brand), var(--accent));
				color: #fffaf1;
				font-size: 28px;
				font-weight: 900;
			}

			.logo-main {
				font-size: 24px;
				font-weight: 900;
				line-height: 1;
			}

			.logo-sub {
				margin-top: 7px;
				font-size: 12px;
				font-weight: 800;
				letter-spacing: .16em;
				color: var(--text-muted);
			}

			.title {
				font-size: clamp(28px, 4vw, 42px);
				font-weight: 900;
				line-height: 1;
				letter-spacing: -.04em;
			}

			.subtitle {
				margin: 12px 0 32px;
				color: var(--text-muted);
			}

			:deep(.el-input__inner) {
				height: 54px;
				font-size: 16px;
				border-radius: 18px;
				padding-left: 44px;
				background: var(--login-input-bg) !important;
				border-color: var(--login-input-border) !important;
				box-shadow: inset 0 1px 0 rgba(255, 255, 255, .02);
			}

			:deep(.el-input__inner:hover) {
				border-color: var(--login-input-hover) !important;
			}

			:deep(.el-input__inner:focus) {
				border-color: var(--brand) !important;
				box-shadow: var(--login-input-shadow) !important;
			}

			:deep(.el-input__inner::placeholder) {
				color: var(--text-placeholder);
			}

			:deep(.el-input__prefix) {
				left: 12px;
				color: var(--brand);
			}

			:deep(.el-input__suffix) {
				color: var(--text-muted);
			}

			:deep(.el-form-item) {
				margin-bottom: 22px;
			}

			.login-button {
				width: 100%;
				height: 52px;
				margin: 24px 0 8px;
				font-size: 17px;
			}

			.foget {
				text-align: right;
				cursor: pointer;
				font-weight: 800;
				color: var(--link-color);
				transition: color .18s ease, transform .18s ease;
			}

			.foget:hover {
				color: var(--brand);
				transform: translateX(-2px);
			}
		}

		:deep(.login-reset-dialog) {
			background:
				linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 56%, transparent), transparent 16rem),
				linear-gradient(145deg, var(--surface-raised), var(--bg-secondary)) !important;
			border-color: var(--login-panel-border) !important;
		}

		:deep(.login-reset-dialog .el-dialog__header::before) {
			background: var(--login-dialog-ribbon);
		}

		:deep(.login-reset-dialog .el-dialog__body) {
			background: transparent;
		}
	}

	@media (max-width: 900px) {
		.login {
			grid-template-columns: 1fr;
			place-items: center;
			padding: 70px 16px 22px;

			.login-copy,
			.login-orbit {
				display: none;
			}

			.loginArea {
				padding: 28px 22px;
				border-radius: 28px;
			}

			.theme-toggle {
				top: calc(env(safe-area-inset-top, 0px) + 24px);
				right: calc(env(safe-area-inset-right, 0px) + 24px);
			}
		}
	}
</style>
