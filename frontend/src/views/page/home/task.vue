<template>
	<div class="task">
		<div class="top-box">
			<el-button class="tao-back-button" type="primary" icon="el-icon-back" size="small" @click="goback">返回</el-button>
			<div class="top-box-title">作业详情</div>
			<menuRefresh :loading="loading" :busy="requesting" :autoRefresh="false" :needShow="1" @getData="getTaskList"></menuRefresh>
		</div>
		<div class="task-content">
			<div class="table-box">
				<div v-if="loading || !hasRows" class="task-state-shell">
					<div class="task-state-card" :class="loading ? 'is-loading' : 'is-empty'">
						<div class="task-state-mark">
							<i :class="loading ? 'el-icon-loading' : 'el-icon-document-remove'"></i>
						</div>
						<div class="task-state-copy">
							<div class="task-state-title">{{ loading ? '正在读取作业列表' : '当前没有作业记录' }}</div>
							<div class="task-state-desc">
								{{ loading ? '请稍等，正在同步最新作业数据。' : '当前筛选条件下没有匹配作业，换个条件再看。' }}
							</div>
						</div>
					</div>
				</div>
				<el-table
					v-else
					:data="taskData.dataList"
					height="100%"
					class="table-data"
					:row-class-name="taskRowClassName"
					@row-dblclick="handleRowDblclick">
					<el-table-column type="index" label="序号" align="center" width="60"></el-table-column>
					<el-table-column prop="status" label="状态" width="130">
						<template slot-scope="scope">
							<div :class="`bg-status bg-${scope.row.status < 6 ? scope.row.status : 7}`">
								<template v-if="scope.row.status == 1 && scope.row.allNum == 0">
									扫描同步中
								</template>
								<template v-else-if="scope.row.status == 2 && scope.row.allNum == 0">
									无需同步
								</template>
								<template v-else>
									<span v-if="scope.row.status != 6">
										{{ scope.row.status | taskStatusFilter }}
									</span>
									<el-popover v-else placement="top-end" title="错误原因" width="200" trigger="hover"
										:content="scope.row.errMsg">
										<span slot="reference">失败，<span class="link-text-inline">原因</span></span>
									</el-popover>
								</template>
							</div>
						</template>
					</el-table-column>
					<el-table-column
						prop="successNum"
						label="任务进度（意义见页面底部图例，单位个）"
						:min-width="progressColumnMinWidth">
						<template slot-scope="scope">
							<span v-if="scope.row.status == 1">查看右侧实时详情</span>
							<div class="progress-numbers" v-else>
								<span class="prgNum bg-8">{{ scope.row.allNum }}</span>
								<span class="prgNum bg-2">{{ scope.row.successNum }}</span>
								<span class="prgNum bg-7">{{ scope.row.failNum }}</span>
								<span class="prgNum bg-3">{{ scope.row.otherNum }}</span>
							</div>
						</template>
					</el-table-column>
					<el-table-column prop="alarmTime" label="创建时间" width="160">
						<template slot-scope="scope">
							{{ scope.row.createTime | timeStampFilter }}
						</template>
					</el-table-column>
					<el-table-column label="结束时间" width="160">
						<template slot-scope="scope">
							{{ finishTimeText(scope.row) }}
						</template>
					</el-table-column>
					<el-table-column label="耗时" width="150">
						<template slot-scope="scope">
							{{ durationText(scope.row) }}
						</template>
					</el-table-column>
					<el-table-column label="操作" width="180">
						<template slot-scope="scope">
							<div class="task-action-group">
								<el-button
									class="mgmt-danger-button"
									type="danger"
									icon="el-icon-delete"
									@click="delTask(scope.row.id)"
									:loading="btnLoading"
									:disabled="scope.row.status == 1"
									size="mini">删除</el-button>
								<el-button
									type="primary"
									:icon="isRunningTask(scope.row) ? 'el-icon-loading' : 'el-icon-view'"
									@click="detail(scope.row)"
									:loading="btnLoading"
									size="mini">详情</el-button>
							</div>
						</template>
					</el-table-column>
				</el-table>
			</div>
		</div>
		<div class="page">
			<div class="page-tip">
				<span>进度图例：</span>
				<span class="prgNum bg-8">总数</span>
				<span class="prgNum bg-2">成功</span>
				<span class="prgNum bg-7">失败</span>
				<span class="prgNum bg-3">其他</span>
			</div>
			<el-pagination
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
				:current-page="params.pageNum"
				:page-size="params.pageSize"
				:total="taskData.count"
				:layout="paginationLayout"
				:page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
	</div>
</template>

<script>
import {
	jobGetTask,
	jobDeleteTask
} from "@/api/job";
import { createDelayedLoadingController } from '@/utils/loadingFeedback';
import menuRefresh from './components/menuRefresh';

