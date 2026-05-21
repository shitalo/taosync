<template>
	<div class="taskDetail">
		<div class="top-box">
			<el-button class="tao-back-button top-box-back" type="primary" icon="el-icon-back" @click="goback" size="small">返回</el-button>
			<div class="top-box-title">任务详情</div>
			<div class="top-box-filters">
				<el-select v-model="params.status" class="task-filter-select" placeholder="筛选状态" @change="getTaskItemList" clearable>
					<el-option :label="item" :value="index" v-for="(item, index) in taskItemStatusList" :key="index"></el-option>
				</el-select>
				<el-select v-model="params.type" class="task-filter-select task-filter-select-type" placeholder="筛选操作类型" @change="getTaskItemList" clearable>
					<el-option label="复制/创建" :value="0"></el-option>
					<el-option label="删除" :value="1"></el-option>
					<el-option label="移动" :value="2"></el-option>
				</el-select>
				<menuRefresh
					class="top-box-refresh"
					:freshInterval="9973"
					:autoRefresh="false"
					:loading="loading"
					:busy="requesting"
					:needShow="1"
					@getData="getTaskItemList"></menuRefresh>
			</div>
		</div>
		<taskDetailTable
			class="table-page-box"
			:loading="loading"
			:hasLoaded="hasLoaded"
			:taskItemData="taskItemData"
			@pageChange="pageChange">
		</taskDetailTable>
	</div>
</template>

<script>
	import {
		jobGetTaskItem
	} from "@/api/job";
	import taskItemStatus from '@/utils/taskItemStatus';
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	import menuRefresh from './components/menuRefresh';
	import taskDetailTable from "./components/taskDetailTable";

	export default {
		name: 'TaskDetail',
		components: {
			menuRefresh,
			taskDetailTable
		},
		data() {
			return {
				taskItemData: {
					dataList: [],
					count: 0
				},
				params: {
					taskId: null,
					pageSize: 10,
					pageNum: 1,
					status: null,
					type: null
				},
				loading: false,
				requesting: false,
				hasLoaded: false,
				btnLoading: false,
				taskId: null,
				taskItemStatusList: [],
				loadingController: null
			};
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.loading = true; },
				hide: () => { this.loading = false; },
				delay: 120,
				minDuration: 180
			});
			if (this.$route.query.hasOwnProperty('taskId')) {
				this.params.taskId = this.$route.query.taskId;
			}
			this.taskItemStatusList = taskItemStatus;
		},
		beforeDestroy() {
			if (this.loadingController) {
				this.loadingController.dispose();
			}
		},
		methods: {
			getTaskItemList(options = {}) {
				if (this.params.taskId != null && !this.requesting) {
					this.requesting = true;
					const isManualRefresh = options && options.trigger === 'manual';
					const loadToken = this.loadingController ? this.loadingController.start(isManualRefresh ? {
						delay: 0,
						minDuration: 360
					} : undefined) : 0;
					jobGetTaskItem(this.params).then(res => {
						this.hasLoaded = true;
						res.data.dataList.forEach(item => {
							item.progress = parseInt(item.progress);
							item.progress = item.progress < 100 ? item.progress : 100;
						});
						this.taskItemData = res.data;
						this.requesting = false;
						if (this.loadingController) {
							this.loadingController.finish(loadToken);
						} else {
							this.loading = false;
						}
					}).catch(() => {
						this.hasLoaded = true;
						this.requesting = false;
						if (this.loadingController) {
							this.loadingController.finish(loadToken);
						} else {
							this.loading = false;
						}
					});
				}
			},
			goback() {
				this.$router.go(-1);
			},
			pageChange(val) {
				this.params.pageSize = val.pageSize;
				this.params.pageNum = val.pageNum;
				this.getTaskItemList();
			}
		}
	}
</script>

<style lang="scss" scoped>
	.taskDetail {
		width: 100%;
		height: 100%;
		padding: 16px;
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		min-height: 0;
		overflow: hidden;

		.top-box {
			display: grid;
			grid-template-columns: auto minmax(0, 1fr) auto;
			align-items: center;
			column-gap: 14px;
			row-gap: 10px;
			margin-bottom: 16px;
			flex: 0 0 auto;
			min-height: 40px;

			.top-box-title {
				grid-column: 1 / -1;
				grid-row: 1;
				display: flex;
				align-items: center;
				justify-content: center;
				align-self: stretch;
				justify-self: center;
				font-weight: bold;
				text-align: center;
				white-space: nowrap;
				max-width: calc(100% - 360px);
				overflow: hidden;
				text-overflow: ellipsis;
			}

			.top-box-filters {
				grid-column: 3;
				grid-row: 1;
				display: flex;
				align-items: center;
				gap: 8px;
				min-width: 0;
				justify-self: end;
			}

			.top-box-back {
				grid-column: 1;
				grid-row: 1;
				z-index: 1;
			}

			.task-filter-select {
				width: 160px;
			}

			.task-filter-select-type {
				width: 140px;
			}

			.top-box-refresh {
				margin-left: -20px;
			}
		}

		.table-page-box {
			width: 100%;
			flex: 1 1 auto;
			min-height: 0;
			height: auto;
		}
	}

	@media (max-width: 768px) {
		.taskDetail {
			padding: 12px;

			.top-box {
				grid-template-columns: auto minmax(0, 1fr);
				column-gap: 10px;
				row-gap: 10px;
				align-items: center;
				padding: 10px 12px;
				margin-bottom: 12px;
				border: 1px solid var(--border-color);
				border-radius: 16px;
				background: color-mix(in srgb, var(--bg-secondary) 86%, transparent);

				.top-box-back {
					grid-column: 1;
					grid-row: 1;
					z-index: 1;
				}

				.top-box-title {
					grid-column: 1 / -1;
					grid-row: 1;
					display: flex;
					align-items: center;
					justify-content: center;
					align-self: stretch;
					justify-self: center;
					font-size: 15px;
					text-align: center;
					white-space: nowrap;
					min-width: 0;
					max-width: calc(100% - 92px);
					overflow: hidden;
					text-overflow: ellipsis;
				}

				.top-box-filters {
					grid-column: 1 / -1;
					grid-row: 2;
					display: flex;
					flex-wrap: nowrap;
					align-items: center;
					gap: 6px;
					min-width: 0;
					overflow: hidden;
				}

				.task-filter-select,
				.task-filter-select-type {
					flex: 1 1 0;
					width: auto;
					min-width: 0;
				}

				.top-box-refresh {
					flex: 0 0 auto;
				}

				::v-deep .task-filter-select .el-input__inner {
					font-size: 12px;
				}
			}

			.table-page-box {
				flex: 1 1 auto;
				min-height: 0;
				height: auto;
			}
		}
	}
</style>
