<template>
	<div class="user">
		<div class="user-info">
			<template v-if="vuex_userInfo">
				<div class="item">
					<div class="label">用户名</div>
					<div class="value">{{vuex_userInfo.userName}}</div>
				</div>
				<div class="item">
					<div class="label">创建时间</div>
					<div class="value">{{vuex_userInfo.createTime | timeStampFilter}}</div>
				</div>
				<el-form :model="resetForm" :rules="rules" ref="resetForm" label-width="0">
					<el-form-item prop="oldPasswd">
						<el-input class="input" placeholder="请输入旧密码" show-password
							v-model="resetForm.oldPasswd"></el-input>
					</el-form-item>
					<el-form-item prop="passwd">
						<el-input placeholder="请输入新密码" show-password v-model="resetForm.passwd"
							show-password></el-input>
					</el-form-item>
					<el-form-item prop="passwd2">
						<el-input placeholder="确认新密码" show-password v-model="resetForm.passwd2" show-password
							@keyup.enter.native="resetPasswd"></el-input>
					</el-form-item>
				</el-form>
				<el-button type="primary" :loading="loading" @click="resetPasswd">修改密码</el-button>
			</template>
		</div>
		<div class="setting-bottom">
			<div class="setting-bottom-item">TaoSync 版本：__version_placeholder__</div>
			<div class="setting-bottom-item"><a href="https://github.com/dr34m-cn/taosync" target="_blank">项目地址（GitHub）</a></div>
			<div class="setting-bottom-item"><a href="https://github.com/dr34m-cn/taosync/issues" target="_blank">问题反馈（GitHub Issues）</a></div>
		</div>
	</div>
</template>

<script>
	import {
		editPwd
	} from "@/api/user";
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	export default {
		name: 'User',
		data() {
			var validatePass2 = (rule, value, callback) => {
				if (value == '' || value == null) {
					callback(new Error('请再次输入新密码'));
				} else if (value !== this.resetForm.passwd) {
					callback(new Error('两次输入密码不一致!'));
				} else {
					callback();
				}
			};
			return {
				resetForm: {
					oldPasswd: null,
					passwd: null,
					passwd2: null
				},
				loading: false,
				loadingController: null,
				rules: {
					oldPasswd: [{
						required: true,
						message: '请输入旧密码',
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
				}
			};
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.loading = true; },
				hide: () => { this.loading = false; },
				delay: 120,
				minDuration: 180
			});
		},
		beforeDestroy() {
			if (this.loadingController) {
				this.loadingController.dispose();
			}
		},
		methods: {
			resetPasswd() {
				this.$refs.resetForm.validate((valid) => {
					if (valid) {
						const loadToken = this.loadingController ? this.loadingController.start() : 0;
						editPwd(this.resetForm).then(res => {
							this.$message({
								message: res.msg,
								type: 'success'
							});
							this.$refs.resetForm.resetFields();
							if (this.loadingController) {
								this.loadingController.finish(loadToken);
							} else {
								this.loading = false;
							}
						}).catch(err => {
							if (this.loadingController) {
								this.loadingController.finish(loadToken);
							} else {
								this.loading = false;
							}
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
	.user {
		min-height: 100%;
		padding: clamp(16px, 3vw, 36px);
		box-sizing: border-box;
		display: grid;
		grid-template-columns: minmax(280px, 460px) minmax(260px, 1fr);
		gap: clamp(18px, 4vw, 52px);
		align-items: start;
		font-size: 16px;

		.user-info {
			width: 100%;
			box-sizing: border-box;
			padding: clamp(24px, 4vw, 40px);
			background: linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
			border: 1px solid var(--border-color);
			border-radius: 32px;
			box-shadow: var(--shadow-card);

			.el-input,
			.el-button {
				width: 100%;
			}

			.item {
				display: grid;
				grid-template-columns: 82px 1fr;
				gap: 16px;
				align-items: center;
				margin-bottom: 18px;
				padding-bottom: 18px;
				border-bottom: 1px solid var(--border-color);

				.label {
					color: var(--text-muted);
					font-size: 13px;
					font-weight: 900;
					letter-spacing: .12em;
				}

				.value {
					color: var(--text-primary);
					font-size: 18px;
					font-weight: 900;
					word-break: break-all;
				}
			}

			:deep(.el-input__inner) {
				height: 48px;
			}

			.el-button {
				height: 46px;
				margin-top: 4px;
			}
		}

		.setting-bottom {
			position: relative;
			align-self: stretch;
			display: flex;
			flex-direction: column;
			justify-content: flex-end;
			gap: 14px;
			min-height: 280px;
			padding: clamp(22px, 4vw, 40px);
			box-sizing: border-box;
			border: 1px solid var(--border-color);
			border-radius: 32px;
			background:
				radial-gradient(circle at 90% 18%, var(--brand-soft), transparent 17rem),
				var(--surface-soft);
			overflow: hidden;

			&::before {
				content: "SYSTEM";
				position: absolute;
				top: 22px;
				left: 28px;
				font-size: clamp(42px, 9vw, 112px);
				font-weight: 900;
				letter-spacing: -.08em;
				line-height: .8;
				color: var(--text-primary);
				opacity: .06;
				pointer-events: none;
			}

			.setting-bottom-item {
				position: relative;
				z-index: 1;
				color: var(--text-secondary);
				font-weight: 800;

				a {
					color: var(--link-color);
					text-decoration: none;
				}

				a:hover {
					color: var(--link-hover-color);
					text-decoration: underline;
				}
			}
		}
	}

	@media (max-width: 860px) {
		.user {
			grid-template-columns: 1fr;
			gap: 16px;

			.setting-bottom {
				min-height: 190px;
			}
		}
	}

	@media (max-width: 480px) {
		.user {
			padding: 12px;

			.user-info,
			.setting-bottom {
				border-radius: 24px;
				padding: 20px;
			}

			.user-info .item {
				grid-template-columns: 1fr;
				gap: 6px;
			}
		}
	}
</style>
