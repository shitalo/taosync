<template>
	<div class="taskDetail">
		<div class="top-box">
			<el-button class="tao-back-button top-box-back" type="primary" icon="el-icon-back" @click="goback" size="small">返回</el-button>
			<div class="top-box-title">任务详情</div>
			<div class="top-box-filters">
				<el-select v-model="params.status" class="task-filter-select" placeholder="筛选状态" @change="getTaskItemList" clearable>
					<el-option :label="item" :value="index" v-for="(item, index) in taskItemStatusList"></el-option>
				</el-select>
				<el-select v-model="params.type" class="task-filter-select task-filter-select-type" placeholder="筛选操作类型" @change="getTaskItemList" clearable>
					<el-option label="复制/创建" :value="0"></el-option>
					<el-option label="删除" :value="1"></el-option>
					<el-option label="移动" :value="2"></el-option>
				</el-select>
			</div>
			<menuRefresh class="top-box-refresh" :freshInterval="9973" :autoRefresh="false" :loading="loading" :needShow="1"
				@getData="getTaskItemList"></menuRefresh>
			<!-- <el-button :loading="loading" type="primary" icon="el-icon-refresh" circle @click="getTaskItemList"></el-button> -->
		</div>
		<taskDetailTable class="table-page-box" :loading="loading" :taskItemData="taskItemData" @pageChange="pageChange"></taskDetailTable>
	</div>
</template>

<script>
	import {
		jobGetTaskItem
	} from "@/api/job";
	import taskItemStatus from '@/utils/taskItemStatus';
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
					conut: 0
				},
				params: {
					taskId: null,
					pageSize: 10,
					pageNum: 1,
					status: null
				},
				loading: false,
				btnLoading: false,
				taskId: null,
				taskItemStatusList: []
			};
		},
		created() {
			if (this.$route.query.hasOwnProperty('taskId')) {
				this.params.taskId = this.$route.query.taskId;
			}
			this.taskItemStatusList = taskItemStatus;
		},
		beforeDestroy() {},
		methods: {
			getTaskItemList() {
				if (this.params.taskId != null) {
					this.loading = true;
					jobGetTaskItem(this.params).then(res => {
						this.loading = false;
						res.data.dataList.forEach(item => {
							item.progress = parseInt(item.progress);
							item.progress = item.progress < 100 ? item.progress : 100;
						})
						this.taskItemData = res.data;
					}).catch(err => {
						this.loading = false;
					})
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
			grid-template-columns: auto auto 1fr auto;
			align-items: center;
			column-gap: 14px;
			row-gap: 10px;
			margin-bottom: 16px;
			flex: 0 0 auto;

			.top-box-title {
				font-weight: bold;
				white-space: nowrap;
			}

			.top-box-filters {
				display: flex;
				align-items: center;
				gap: 12px;
				min-width: 0;
			}

			.task-filter-select {
				width: 160px;
			}

			.task-filter-select-type {
				width: 140px;
			}

			.top-box-refresh {
				justify-self: end;
			}
		}

		.table-page-box {
			width: 100%;
			flex: 1 1 auto;
			min-height: 0;
			height: auto;
		}
	}

	// 移动端适配
	@media (max-width: 768px) {
		.taskDetail {
			padding: 12px;

			.top-box {
				grid-template-columns: auto 1fr auto;
				column-gap: 8px;
				row-gap: 10px;
				align-items: center;

				.top-box-title {
					font-size: 16px;
					text-align: center;
				}

				.top-box-back {
					grid-column: 1;
				}

				.top-box-refresh {
					grid-column: 3;
				}

				.top-box-filters {
					grid-column: 1 / -1;
					display: grid;
					grid-template-columns: repeat(2, minmax(0, 1fr));
					gap: 8px;
				}

				.task-filter-select,
				.task-filter-select-type {
					width: 100%;
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
