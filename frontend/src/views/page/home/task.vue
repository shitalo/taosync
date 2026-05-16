<template>
	<div class="task">
		<div class="top-box">
			<el-button class="tao-back-button" type="primary" icon="el-icon-back" size="small" @click="goback">返回</el-button>
			<div class="top-box-title">作业详情</div>
			<menuRefresh :loading="loading" :autoRefresh="false" :needShow="1" @getData="getTaskList"></menuRefresh>
		</div>
		<div class="task-content">
			<div class="table-box">
				<el-table
					:data="taskData.dataList"
					height="100%"
					class="table-data"
					v-loading="loading"
					empty-text="暂无任务"
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
									{{scope.row.status | taskStatusFilter}}
								</span>
								<el-popover v-else placement="top-end" title="错误原因" width="200" trigger="hover"
									:content="scope.row.errMsg">
									<span slot="reference">失败，<span class="link-text-inline">原因</span></span>
								</el-popover>
							</template>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="successNum" label="任务进度（意义见页面底部图例，单位个）" :min-width="progressColumnMinWidth">
					<template slot-scope="scope">
						<span v-if="scope.row.status == 1">查看右侧实时详情</span>
						<div class="progress-numbers" v-else>
							<span class="prgNum bg-8">{{scope.row.allNum}}</span>
							<span class="prgNum bg-2">{{scope.row.successNum}}</span>
							<span class="prgNum bg-7">{{scope.row.failNum}}</span>
							<span class="prgNum bg-3">{{scope.row.otherNum}}</span>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="alarmTime" label="创建时间" width="160">
					<template slot-scope="scope">
						{{scope.row.createTime | timeStampFilter}}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="180">
					<template slot-scope="scope">
						<div class="task-action-group">
							<el-button class="mgmt-danger-button" type="danger" icon="el-icon-delete" @click="delTask(scope.row.id)"
								:loading="btnLoading" :disabled="scope.row.status == 1"
								size="mini">删除</el-button>
							<el-button type="primary" :icon="isRunningTask(scope.row) ? 'el-icon-loading' : 'el-icon-view'" @click="detail(scope.row)"
								:loading="btnLoading" size="mini">详情</el-button>
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
			<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
				:current-page="params.pageNum" :page-size="params.pageSize" :total="taskData.count"
				:layout="paginationLayout" :page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
	</div>
</template>

<script>
	import {
		jobGetTask,
		jobDeleteTask
	} from "@/api/job";
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
					conut: 0
				},
				params: {
					id: null,
					pageSize: 10,
					pageNum: 1
				},
				loading: false,
				btnLoading: false,
				isMobile: false
			};
		},
		computed: {
			paginationLayout() {
				// 根据屏幕尺寸动态调整分页布局
				if (this.isMobile) {
					return 'sizes, prev, pager, next';
				}
				return 'total, sizes, prev, pager, next, jumper';
			},
			progressColumnMinWidth() {
				// 根据屏幕尺寸动态调整进度列的最小宽度
				if (this.isMobile) {
					return 280; // 移动端确保四个数字能在一行显示
				}
				return 200; // PC端使用较小值，让列自适应
			}
		},
		mounted() {
			this.checkMobile();
			window.addEventListener('resize', this.checkMobile);
		},
		created() {
			if (this.$route.query.hasOwnProperty('jobId')) {
				this.params.id = this.$route.query.jobId;
			}
		},
		beforeDestroy() {
			window.removeEventListener('resize', this.checkMobile);
		},
		methods: {
			getTaskList() {
				if (this.params.id != null) {
					this.loading = true;
					jobGetTask(this.params).then(res => {
						this.loading = false;
						this.taskData = res.data;
					}).catch(err => {
						this.loading = false;
					})
				}
			},
			delTask(taskId) {
				this.$confirm("操作不可逆，将永久删除该记录，确定吗？", '提示', {
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
					}).catch(err => {
						this.btnLoading = false;
					})
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
					})
					return;
				}
				this.$router.push({
					path: '/home/task/detail',
					query: {
						taskId: row.id
					}
				})
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
			overflow: hidden;
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
			overflow-x: auto;
			overflow-y: hidden;

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
				white-space: nowrap;
			}
		}

		.link-text-inline {
			color: var(--link-color);
		}
	}

	// 移动端适配
	@media (max-width: 768px) {
		.task {
			padding: 12px;

			.table-box {
				min-height: 240px;
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

				.page-tip {
					display: none;
				}

				::v-deep .el-pagination {
					width: 100%;
					justify-content: center;
					
					.el-pagination__total,
					.el-pagination__jump {
						display: none;
					}
				}
			}
		}
	}

	// 超小屏幕适配
	@media (max-width: 480px) {
		.task {
			.page {
				::v-deep .el-pagination {
					.el-pagination__total,
					.el-pagination__jump {
						display: none;
					}
					
					// 在超小屏幕上保持 sizes 显示，但可以调整样式
					.el-pagination__sizes {
						.el-input__inner {
							padding: 0 20px 0 8px;
						}
					}
				}
			}
		}
	}
</style>
