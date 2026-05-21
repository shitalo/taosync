<template>
	<div class="taskCurrent">
		<div class="content-none-data" v-if="current === null">
			{{ emptyStateLoading ? '加载中...' : '作业未在进行中' }}
		</div>
		<div class="current-box" v-else>
			<div class="current-box-top">
				<div class="current-box-top-left">
					<div class="top-line">
						<div style="display: flex; align-items: center; min-width: 0; flex: 1;">
							整体进度：
							<span class="info-value" v-if="current.firstSync === null" style="display: inline-block;">暂未发现需同步文件</span>
							<template v-else style="display: inline-flex; align-items: center;">
								<el-progress
									:stroke-width="20"
									:text-inside="true"
									style="width: 130px; flex-shrink: 0;"
									color="rgba(64, 158, 255, .8)"
									text-color="#fff"
									define-back-color="rgba(64, 158, 255, .3)"
									:percentage="Number(current.allProgress.toFixed(4))"></el-progress>
								<el-tooltip
									v-if="!current.scanFinish"
									effect="dark"
									content="扫描未完成前，进度仅供参考"
									placement="top-end">
									<i class="el-icon-question" style="margin-left: 6px; flex-shrink: 0;"></i>
								</el-tooltip>
							</template>
						</div>
						<div>当前状态：<span class="info-value">{{ currentStatusText }}</span></div>
						<div>
							平均速度：
							<span class="info-value" v-if="current.firstSync === null">--</span>
							<span class="info-value" v-else>{{ current.speedAvg | sizeFilter }}/s</span>
							<el-tooltip
								v-if="current.firstSync !== null"
								effect="dark"
								placement="top-end"
								content="如果扫描用时太久，估算速度可能有较大误差">
								<i class="el-icon-question" style="margin-left: 6px;"></i>
							</el-tooltip>
						</div>
						<div>
							瞬时速度：
							<span class="info-value" v-if="current.firstSync === null">--</span>
							<span class="info-value" v-else>{{ current.speed | sizeFilter }}/s</span>
						</div>
					</div>
					<div class="top-line">
						<div>持续时间：<span class="info-value">{{ current.durationText }}</span></div>
						<div>
							预计还要：<span class="info-value">{{ current.firstSync === null ? '--' : current.remainTimeText }}</span>
							<el-tooltip
								effect="dark"
								placement="top-end"
								:content="`${current.scanFinish ? '' : '扫描未完成前，预计时间仅供参考；'}如果扫描用时太久，估算时间可能有较大误差`">
								<i class="el-icon-question" style="margin-left: 6px;"></i>
							</el-tooltip>
						</div>
						<div>开始时间：<span class="info-value">{{ current.createTime | timeStampFilter }}</span></div>
						<div>
							预计完成：
							<span class="info-value" v-if="current.firstSync === null">--</span>
							<span class="info-value" v-else>{{ (current.createTime + current.duration + current.remainTime) | timeStampFilter }}</span>
							<el-tooltip
								v-if="current.firstSync !== null"
								effect="dark"
								placement="top-end"
								:content="`${current.scanFinish ? '' : '扫描未完成前，预计时间仅供参考；'}如果扫描用时太久，估算时间可能有较大误差`">
								<i class="el-icon-question" style="margin-left: 6px;"></i>
							</el-tooltip>
						</div>
					</div>
				</div>
				<div class="current-box-top-right">
					<el-button class="mgmt-danger-button" type="danger" @click="abortJob">中止任务</el-button>
				</div>
			</div>
			<div class="current-box-bottom">
				<div class="current-empty-pane" v-if="current.firstSync === null">
					<div class="content-none-data">扫描中，暂未发现需要同步的文件，请耐心等待...</div>
				</div>
				<taskCurrentEcharts v-else class="current-echart-box" :taskCurrent="current"></taskCurrentEcharts>
				<div class="current-box-task">
					<div class="current-box-task-left">
						<div @click="changeTaskCu(0)" :class="`task-left-item${cuTaskSelect == 0 ? ' is-current' : ''}`">
							等待中
						</div>
						<div @click="changeTaskCu(1)" :class="`task-left-item${cuTaskSelect == 1 ? ' is-current' : ''}`">
							进行中
						</div>
						<div @click="changeTaskCu(2)" :class="`task-left-item${cuTaskSelect == 2 ? ' is-current' : ''}`">
							成功
						</div>
						<div @click="changeTaskCu(7)" :class="`task-left-item${cuTaskSelect == 7 ? ' is-current' : ''}`">
							失败
						</div>
						<div @click="changeTaskCu(-1)" :class="`task-left-item${cuTaskSelect == -1 ? ' is-current' : ''}`">
							其他
						</div>
					</div>
					<taskDetailTable
						class="current-box-task-right"
						:taskItemData="toTable"
						:loading="loadingTask"
						:hasLoaded="taskListHasLoaded"
						@pageChange="pageChange">
					</taskDetailTable>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
	import {
		jobGetTaskCurrent,
		jobPut
	} from "@/api/job";
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	import menuRefresh from './menuRefresh';
	import taskCurrentEcharts from './taskCurrentEcharts';
	import taskDetailTable from "./taskDetailTable";

	export default {
		name: 'Task',
		props: {
			jobId: {
				type: String,
				default: null
			},
			finishOnEmpty: {
				type: Boolean,
				default: false
			}
		},
		components: {
			menuRefresh,
			taskCurrentEcharts,
			taskDetailTable
		},
		computed: {
			toTable() {
				const count = this.cuTaskList.length;
				let dataList = [];
				if (count !== 0) {
					const startIndex = (this.toTableParams.pageNum - 1) * this.toTableParams.pageSize;
					dataList = this.cuTaskList.slice(startIndex, startIndex + this.toTableParams.pageSize);
				}
				return {
					dataList,
					count
				};
			},
			currentStatusText() {
				if (this.current === null) {
					return '--';
				}
				if (this.current.scanFinish && this.current.firstSync === null) {
					return '扫描完成，未发现需同步内容';
				}
				if (this.current.scanFinish) {
					return '扫描完成，同步中';
				}
				if (this.current.firstSync === null) {
					return '扫描中';
				}
				return '扫描并同步中';
			},
			emptyStateLoading() {
				return !this.hasLoaded || this.loading;
			}
		},
		data() {
			return {
				loading: false,
				loadingTask: false,
				hasLoaded: false,
				taskListHasLoaded: true,
				isFetchingCurrent: false,
				isFetchingTaskList: false,
				timer: null,
				hideTimer: null,
				finishTimer: null,
				loadingController: null,
				taskListLoadingController: null,
				cuTaskSelect: 1,
				cuTaskList: [],
				toTableParams: {
					pageSize: 10,
					pageNum: 1
				},
				current: null
			};
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.loading = true; },
				hide: () => { this.loading = false; },
				delay: 120,
				minDuration: 180
			});
			this.taskListLoadingController = createDelayedLoadingController({
				show: () => { this.loadingTask = true; },
				hide: () => { this.loadingTask = false; },
				delay: 120,
				minDuration: 180
			});
			this.startRefresh();
		},
		beforeDestroy() {
			this.endRefresh();
			if (this.hideTimer) {
				clearTimeout(this.hideTimer);
				this.hideTimer = null;
			}
			if (this.finishTimer) {
				clearTimeout(this.finishTimer);
				this.finishTimer = null;
			}
			if (this.loadingController) {
				this.loadingController.dispose();
			}
			if (this.taskListLoadingController) {
				this.taskListLoadingController.dispose();
			}
		},
		methods: {
			startRefresh() {
				this.getCurrent();
				this.timer = setInterval(() => {
					this.getCurrent();
				}, 610);
			},
			endRefresh() {
				if (this.timer) {
					clearInterval(this.timer);
					this.timer = null;
				}
			},
			getCurrent() {
				if (this.isFetchingCurrent) {
					return;
				}
				this.isFetchingCurrent = true;
				const loadToken = this.loadingController ? this.loadingController.start() : 0;
				jobGetTaskCurrent({
					id: this.jobId
				}).then(res => {
					this.dealWithCurrent(res.data, loadToken);
				}).catch(() => {
					this.isFetchingCurrent = false;
					if (this.loadingController) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
				});
			},
			dealWithCurrent(current, loadToken = 0) {
				this.isFetchingCurrent = false;
				this.hasLoaded = true;
				if (current === null) {
					if (this.finishOnEmpty) {
						this.scheduleFinish();
					}
					if (this.current !== null) {
						this.current = null;
						if (!this.hideTimer) {
							this.hideTimer = setTimeout(() => {
								this.hideTimer = null;
								if (this.current === null) {
									this.hide();
								}
							}, 1800);
						}
					}
					if (this.loadingController) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
					return;
				}

				if (this.finishTimer) {
					clearTimeout(this.finishTimer);
					this.finishTimer = null;
				}
				if (this.hideTimer) {
					clearTimeout(this.hideTimer);
					this.hideTimer = null;
				}
				if (this.current === null) {
					this.show();
				}

				current.durationText = this.formatSeconds(current.duration);
				const calcs = this.calcSpeedAndSize(current);
				if (this.cuTaskSelect === 1) {
					this.cuTaskList = current.doingTask || [];
					this.taskListHasLoaded = true;
				}
				this.current = {
					...current,
					...calcs
				};
				if (this.loadingController) {
					this.loadingController.finish(loadToken);
				} else {
					this.loading = false;
				}
				this.getTaskList();
			},
			scheduleFinish() {
				if (this.finishTimer) {
					return;
				}
				this.finishTimer = setTimeout(() => {
					this.finishTimer = null;
					if (this.current === null) {
						this.endRefresh();
						this.$emit('currentFinished');
					}
				}, 1800);
			},
			getTaskList() {
				if (this.current === null || this.isFetchingTaskList || this.cuTaskSelect === 1) {
					return;
				}
				this.isFetchingTaskList = true;
				if (this.cuTaskList.length === 0) {
					this.taskListHasLoaded = false;
				}
				const loadToken = this.taskListLoadingController ? this.taskListLoadingController.start() : 0;
				jobGetTaskCurrent({
					id: this.jobId,
					status: this.cuTaskSelect
				}).then(res => {
					this.cuTaskList = res.data || [];
					this.taskListHasLoaded = true;
					this.isFetchingTaskList = false;
					if (this.taskListLoadingController) {
						this.taskListLoadingController.finish(loadToken);
					} else {
						this.loadingTask = false;
					}
				}).catch(() => {
					this.taskListHasLoaded = true;
					this.isFetchingTaskList = false;
					if (this.taskListLoadingController) {
						this.taskListLoadingController.finish(loadToken);
					} else {
						this.loadingTask = false;
					}
				});
			},
			calcSpeedAndSize(current) {
				const doingTask = Array.isArray(current.doingTask) ? current.doingTask : [];
				const doingSize = doingTask.reduce((sum, obj) => {
					return sum + obj.fileSize * obj.progress / 100.0;
				}, 0);
				const remainSize = current.size.running - doingSize + current.size.wait;
				const doneSize = current.size.success + doingSize;
				let speed = 0;
				if (this.current !== null) {
					speed = this.current.speed;
					if (current.duration - this.current.duration !== 0 && doneSize - this.current.doneSize !== 0) {
						speed = (doneSize - this.current.doneSize) / (current.duration - this.current.duration);
					}
				}
				const speedAvg = doneSize / (current.duration - current.firstSync + current.createTime);
				const remainTime = parseInt(remainSize / speedAvg);
				return {
					remainSize,
					doneSize,
					speedAvg,
					speed,
					remainTime,
					remainTimeText: this.formatSeconds(remainTime),
					allProgress: doneSize / (doneSize + remainSize) * 100
				};
			},
			changeTaskCu(status) {
				if (this.cuTaskSelect === status || this.current === null) {
					return;
				}
				this.cuTaskSelect = status;
				this.toTableParams.pageNum = 1;
				if (status === 1) {
					this.cuTaskList = this.current.doingTask || [];
					this.taskListHasLoaded = true;
				} else {
					this.getTaskList();
				}
			},
			pageChange(val) {
				this.toTableParams = val;
			},
			formatSeconds(seconds) {
				const totalSeconds = Math.max(0, Number(seconds) || 0);
				const days = Math.floor(totalSeconds / (24 * 3600));
				const hours = Math.floor((totalSeconds % (24 * 3600)) / 3600);
				const minutes = Math.floor((totalSeconds % 3600) / 60);
				const secs = totalSeconds % 60;
				const timeUnits = [
					{ value: days, unit: '天' },
					{ value: hours, unit: '小时' },
					{ value: minutes, unit: '分钟' },
					{ value: secs, unit: '秒' }
				];
				const nonZeroUnits = timeUnits.filter(unit => unit.value > 0);
				if (nonZeroUnits.length === 0) return '0秒';
				return nonZeroUnits.map(unit => `${unit.value}${unit.unit}`).join(' ');
			},
			show() {
				this.$emit('currentChange', 1);
			},
			hide() {
				this.$emit('currentChange', 0);
			},
			abortJob() {
				this.$confirm('中止任务不会影响已完成的同步项，进行中或等待中的同步项将被取消，确定吗？', '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					jobPut({
						pause: true,
						id: Number(this.jobId),
						abort: true
					}).then(() => {
						this.$message({
							message: '中止指令已发送，请等待中止完成',
							type: 'success'
						});
					}).catch(() => {});
				});
			}
		}
	}