export default {
	name: 'Task',
	components: {
		menuRefresh
	},
	data() {
		return {
			taskData: {
				dataList: [],
				count: 0
			},
			params: {
				id: null,
				pageSize: 10,
				pageNum: 1
			},
			loading: false,
			requesting: false,
			btnLoading: false,
			isMobile: false,
			loadingController: null
		};
	},
	computed: {
		hasRows() {
			return !!(this.taskData && this.taskData.dataList && this.taskData.dataList.length > 0);
		},
		paginationLayout() {
			if (this.isMobile) {
				return 'sizes, prev, pager, next';
			}
			return 'total, sizes, prev, pager, next, jumper';
		},
		progressColumnMinWidth() {
			if (this.isMobile) {
				return 280;
			}
			return 200;
		}
	},
	mounted() {
		this.checkMobile();
		window.addEventListener('resize', this.checkMobile);
	},
	created() {
		this.loadingController = createDelayedLoadingController({
			show: () => { this.loading = true; },
			hide: () => { this.loading = false; },
			delay: 120,
			minDuration: 180
		});
		if (this.$route.query.hasOwnProperty('jobId')) {
			this.params.id = this.$route.query.jobId;
		}
	},
	beforeDestroy() {
		window.removeEventListener('resize', this.checkMobile);
		if (this.loadingController) {
			this.loadingController.dispose();
		}
	},
		methods: {
		getTaskList(options = {}) {
			if (this.params.id != null && !this.requesting) {
				this.requesting = true;
				const isManualRefresh = options && options.trigger === 'manual';
				const loadToken = this.loadingController ? this.loadingController.start(isManualRefresh ? {
					delay: 0,
					minDuration: 360
				} : undefined) : 0;
				jobGetTask(this.params).then(res => {
					this.taskData = res.data;
					this.requesting = false;
					if (this.loadingController) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
				}).catch(() => {
					this.requesting = false;
					if (this.loadingController) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
				});
			}
		},
		delTask(taskId) {
			this.$confirm("此操作不可逆，将永久删除该记录，确定吗？", '提示', {
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning'
			}).then(() => {
				this.btnLoading = true;
				jobDeleteTask(taskId).then(res => {
					this.btnLoading = false;
					this.$message({
						message: res.msg,
						type: 'success'
					});
					this.getTaskList();
				}).catch(() => {
					this.btnLoading = false;
				});
			});
		},
		detail(row) {
			if (!row) {
				return;
			}
			if (this.isRunningTask(row)) {
				this.$router.push({
					path: '/home/task/current',
					query: {
						jobId: this.params.id,
						taskId: row.id
					}
				});
				return;
			}
			this.$router.push({
				path: '/home/task/detail',
				query: {
					taskId: row.id
				}
			});
		},
		goback() {
			this.$router.go(-1);
		},
		handleSizeChange(val) {
			this.params.pageSize = val;
			this.getTaskList();
		},
		handleCurrentChange(val) {
			this.params.pageNum = val;
			this.getTaskList();
		},
		isRunningTask(row) {
			return row && row.status == 1;
		},
		finishTimeText(row) {
			if (!row || this.isRunningTask(row)) {
				return '--';
			}
			const duration = Number(row.duration);
			if (!Number.isFinite(duration) || duration < 0 || !row.createTime) {
				return '--';
			}
			return this.$options.filters.timeStampFilter(row.createTime + duration);
		},
		durationText(row) {
			if (!row || !row.createTime) {
				return '--';
			}
			if (this.isRunningTask(row)) {
				return this.formatDuration(Math.max(0, Math.floor(Date.now() / 1000) - row.createTime));
			}
			const duration = Number(row.duration);
			if (!Number.isFinite(duration) || duration < 0) {
				return '--';
			}
			return this.formatDuration(duration);
		},
		formatDuration(seconds) {
			const totalSeconds = Math.max(0, Number(seconds) || 0);
			const days = Math.floor(totalSeconds / 86400);
			const hours = Math.floor((totalSeconds % 86400) / 3600);
			const minutes = Math.floor((totalSeconds % 3600) / 60);
			const secs = Math.floor(totalSeconds % 60);
			const parts = [];
			if (days) parts.push(`${days}天`);
			if (hours) parts.push(`${hours}小时`);
			if (minutes) parts.push(`${minutes}分钟`);
			if (secs || parts.length === 0) parts.push(`${secs}秒`);
			return parts.join(' ');
		},
		taskRowClassName({ row }) {
			return this.isRunningTask(row) ? 'is-running-task-row' : '';
		},
		handleRowDblclick(row) {
			if (row && row.id) {
				this.detail(row);
			}
		},
		checkMobile() {
			this.isMobile = window.innerWidth <= 768;
		}
	}
}
</script>

