<template>
	<div class="taskCurrentDetail">
		<div class="top-box">
			<el-button class="tao-back-button" type="primary" icon="el-icon-back" @click="goback" size="small">返回</el-button>
			<div class="top-box-title">实时任务详情</div>
			<div class="top-box-spacer"></div>
		</div>
		<taskCurrent
			v-if="!finished"
			class="current-detail-box"
			:jobId="jobId"
			:finishOnEmpty="true"
			@currentFinished="handleCurrentFinished">
		</taskCurrent>
		<div v-else class="task-finished-state">
			<div class="finish-icon"><i class="el-icon-finished"></i></div>
			<div class="finish-copy">
				<div class="finish-title">任务已结束</div>
				<div class="finish-desc">实时进度已停止刷新，可以回到任务列表，或查看本次任务的明细记录。</div>
			</div>
			<div class="finish-actions">
				<el-button type="primary" icon="el-icon-document" @click="toTaskDetail" size="small">查看记录详情</el-button>
				<el-button icon="el-icon-back" @click="goback" size="small">返回任务列表</el-button>
			</div>
		</div>
	</div>
</template>

<script>
	import taskCurrent from './components/taskCurrent';
	export default {
		name: 'TaskCurrentDetail',
		components: {
			taskCurrent
		},
		data() {
			return {
				jobId: null,
				taskId: null,
				finished: false
			};
		},
		created() {
			if (this.$route.query.hasOwnProperty('jobId')) {
				this.jobId = this.$route.query.jobId;
			}
			if (this.$route.query.hasOwnProperty('taskId')) {
				this.taskId = this.$route.query.taskId;
			}
		},
		methods: {
			handleCurrentFinished() {
				this.finished = true;
			},
			toTaskDetail() {
				if (!this.taskId) {
					this.goback();
					return;
				}
				this.$router.replace({
					path: '/home/task/detail',
					query: {
						taskId: this.taskId
					}
				})
			},
			goback() {
				this.$router.go(-1);
			}
		}
	}
</script>

<style lang="scss" scoped>
	.taskCurrentDetail {
		width: 100%;
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		padding: 16px;
		box-sizing: border-box;
		overflow: hidden;

		.top-box {
			display: flex;
			align-items: center;
			justify-content: space-between;
			margin-bottom: 16px;
			flex: 0 0 auto;

			.top-box-title {
				font-weight: bold;
			}

			.top-box-spacer {
				width: 72px;
				height: 1px;
			}
		}

		.current-detail-box {
			flex: 1 1 auto;
			min-height: 0;
			height: auto;
		}

		.task-finished-state {
			flex: 1 1 auto;
			min-height: 0;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			gap: 16px;
			padding: 32px;
			border: 1px solid var(--border-color);
			border-radius: 8px;
			background: var(--bg-secondary);
			text-align: center;
			box-sizing: border-box;
		}

		.finish-icon {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 64px;
			height: 64px;
			border-radius: 18px;
			background: color-mix(in srgb, var(--link-color) 12%, var(--bg-tertiary));
			color: var(--link-color);
			font-size: 30px;
		}

		.finish-copy {
			max-width: 520px;
		}

		.finish-title {
			font-size: 20px;
			font-weight: 800;
			color: var(--text-primary);
		}

		.finish-desc {
			margin-top: 8px;
			color: var(--text-secondary);
			font-size: 14px;
			line-height: 1.7;
		}

		.finish-actions {
			display: flex;
			align-items: center;
			justify-content: center;
			flex-wrap: wrap;
			gap: 10px;
		}
	}

	@media (max-width: 768px) {
		.taskCurrentDetail {
			padding: 12px;

			.top-box {
				margin-bottom: 12px;

				.top-box-title {
					font-size: 16px;
				}

				.top-box-spacer {
					width: 64px;
				}
			}

			.task-finished-state {
				padding: 24px 16px;
			}

			.finish-actions {
				width: 100%;

				.el-button {
					flex: 1 1 150px;
					margin-left: 0;
				}
			}
		}
	}
</style>