</script>

<style lang="scss" scoped>
	.taskCurrent {
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;

		.current-box {
			background-color: var(--bg-secondary);
			flex: 1 1 auto;
			min-height: 0;
			padding: 2px 10px;
			width: 100%;
			box-sizing: border-box;
			overflow-x: auto;
			overflow-y: hidden;
			border: 1px solid var(--border-color);
			border-radius: 8px;
			height: 100%;
			max-height: 100%;
			display: flex;
			flex-direction: column;

			.current-box-top {
				min-width: 1100px;
				box-sizing: border-box;
				flex: 0 0 56px;
				height: 56px;
				padding: 3px 0;
				border-bottom: 1px dotted var(--border-light);
				display: flex;
				align-items: center;
				justify-content: center;

				.current-box-top-left {
					flex: 1;
					min-width: 0;

					.top-line {
						display: flex;
						align-items: center;
						justify-content: center;
						gap: 12px;
						flex-wrap: nowrap;

						div {
							min-width: 180px;
							max-width: 280px;
							flex: 1;
							overflow: hidden;
							text-overflow: ellipsis;
							white-space: nowrap;
							font-size: 13px;
							color: var(--text-primary);
							display: flex;
							align-items: center;

							.info-value {
								display: inline-block;
								max-width: 100%;
								overflow: hidden;
								text-overflow: ellipsis;
								white-space: nowrap;
								vertical-align: middle;
								flex: 1;
								min-width: 0;
							}

							.el-icon-question {
								flex-shrink: 0;
								margin-left: 4px;
							}
						}
					}
				}

				.current-box-top-right {
					margin-left: 16px;
					flex-shrink: 0;
				}
			}

			.current-box-bottom {
				min-width: 1100px;
				box-sizing: border-box;
				flex: 1 1 auto;
				min-height: 0;
				height: auto;
				width: 100%;
				display: flex;
				overflow: hidden;

				.current-echart-box {
					height: 100%;
					width: 40%;
					min-width: 390px;
					box-sizing: border-box;
					border-right: 1px dotted var(--border-light);
				}

				.current-empty-pane {
					width: 40%;
					height: 100%;
					min-height: 0;
					box-sizing: border-box;
					padding: 8px 12px 8px 0;
					border-right: 1px dotted var(--border-light);
					display: flex;
				}

				.current-empty-pane .content-none-data {
					width: 100%;
					min-height: 0;
					height: 100%;
					padding: 18px 20px;
					border-radius: 18px;
					font-size: 14px;
					line-height: 1.6;
					text-align: center;
					white-space: normal;
					overflow-wrap: anywhere;
					word-break: break-word;
					box-sizing: border-box;
				}

				.current-box-task {
					width: 60%;
					height: 100%;
					min-height: 0;
					box-sizing: border-box;
					padding: 8px 0 8px 12px;
					display: flex;
					overflow: hidden;

					.current-box-task-left {
						width: 60px;
						height: 100%;
						flex: 0 0 60px;
						overflow-y: auto;

						.task-left-item {
							cursor: pointer;
							width: 60px;
							margin: 14px 0;
							padding: 3px 6px 3px 0;
							color: var(--text-secondary);
							text-align: right;
							box-sizing: border-box;
							transition: all 0.2s ease;
						}

						.is-current {
							color: var(--link-color);
							border-right: 3px solid var(--link-color);
							background-color: var(--bg-tertiary);
						}
					}

					.current-box-task-right {
						margin-left: 8px;
						width: calc(100% - 68px);
						height: 100%;
						min-height: 0;
						flex: 1 1 auto;
					}
				}
			}
		}
	}

	@media (max-width: 768px) {
		.taskCurrent {
			padding: 0;

			.top-line {
				flex-wrap: wrap;
				gap: 8px;

				div {
					min-width: 140px !important;
					max-width: 100% !important;
					font-size: 12px;
				}
			}

			.current-box {
				overflow-x: auto;
				overflow-y: hidden;

				.current-box-top {
					min-width: 920px;
				}

				.current-box-bottom {
					min-width: 920px;

					.current-empty-pane {
						width: 40%;
						padding: 8px 12px 8px 0;
					}

					.current-empty-pane .content-none-data {
						padding: 16px;
						font-size: 13px;
					}

					.current-box-task {
						width: 100%;
						padding: 8px 0;
						flex-direction: column;

						.current-box-task-left {
							width: 100%;
							display: flex;
							overflow-x: auto;
							padding-bottom: 8px;

							.task-left-item {
								width: auto;
								min-width: 80px;
								text-align: center;
								padding: 6px 12px;
								margin: 0 4px;
								border-right: none;
								border-bottom: 3px solid transparent;
							}

							.is-current {
								border-right: none;
								border-bottom: 3px solid var(--link-color);
							}
						}

						.current-box-task-right {
							width: 100%;
							flex: 1 1 auto;
							min-height: 0;
							margin-left: 0;
							margin-top: 12px;
						}
					}
				}
			}
		}
	}
</style>