<style lang="scss" scoped>
	.task {
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
			flex-shrink: 0;

			.top-box-title {
				font-weight: bold;
			}
		}

		.task-content {
			flex: 1 1 auto;
			display: flex;
			flex-direction: column;
			min-height: 0;
			overflow: hidden;
		}

		.table-box {
			flex: 1 1 260px;
			min-height: 220px;
			overflow-y: auto;
			padding: 10px 2px 12px 0;
			display: flex;
			flex-direction: column;
		}

		.task-state-shell {
			flex: 1 1 auto;
			min-height: 0;
			display: flex;
			align-items: flex-start;
		}

		.task-state-card {
			position: relative;
			display: grid;
			grid-template-columns: auto minmax(0, 1fr);
			align-items: center;
			gap: 14px;
			width: 100%;
			min-height: 120px;
			margin-bottom: 8px;
			padding: 16px;
			border: 1px solid var(--border-color);
			border-radius: 18px;
			background:
				radial-gradient(circle at 14% 18%, color-mix(in srgb, var(--link-color) 7%, transparent), transparent 18rem),
				var(--bg-secondary);
			box-sizing: border-box;
			overflow: hidden;
		}

		.task-state-card.is-loading {
			border-color: color-mix(in srgb, var(--link-color) 18%, var(--border-color));
		}

		.task-state-card.is-loading::after {
			content: "";
			position: absolute;
			inset: 0;
			transform: translateX(-110%);
			background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--link-color) 14%, transparent), transparent);
			animation: taskSweep 1.35s ease-in-out infinite;
			pointer-events: none;
		}

		.task-state-mark {
			width: 52px;
			height: 52px;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 16px;
			font-size: 22px;
			flex-shrink: 0;
			background: color-mix(in srgb, var(--bg-tertiary) 82%, transparent);
			color: var(--text-muted);
		}

		.task-state-card.is-loading .task-state-mark {
			background: color-mix(in srgb, var(--link-color) 10%, var(--bg-tertiary));
			color: var(--link-color);
		}

		.task-state-copy {
			min-width: 0;
		}

		.task-state-title {
			font-size: 16px;
			font-weight: 800;
			color: var(--text-primary);
		}

		.task-state-desc {
			margin-top: 4px;
			font-size: 13px;
			line-height: 1.65;
			color: var(--text-muted);
		}

		::v-deep .is-running-task-row {
			background: color-mix(in srgb, var(--link-color) 8%, var(--bg-secondary));
		}

		::v-deep .is-running-task-row:hover > td {
			background: color-mix(in srgb, var(--link-color) 12%, var(--bg-tertiary)) !important;
		}

		.task-action-group {
			display: flex;
			align-items: center;
			justify-content: flex-start;
			gap: 8px;
		}

		::v-deep .table-data .cell {
			line-height: 1.35;
		}

		.progress-numbers {
			display: flex;
			align-items: center;
			flex-wrap: wrap;
			gap: 4px;
		}

		.prgNum {
			font-size: 14px;
			padding: 1px 3px;
			text-align: center;
			font-weight: bold;
			margin: 0;
			min-width: 56px;
			border-radius: 3px;
			flex-shrink: 0;
		}

		.page {
			flex: 0 0 auto;
			margin-top: 12px;
			padding: 10px 0 2px;
			border-top: 1px solid var(--border-color);
			background: color-mix(in srgb, var(--bg-primary) 84%, transparent);
			display: flex;
			align-items: center;
			justify-content: space-between;
			flex-wrap: wrap;
			gap: 16px;
			box-sizing: border-box;
			overflow: hidden;

			.page-tip {
				display: flex;
				align-items: center;
				flex-wrap: wrap;
				gap: 8px;
				flex: 1;
				min-width: 0;

				span {
					white-space: nowrap;
				}
			}

			::v-deep .el-pagination {
				flex-shrink: 0;
				white-space: normal;
			}
		}

		.link-text-inline {
			color: var(--link-color);
		}
	}

	@keyframes taskSweep {
		to {
			transform: translateX(110%);
		}
	}

	@media (max-width: 768px) {
		.task {
			padding: 12px;

			.table-box {
				min-height: 240px;
				padding: 10px 0 12px;
				-ms-overflow-style: none;
			}

			.task-state-card {
				grid-template-columns: 1fr;
				justify-items: center;
				text-align: center;
				padding: 14px 12px;
			}

			.task-state-mark {
				width: 48px;
				height: 48px;
				font-size: 20px;
			}

			.progress-numbers {
				flex-wrap: nowrap;
				gap: 2px;
			}

			.prgNum {
				font-size: 12px;
				padding: 2px 4px;
				min-width: 50px;
			}

			.page {
				margin-top: 10px;
				padding-top: 8px;
				padding-bottom: 2px;
				justify-content: center;
				scrollbar-width: none;
				-ms-overflow-style: none;

				.page-tip {
					display: none;
				}

				::v-deep .el-pagination {
					width: auto;
					max-width: 100%;
					justify-content: center;
					align-items: center;
					flex-wrap: nowrap;
					column-gap: 6px;
					min-width: 0;

					.el-pagination__total,
					.el-pagination__jump {
						display: none;
					}
				}

				::v-deep .el-pagination > * {
					min-width: 0;
				}

				::v-deep .el-pagination__sizes {
					margin: 0;
				}

				::v-deep .el-pagination__sizes .el-input {
					width: 84px;
				}

				::v-deep .el-pagination__sizes .el-input__inner {
					padding: 0 22px 0 8px;
				}

				::v-deep .el-pagination button,
				::v-deep .el-pager li {
					min-width: 28px;
				}

				::v-deep .el-pager li {
					margin: 0 2px;
				}
			}

			.page::-webkit-scrollbar,
			.table-box::-webkit-scrollbar {
				width: 0;
				height: 0;
				display: none;
			}
		}
	}
</style>
