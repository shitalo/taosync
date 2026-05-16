<template>
	<div class="home">
		<ManagementHero
			kicker="SYNC JOBS"
			title="作业管理"
			description="快速查看同步链路、执行状态与常用操作；列表优先展示更多作业，减少翻页和滚动成本。"
			:statValue="jobData.count || jobData.dataList.length"
			statLabel="总作业"
			actionText="新建作业"
			@action="addShow"
		/>

		<JobList
			:jobData="jobData"
			:loading="loading"
			:hasLoaded="hasLoaded"
			:btnLoading="btnLoading"
			:runningJobCount="runningJobCount"
			:jobRunning="jobRunning"
			:methodText="methodText"
			:callModeText="callModeText"
			:scheduleText="scheduleText"
			:runningTaskText="runningTaskText"
			:destinationList="destinationList"
			:excludeList="excludeList"
			:cacheText="cacheText"
			@add-show="addShow"
			@put-job="putJob"
			@detail="detail"
			@disable-job-show="disableJobShow"
			@edit-job-show="editJobShow"
		/>
		<div class="page">
			<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
				:current-page="params.pageNum" :page-size="params.pageSize" :total="jobData.count"
				:layout="paginationLayout" :page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
		<JobEditorDialog
			ref="jobEditorDialog"
			:visible="editShow"
			:editData="editData"
			:rules="addRule"
			:isMobile="isMobile"
			:dialogWidth="dialogWidth"
			:openlistList="openlistList"
			:cronPreset="cronPreset"
			:cronList="cronList"
			:timeWindowPreset="timeWindowPreset"
			:weekOptions="weekOptions"
			:monthDayOptions="monthDayOptions"
			:loading="editLoading"
			@close="closeShow"
			@submit="submit"
			@select-path="selectPath"
			@delete-dst-path="delDstPath"
			@add-exclude="addExclude"
			@delete-exclude="delExclude"
			@open-ignore-help="toIgnore"
			@open-cron-help="toCron"
			@apply-cron-preset="applyCronPreset"
			@apply-time-window-preset="applyTimeWindowPreset"
			@time-window-mode-change="handleTimeWindowModeChange"
			@format-time-window-point="formatTimeWindowPoint"
			@remove-time-window-range="removeTimeWindowRange"
			@apply-time-window-ranges="applyTimeWindowRangePreset"
			@add-time-window-range="addTimeWindowRange"
		/>
		<el-dialog :close-on-click-modal="false" :visible.sync="disableShow" :append-to-body="true" title="警告"
			:width="isMobile ? '90%' : '460px'" :before-close="closeDisableShow">
			<div class="error-message">
				{{ disableIsDel ? '此操作不可逆，将永久删除该作业，确认吗？' : '将禁用任务，确认吗？' }}
			</div>
			<span slot="footer" class="dialog-footer">
				<el-button @click="closeDisableShow">取消</el-button>
				<el-button type="primary" @click="submitDisable" :loading="editLoading">确定</el-button>
			</span>
		</el-dialog>
		<pathSelect v-if="editData" :openlistId="editData.openlistId" ref="pathSelect" @submit="submitPath"></pathSelect>
	</div>
</template>

<script>
	import {
		jobGetJob,
		jobPut,
		jobDelete,
		jobPost,
		openlistGet
	} from "@/api/job";
	import JobEditorDialog from './components/JobEditorDialog.vue';
	import JobList from './components/JobList.vue';
	import pathSelect from './components/pathSelect.vue';
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	import ManagementHero from '@/views/components/ManagementHero.vue';
	export default {
		name: 'Home',
		components: {
			ManagementHero,
			JobEditorDialog,
			JobList,
			pathSelect
		},
		data() {
			return {
				jobData: {
					dataList: [],
					count: 0
				},
				params: {
					pageSize: 10,
					pageNum: 1
				},
				openlistList: [],
				weekOptions: [{
					label: '周一',
					value: 0
				}, {
					label: '周二',
					value: 1
				}, {
					label: '周三',
					value: 2
				}, {
					label: '周四',
					value: 3
				}, {
					label: '周五',
					value: 4
				}, {
					label: '周六',
					value: 5
				}, {
					label: '周日',
					value: 6
				}],
				monthDayOptions: Array.from({ length: 31 }, (_, index) => index + 1),
				timeWindowPreset: 'night',
				cronPreset: 'custom',
				cronList: [{
					label: 'year',
					palce: '2024'
				}, {
					label: 'month',
					palce: '1-12'
				}, {
					label: 'day',
					palce: '1-31'
				}, {
					label: 'week',
					palce: '1-53'
				}, {
					label: 'day_of_week',
					palce: '0-6 or mon,tue,wed,thu,fri,sat,sun'
				}, {
					label: 'hour',
					palce: '0-23'
				}, {
					label: 'minute',
					palce: '0-59'
				}, {
					label: 'second',
					palce: '0-59'
				}, {
					label: 'start_date',
					palce: '2000-01-01'
				}, {
					label: 'end_date',
					palce: '2040-12-31'
				}],
				cuIsSrc: false,
				loading: false,
				hasLoaded: false,
				loadingController: null,
				jobRefreshTimer: null,
				btnLoading: false,
				editLoading: false,
				editData: null,
				editShow: false,
				disableShow: false,
				disableIsDel: false,
				disableCu: {
					id: null,
					pause: true
				},
				isMobile: false,
				addRule: {
					srcPath: [{
						required: true,
						message: '请选择来源目录',
						trgger: 'change'
					}],
					dstPath: [{
						type: 'array',
						required: true,
						message: '请选择目标目录',
						trgger: 'change'
					}],
					openlistId: [{
						type: 'number',
						required: true,
						message: '请选择引擎',
						trgger: 'change'
					}],
					scanIntervalT: [{
						required: true,
						pattern: /^(0|[1-9]\d*)$/,
						message: '必填且需为非负整数',
						trgger: 'blur'
					}],
					scanIntervalS: [{
						required: true,
						pattern: /^(0|[1-9]\d*)$/,
						message: '必填且需为非负整数',
						trgger: 'blur'
					}]
				}
			};
		},
		computed: {
			runningJobCount() {
				return (this.jobData.dataList || []).filter(item => this.jobRunning(item)).length;
			},
			dialogWidth() {
				return this.isMobile ? 'calc(100vw - 20px)' : 'min(1080px, calc(100vw - 56px))';
			},
			paginationLayout() {
				if (this.isMobile) {
					return 'sizes, prev, pager, next';
				}
				return 'total, sizes, prev, pager, next, jumper';
			}
		},
		mounted() {
			this.checkMobile();
			window.addEventListener('resize', this.checkMobile);
			this.startJobStatusRefresh();
		},
		beforeDestroy() {
			window.removeEventListener('resize', this.checkMobile);
			if (this.jobRefreshTimer) {
				clearInterval(this.jobRefreshTimer);
			}
			if (this.loadingController) {
				this.loadingController.dispose();
			}
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.loading = true; },
				hide: () => { this.loading = false; }
			});
			this.getJobList();
		},
		methods: {
			checkMobile() {
				this.isMobile = window.innerWidth <= 768;
			},
			methodText(method) {
				return method == 0 ? '仅新增' : (method == 1 ? '全同步' : '移动模式');
			},
			callModeText(row) {
				return row.isCron == 0 ? '间隔调用' : (row.isCron == 1 ? 'Cron 计划' : (row.isCron == 3 ? '时间段调用' : '仅手动'));
			},
			scheduleText(row) {
				if (row.isCron == 0) {
					return `${row.interval || 0} 分钟一次`;
				}
				if (row.isCron == 1) {
					const activeCron = this.cronList.filter(item => row[item.label] != null && row[item.label] !== '').map(item => `${item.label}:${row[item.label]}`);
					return activeCron.length ? activeCron.slice(0, 2).join(' / ') : 'Cron 未配置';
				}
				if (row.isCron == 3) {
					return this.timeWindowText(row.timeWindow);
				}
				return '需要时手动执行';
			},
			clearCronFields(target = this.editData) {
				this.cronList.forEach(item => {
					target[item.label] = null;
				});
			},
			applyCronPreset(key) {
				this.cronPreset = key;
				if (!this.editData) {
					return;
				}
				if (key == 'custom') {
					return;
				}
				this.clearCronFields(this.editData);
				this.editData.minute = '0';
				this.editData.second = '0';
				if (key == 'daily-2am') {
					this.editData.hour = '2';
				} else if (key == 'daily-3am') {
					this.editData.hour = '3';
				} else if (key == 'weekend-2am') {
					this.editData.hour = '2';
					this.editData.day_of_week = 'sat,sun';
				}
				this.$nextTick(() => {
					if (this.$refs.jobEditorDialog && this.$refs.jobEditorDialog.syncCronEditorFromFields) {
						this.$refs.jobEditorDialog.syncCronEditorFromFields();
					}
				});
			},
			refreshCronPreset() {
				if (!this.editData) {
					this.cronPreset = 'custom';
					return;
				}
				const noDateLimit = ['year', 'month', 'day', 'week', 'start_date', 'end_date'].every(key => !this.editData[key]);
				const isMinuteSecondZero = `${this.editData.minute || ''}` == '0' && `${this.editData.second || ''}` == '0';
				if (noDateLimit && isMinuteSecondZero && `${this.editData.hour || ''}` == '2' && !this.editData.day_of_week) {
					this.cronPreset = 'daily-2am';
				} else if (noDateLimit && isMinuteSecondZero && `${this.editData.hour || ''}` == '3' && !this.editData.day_of_week) {
					this.cronPreset = 'daily-3am';
				} else if (noDateLimit && isMinuteSecondZero && `${this.editData.hour || ''}` == '2' && this.editData.day_of_week == 'sat,sun') {
					this.cronPreset = 'weekend-2am';
				} else {
					this.cronPreset = 'custom';
				}
			},
			defaultTimeWindow() {
				return {
					mode: 'daily',
					days: [],
					daysOfMonth: [],
					ranges: [{ start: '00:00', end: '07:00' }]
				};
			},
			quickTimeWindowConfig(key) {
				if (key == 'night') {
					return { mode: 'daily', days: [], daysOfMonth: [], ranges: [{ start: '22:00', end: '24:00' }, { start: '00:00', end: '07:00' }] };
				}
				if (key == 'daylight') {
					return { mode: 'daily', days: [], daysOfMonth: [], ranges: [{ start: '07:00', end: '22:00' }] };
				}
				if (key == 'weekday-night') {
					return { mode: 'week', days: [0, 1, 2, 3, 4], daysOfMonth: [], ranges: [{ start: '21:30', end: '24:00' }, { start: '00:00', end: '07:30' }] };
				}
				return this.defaultTimeWindow();
			},
			applyTimeWindowPreset(key) {
				this.timeWindowPreset = key;
				if (key == 'custom') {
					if (!this.editData.timeWindow.ranges || this.editData.timeWindow.ranges.length == 0) {
						this.editData.timeWindow.ranges = [{ start: '00:00', end: '07:00' }];
					}
					return;
				}
				this.editData.timeWindow = this.normalizeTimeWindow(this.quickTimeWindowConfig(key));
			},
			normalizeTimeWindow(value) {
				let result = this.defaultTimeWindow();
				if (value) {
					try {
						const parsed = typeof value === 'string' ? JSON.parse(value) : value;
						result = Object.assign(result, parsed || {});
					} catch (e) {}
				}
				if (!Array.isArray(result.days)) result.days = [];
				if (!Array.isArray(result.daysOfMonth)) result.daysOfMonth = [];
				if (!Array.isArray(result.ranges) || result.ranges.length == 0) result.ranges = [{ start: '00:00', end: '07:00' }];
				return result;
			},
			refreshTimeWindowPreset() {
				const config = this.normalizeTimeWindow(this.editData.timeWindow);
				const compare = (a, b) => JSON.stringify(a) == JSON.stringify(b);
				if (compare(config, this.quickTimeWindowConfig('night'))) {
					this.timeWindowPreset = 'night';
				} else if (compare(config, this.quickTimeWindowConfig('daylight'))) {
					this.timeWindowPreset = 'daylight';
				} else if (compare(config, this.quickTimeWindowConfig('weekday-night'))) {
					this.timeWindowPreset = 'weekday-night';
				} else {
					this.timeWindowPreset = 'custom';
				}
			},
			timeWindowText(value) {
				const config = this.normalizeTimeWindow(value);
				const modeText = config.mode == 'daily'
					? '每天'
					: (config.mode == 'week'
						? `每周 ${(config.days || []).length || 0} 天`
						: `每月 ${(config.daysOfMonth || []).length || 0} 天`);
				const rangeText = (config.ranges || []).slice(0, 2).map(item => `${item.start}-${item.end}`).join(' / ');
				return `${modeText} ${rangeText || '未设置时间段'}`;
			},
			addTimeWindowRange() {
				this.editData.timeWindow.ranges.push({ start: '00:00', end: '07:00' });
				this.timeWindowPreset = 'custom';
			},
			applyTimeWindowRangePreset(ranges) {
				this.editData.timeWindow.ranges = (ranges || []).map(item => ({
					start: item.start,
					end: item.end
				}));
				this.timeWindowPreset = 'custom';
			},
			removeTimeWindowRange(index) {
				this.editData.timeWindow.ranges.splice(index, 1);
				this.timeWindowPreset = 'custom';
			},
			handleTimeWindowModeChange() {
				if (this.editData.timeWindow.mode == 'daily') {
					this.editData.timeWindow.days = [];
					this.editData.timeWindow.daysOfMonth = [];
				}
				this.timeWindowPreset = 'custom';
			},
			normalizeTimeWindowPoint(value) {
				const text = `${value || ''}`.trim();
				const match = text.match(/^(\d{1,2}):(\d{1,2})$/);
				if (!match) {
					return text;
				}
				const hour = Number(match[1]);
				const minute = Number(match[2]);
				if (Number.isNaN(hour) || Number.isNaN(minute) || minute > 59 || hour > 24 || (hour == 24 && minute != 0)) {
					return text;
				}
				return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
			},
			formatTimeWindowPoint(range, key) {
				range[key] = this.normalizeTimeWindowPoint(range[key]);
				this.timeWindowPreset = 'custom';
			},
			isValidTimeWindowPoint(value) {
				return /^([01]\d|2[0-3]):[0-5]\d$/.test(`${value || ''}`) || `${value || ''}` == '24:00';
			},
			validateTimeWindow(config) {
				if (!config || !Array.isArray(config.ranges) || config.ranges.length == 0) {
					this.$message.error('时间段调用至少需要一个同步时间段');
					return false;
				}
				if (config.mode == 'week' && (!config.days || config.days.length == 0)) {
					this.$message.error('按星期执行时，请至少选择一个星期项');
					return false;
				}
				if (config.mode == 'day' && (!config.daysOfMonth || config.daysOfMonth.length == 0)) {
					this.$message.error('按日期执行时，请至少选择一天');
					return false;
				}
				for (let item of config.ranges) {
					item.start = this.normalizeTimeWindowPoint(item.start);
					item.end = this.normalizeTimeWindowPoint(item.end);
					if (!item.start || !item.end || item.start == item.end) {
						this.$message.error('每个时间段都需要填写不同的开始和结束时间');
						return false;
					}
					if (!this.isValidTimeWindowPoint(item.start) || !this.isValidTimeWindowPoint(item.end)) {
						this.$message.error('时间格式应为 HH:mm，例如 23:03；最大只支持到 24:00');
						return false;
					}
				}
				return true;
			},

			destinationList(row) {
				return row && row.dstPath ? row.dstPath.split(':').filter(Boolean) : [];
			},
			excludeList(row) {
				return row && row.exclude ? row.exclude.split(':').filter(Boolean) : [];
			},
			cacheText(useCache, interval) {
				return `${useCache == 0 ? '不使用缓存' : '使用缓存'} / ${interval || 0} 秒`;
			},
			getJobList(silent = false) {
				const loadToken = !silent && !this.hasLoaded ? this.loadingController.start() : 0;
				jobGetJob(this.params).then(res => {
					this.hasLoaded = true;
					this.jobData = res.data;
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else if (!silent) {
						this.loading = false;
					}
				}).catch(err => {
					this.hasLoaded = true;
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else if (!silent) {
						this.loading = false;
					}
				})
			},
			startJobStatusRefresh() {
				this.jobRefreshTimer = setInterval(() => {
					if (!this.editShow && !this.loading) {
						this.getJobList(true);
					}
				}, 5000);
			},
			jobRunning(row) {
				return !!(row && row.runningTask);
			},
			runningTaskText(row) {
				const num = row && row.runningTaskNum ? row.runningTaskNum : {};
				const wait = num.wait || 0;
				const running = num.running || 0;
				const success = num.success || 0;
				if (wait || running || success) {
					return `运行 ${running} / 等待 ${wait} / 完成 ${success}`;
				}
				return row && row.runningTaskScanFinish ? '正在收尾' : '正在扫描';
			},
			selectPath(isSrc) {
				this.cuIsSrc = isSrc;
				this.$refs.pathSelect.show();
			},
			getOpenListList() {
				openlistGet().then(res => {
					this.openlistList = res.data;
				})
			},
			toCron() {
				window.open('https://dr34m.cn/2024/08/newpost-58/', '_blank');
			},
			toIgnore() {
				window.open('https://dr34m.cn/2024/09/newpost-60/', '_blank');
			},
			putJob(row, pause = null) {
				if (row.enable != 1 && pause !== false) {
					this.$message.error('如需手动执行，请先启用作业');
					return
				}
				this.btnLoading = true;
				jobPut({
					id: row.id,
					pause: pause
				}).then(res => {
					this.btnLoading = false;
					this.$message({
						message: res.msg,
						type: 'success'
					});
					if (pause !== false) {
						this.detail(row.id);
					} else {
						this.getJobList();
					}
				}).catch(err => {
					this.btnLoading = false;
				})
			},
			disableJobShow(row, disableIsDel) {
				this.disableIsDel = disableIsDel;
				this.disableCu.id = row.id;
				this.disableShow = true;
			},
			editJobShow(row) {
				if (row.enable && row.isCron != 2) {
					this.$message.error('禁用作业后才能编辑');
					return
				}
				if (this.openlistList.length == 0) {
					this.getOpenListList();
				}
				this.editData = JSON.parse(JSON.stringify(row));
				this.editData.enable = this.editData.enable ? 1 : 0;
				this.editData.dstPath = this.editData.dstPath.split(':');
				this.editData.timeWindow = this.normalizeTimeWindow(this.editData.timeWindow);
				this.refreshTimeWindowPreset();
				this.refreshCronPreset();
				if (this.editData.exclude) {
					this.editData.exclude = this.editData.exclude.split(':');
				} else {
					this.editData.exclude = [];
				}
				this.editShow = true;

			},
			addShow() {
				if (this.openlistList.length == 0) {
					this.getOpenListList();
				}
				let editData = {
					enable: 1,
					remark: '',
					srcPath: '',
					dstPath: [],
					openlistId: null,
					useCacheT: 1,
					scanIntervalT: 1,
					useCacheS: 0,
					scanIntervalS: 0,
					method: 0,
					interval: 1440,
					isCron: 2,
					timeWindow: this.quickTimeWindowConfig('night'),
					exclude: []
				}
				this.cronList.forEach(item => {
					editData[item.label] = null;
				})
				this.editData = editData;
				this.timeWindowPreset = 'night';
				this.cronPreset = 'custom';
				this.editShow = true;

			},
			closeShow() {
				this.editShow = false;
			},
			closeDisableShow() {
				this.disableShow = false;
				this.disableCu = {
					id: null,
					pause: true
				};
			},
			addExclude(value) {
				if (value != null && value != '') {
					this.editData.exclude.push(value);
				}
			},
			delExclude(index) {
				this.editData.exclude.splice(index, 1);
			},
			delDstPath(index) {
				this.editData.dstPath.splice(index, 1);
			},
			submit() {
				this.$refs.jobEditorDialog.validate((valid) => {
					if (valid) {
						let postData = JSON.parse(JSON.stringify(this.editData));
						for (let i in postData) {
							if (postData[i] === '') {
								postData[i] = null;
							}
						}
						if (postData.isCron == 0 && postData.interval == null) {
							this.$message.error("选择间隔方式时，间隔必填");
							return
						}
						if (postData.isCron == 3) {
							postData.timeWindow = this.normalizeTimeWindow(postData.timeWindow);
							if (!this.validateTimeWindow(postData.timeWindow)) {
								return
							}
						} else {
							postData.timeWindow = null;
						}
						if (postData.isCron == 1) {
							let flag = 0;
							this.cronList.forEach(item => {
								if (postData[item.label] != null && postData[item.label] !== '') {
									flag += 1;
								}
							})
							if (flag == 0) {
								this.$message.error('选择 cron 方式时，请使用生成器或高级字段，至少配置一项计划');
								return
							}
						}
						if (postData.timeWindow) {
							postData.timeWindow = JSON.stringify(postData.timeWindow);
						}
						delete postData.cronPreset;
						delete postData.timeWindowPreset;
						postData.dstPath = postData.dstPath.join(':');
						postData.exclude = postData.exclude.join(':');
						this.editLoading = true;
						jobPost(postData).then(res => {
							this.editLoading = false;
							this.$message({
								message: res.msg,
								type: 'success'
							});
							this.closeShow();
							this.getJobList();
						}).catch(err => {
							this.editLoading = false;
						})
					}
				})
			},
			submitPath(path) {
				if (this.cuIsSrc) {
					this.editData.srcPath = path;
				} else {
					if (this.editData.dstPath.includes(path)) {
						this.$message({
							message: '该目录已存在',
							type: 'error'
						});
					} else {
						this.editData.dstPath.push(path);
					}
				}
			},
			submitDisable() {
				this.editLoading = true;
				if (this.disableIsDel) {
					jobDelete(this.disableCu).then(res => {
						this.editLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getJobList();
						this.closeDisableShow();
					}).catch(err => {
						this.editLoading = false;
					})
				} else {
					jobPut(this.disableCu).then(res => {
						this.editLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getJobList();
						this.closeDisableShow();
					}).catch(err => {
						this.editLoading = false;
					})
				}
			},
			detail(jobId) {
				this.$router.push({
					path: '/home/task',
					query: {
						jobId
					}
				})
			},
			handleSizeChange(val) {
				this.params.pageSize = val;
				this.getJobList();
			},
			handleCurrentChange(val) {
				this.params.pageNum = val;
				this.getJobList();
			},
		}
	}

</script>

<style lang="scss">
	.home {
		width: 100%;
		height: 100%;
		padding: clamp(14px, 2.4vw, 28px);
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
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

			.top-box-left {
				display: flex;
				align-items: center;
			}
		}

		.pathList {
			display: flex;
			flex-wrap: wrap;
			flex-shrink: 0;

			.pathBox {
				font-size: 14px;
				padding: 2px 6px;
				margin: 2px 0;
				margin-right: 6px;
				border-radius: 3px;
				word-break: break-all;
				max-width: 100%;
			}

			.pathBox:last-child {
				margin-right: 0;
			}
		}

		.action-buttons {
			display: flex;
			align-items: center;
			justify-content: center;
			flex-wrap: wrap;
			gap: 4px;
		}

		.expand-actions {
			display: flex;
			flex-wrap: wrap;
			gap: 6px;
		}

		.table-wrapper {
			width: 100%;
			flex: 1;
			min-height: 400px;
			overflow: hidden;
			display: flex;
			flex-direction: column;
			position: relative;
		}

		.page {
			margin-top: 24px;
			display: flex;
			justify-content: right;
			flex-shrink: 0;
		}

		.form-box {
			padding: 16px 12px;
			min-height: 100px;

			.form-box-item {
				display: flex;
				align-items: flex-start;
				margin-bottom: 16px;
				padding: 6px 0;
				min-height: 28px;

				.form-box-item-label {
					font-size: 13px;
					width: 100px;
					text-align: right;
					margin-right: 12px;
					color: var(--text-muted, #606266);
					flex-shrink: 0;
					padding-top: 4px;
					line-height: 1.5;
				}

				.form-box-item-value {
					flex: 1;
					font-size: 13px;
					color: var(--text-primary, #303133);
					word-break: break-all;
					line-height: 1.6;
					min-width: 0;
					padding-top: 2px;
				}
			}
		}

		// 琛ㄦ牸灞曞紑琛屾牱寮忎紭鍖?
		::v-deep .el-table__expanded-cell {
			padding: 0 !important;
			background-color: var(--bg-secondary, #fafafa);
		}

		::v-deep .el-table__expanded-cell[class*="cell"] {
			padding: 0 !important;
		}
	}

	.label_width {
		width: 100%;
		max-width: 100%;
		box-sizing: border-box;

		.label-list-box {
			display: flex;
			align-items: center;
			flex-wrap: wrap;
			min-height: 42px;

			.label-list-item {
				display: flex;
				align-items: center;
				margin: 4px 0;
				margin-right: 12px;
				flex-shrink: 0;

				.label-list-item-left {
					border-radius: 3px;
					padding: 0 6px;
					line-height: 20px;
					margin-right: -4px;
				}

				.el-button {
					border-radius: 0 3px 3px 0;
				}
			}
		}

		.to-link {
			color: var(--link-color);
			text-decoration: underline;
			cursor: pointer;
			transition: color 0.2s ease;
			
			&:hover {
				color: var(--link-hover-color);
			}
		}

		.option-main {
			display: inline-block;
			margin-right: 16px;
			max-width: calc(100% - 100px);
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
			vertical-align: top;
		}

		.option-desc {
			float: right;
			color: var(--desc-text-color, #909399);
			font-size: 13px;
		}

		.method-warning-wrapper {
			margin-bottom: 18px;
		}

		.method-warning {
			margin: 0;
			color: var(--danger-color, #f56c6c);
			font-weight: bold;
			display: block;
			padding: 12px 16px;
			background-color: rgba(245, 108, 108, 0.1);
			border-left: 4px solid var(--danger-color, #f56c6c);
			border-radius: 4px;
			line-height: 1.6;
		}

		.interval-tip-wrapper {
			margin-bottom: 18px;
		}

	.error-message {
		color: var(--danger-color);
		font-weight: bold;
		text-align: center;
		font-size: 20px;
	}

	// 鍚敤寮€鍏虫牱寮?
	.enable-switch-wrapper {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
		position: relative;
		z-index: 1;

		.enable-disabled-tip {
			color: var(--text-secondary, #909399);
			font-size: 12px;
		}
	}

	::v-deep .light-switch {
		position: relative;
		z-index: 10;
		pointer-events: auto !important;

		.el-switch__core {
			width: 60px !important;
			height: 30px !important;
			border-radius: 15px !important;
			background-color: #dcdfe6 !important;
			border: 2px solid #dcdfe6 !important;
			transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
			position: relative;
			box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
			cursor: pointer !important;
			pointer-events: auto !important;
			z-index: 10;

			&::after {
				width: 26px !important;
				height: 26px !important;
				border-radius: 50% !important;
				background-color: #ffffff !important;
				box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
				transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
				left: 2px !important;
				top: 2px !important;
				position: absolute;
				pointer-events: none;
				z-index: 11;
			}

			&::before {
				content: '';
				position: absolute;
				width: 100%;
				height: 100%;
				border-radius: 15px;
				background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
				opacity: 0;
				transition: opacity 0.3s ease;
				left: 0;
				top: 0;
				pointer-events: none;
				z-index: 1;
			}
		}

		&.is-checked .el-switch__core {
			background-color: #67c23a !important;
			border-color: #67c23a !important;
			box-shadow: 0 0 12px rgba(103, 194, 58, 0.5), inset 0 0 10px rgba(255, 255, 255, 0.2) !important;

			&::after {
				left: 32px !important;
				background-color: #ffffff !important;
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
				transform: scale(1.05);
			}

			&::before {
				opacity: 1;
			}
		}

		&:not(.is-checked) .el-switch__core:hover {
			background-color: #c0c4cc !important;
			border-color: #c0c4cc !important;
		}

		&.is-checked .el-switch__core:hover {
			background-color: #5daf34 !important;
			border-color: #5daf34 !important;
			box-shadow: 0 0 16px rgba(103, 194, 58, 0.6), inset 0 0 10px rgba(255, 255, 255, 0.2) !important;
		}

		.el-switch__label {
			color: var(--text-primary, #303133);
			font-size: 14px;
			font-weight: 500;
			transition: color 0.3s ease;
			margin-left: 8px;
			pointer-events: none;

			&.is-active {
				color: #67c23a;
			}
		}

		&.is-disabled {
			opacity: 0.6;
			cursor: not-allowed !important;
			pointer-events: none !important;

			.el-switch__core {
				cursor: not-allowed !important;
				pointer-events: none !important;
			}
		}
	}

	// 纭繚琛ㄥ崟椤瑰唴瀹逛笉鎷︽埅寮€鍏崇偣鍑?
	::v-deep .el-form-item[prop="enable"] {
		.el-form-item__content {
			overflow: visible !important;
			pointer-events: auto !important;
		}
	}
}

	.label_width_2 {
		width: 600px;
	}

	.exclude-item {
		margin-right: 6px;
		padding: 0 2px;
		border-radius: 3px;
	}

	.exclude-item:last-child {
		margin-right: 0;
	}

	// 缁夎濮╃粩顖炩偓鍌炲帳
	@media (max-width: 768px) {
		.home {
			padding: 12px;

			.top-box {
				flex-wrap: wrap;
				gap: 8px;
				margin-bottom: 12px;

				.top-box-left {
					width: 100%;
					justify-content: flex-start;
					gap: 8px;
					
					.el-button {
						font-size: 12px;
						padding: 8px 12px;
						flex: 1;
						min-width: 0;
					}
				}

				.top-box-title {
					font-size: 16px;
					width: 100%;
					text-align: center;
					order: -1;
				}
			}

			.form-items-wrapper {
				grid-template-columns: 1fr !important;
				gap: 0 !important;
			}

			.method-warning-wrapper {
				margin-bottom: 16px;
			}

			.method-warning {
				margin: 0;
				font-size: 13px;
				width: 100%;
				line-height: 1.5;
				padding: 10px 12px;
				background-color: rgba(245, 108, 108, 0.1);
				border-left: 3px solid var(--danger-color, #f56c6c);
				border-radius: 4px;
			}

			.interval-tip-wrapper {
				margin-bottom: 16px;
			}

			.pathList {
				.pathBox {
					font-size: 12px;
					padding: 2px 4px;
					margin: 2px;
					max-width: calc(100% - 4px);
				}
			}

			.action-buttons {
				flex-direction: column;
				width: 100%;
				gap: 6px;

				.mobile-button {
					width: 100%;
					margin: 0;
				}
			}

			.expand-actions {
				flex-direction: column;
				width: 100%;

				.el-button {
					width: 100%;
					margin: 0 0 6px 0;
				}
			}

			.form-box {
				padding: 12px 8px;
				min-height: 80px;

				.form-box-item {
					flex-direction: column;
					align-items: flex-start;
					margin-bottom: 16px;
					min-height: 32px;
					padding: 8px 0;

					.form-box-item-label {
						width: 100%;
						text-align: left;
						margin-right: 0;
						margin-bottom: 8px;
						font-weight: 500;
						padding-top: 0;
						line-height: 1.5;
					}

					.form-box-item-value {
						width: 100%;
						padding-top: 0;
						line-height: 1.6;
					}
				}
			}

			// 绉诲姩绔〃鏍煎睍寮€琛屼紭鍖?
			::v-deep .el-table__expanded-cell {
				padding: 0 !important;
			}

			.table-wrapper {
				margin: 0 -12px;
				padding: 0 12px;
				min-height: 300px;
				flex: 1;
			}

			.page {
				margin-top: 16px;
				justify-content: center;
				overflow-x: auto;
			}

			// 缁夎濮╃粩顖濐唨 label_width 娑撳秹妾洪崚璺侯啍鎼达讣绱濋悽杈╁煑鐎圭懓娅掗幒褍鍩?
			.label_width {
				width: 100% !important;
				max-width: 100% !important;
				box-sizing: border-box;
				overflow: visible;
				display: block;

				.el-input,
				.el-select,
				.el-input-group {
					width: 100% !important;
					max-width: 100% !important;
					box-sizing: border-box;
					display: block;
				}

				.el-select {
					display: block !important;
					width: 100% !important;
					
					.el-input {
						width: 100% !important;
						max-width: 100% !important;
						display: block !important;
						
						.el-input__inner {
							width: 100% !important;
							max-width: 100% !important;
							box-sizing: border-box !important;
						}
					}
				}

				.el-input-group {
					display: flex !important;
					width: 100% !important;

					.el-input {
						flex: 1;
						min-width: 0;
					}
				}
			}

			.label_width_2 {
				width: 100% !important;
				max-width: 100%;
				box-sizing: border-box;
			}
		}

		::v-deep .table-wrapper .el-table {
			font-size: 12px;
			display: flex;
			flex-direction: column;
			height: 100% !important;
			max-height: 100% !important;

			.el-table__header-wrapper {
				flex-shrink: 0;
			}

			.el-table__body-wrapper {
				flex: 1;
				overflow-y: auto;
				overflow-x: auto;
				-webkit-overflow-scrolling: touch;
				min-height: 0;
				max-height: 100%;
			}

			.el-table__cell {
				padding: 8px 4px;
			}

			.el-table__header-wrapper {
				.el-table__header {
					th {
						padding: 8px 4px;
						font-size: 12px;
						word-break: break-word;
					}
				}
			}

			.el-table__body-wrapper {
				.el-table__row {
					td {
						padding: 8px 4px;
						word-break: break-word;
					}
				}
			}

			// 绉诲姩绔搷浣滃垪浼樺寲
			.action-column {
				.cell {
					padding: 4px 0;
				}
			}

			// 鐞涖劍鐗搁崚妤€顔旀导妯哄
			.el-table__column--selection {
				width: 40px !important;
			}

			// 鐏炴洖绱戠悰灞藉礋閸忓啯鐗搁弽宄扮础
			.el-table__expanded-cell {
				padding: 0 !important;
				background-color: var(--bg-secondary, #fafafa);
			}
		}

		.form-items-wrapper {
			display: flex;
			flex-direction: column;
			gap: 0;

			// PC缁旑垯濞囬悽鈺ex-wrap鐎圭偟骞囨稉銈呭灙鐢啫鐪?
			@media (min-width: 769px) {
				flex-direction: row;
				flex-wrap: wrap;
				gap: 0 24px;
			}

			// 鍏ㄥ琛ㄥ崟椤癸細鐢ㄤ簬鎺掗櫎椤广€佽鍛婁俊鎭瓑鍐呭
			.form-item-full-width {
				width: 100%;

				@media (min-width: 769px) {
					flex: 0 0 100% !important;
					width: 100% !important;
					max-width: 100% !important;
				}
			}

			// 鐩存帴瀛愬厓绱?el-form-item 鍙備笌 flex 甯冨眬
			> .el-form-item {
				margin-bottom: 18px;
				width: 100%;

				// PC 绔瘡涓〃鍗曢」鍗犱竴鍗婂搴︼紝褰㈡垚鍙屽垪甯冨眬
				@media (min-width: 769px) {
					margin-bottom: 14px;
					flex: 0 0 calc(50% - 12px) !important; // 鎵ｆ帀涓€鍗?gap
					width: calc(50% - 12px) !important;
					max-width: calc(50% - 12px) !important;
					box-sizing: border-box;
				}
			}

			// 浣跨敤娣卞害閫夋嫨鍣紝纭繚 Element UI 鐨?form-item 姝ｅ父鍙備笌 flex 甯冨眬
			::v-deep .el-form-item {
				margin-bottom: 18px;
				width: 100%;

				@media (min-width: 769px) {
					margin-bottom: 14px;
					flex: 0 0 calc(50% - 12px) !important;
					width: calc(50% - 12px) !important;
					max-width: calc(50% - 12px) !important;
					box-sizing: border-box;
				}
			}

			// 鍏ㄥ琛ㄥ崟椤圭殑娣卞害閫夋嫨鍣ㄨ鐩?
			::v-deep .form-item-full-width {
				@media (min-width: 769px) {
					flex: 0 0 100% !important;
					width: 100% !important;
					max-width: 100% !important;
				}
			}
		}

		.method-warning-wrapper,
		.interval-tip-wrapper {
			width: 100%;
			margin-bottom: 18px;

			// PC缁旑垯绱崠鏍电窗閸戝繐鐨梻纾嬬獩
			@media (min-width: 769px) {
				margin-bottom: 14px;
				width: 100%;
				flex: 0 0 100%;
			}
		}

		// PC缁旑垯绱崠鏍€冮崡鏇€嶉弽鍥╊劮鐎硅棄瀹?
		@media (min-width: 769px) {

			::v-deep .el-form {
				.el-form-item:not(.form-item-full-width) {
					.el-form-item__label {
						width: 120px !important;
						flex-shrink: 0;
					}
				}
			}
		}

		// 缁熶竴璺緞閫夋嫨鍣ㄦ牱寮忥紝浣跨敤鏇撮珮浼樺厛绾ц鐩栭粯璁ゆ牱寮?
		.home .path-list-wrapper,
		.path-list-wrapper {
			display: flex;
			flex-direction: column;
			gap: 10px;
			width: 100%;
			max-width: 100%;
			box-sizing: border-box;

			.path-item {
				width: 100%;
				max-width: 100%;
				margin-bottom: 0;
				box-sizing: border-box;
			}

			.path-item-content {
				display: flex !important;
				align-items: center !important;
				justify-content: flex-start !important;
				padding: 12px 16px !important;
				border-radius: 8px !important;
				min-height: 44px !important;
				box-sizing: border-box !important;
				width: 100% !important;
				max-width: 100% !important;
				position: relative !important;
				transition: all 0.18s ease !important;
				// PC 绔娇鐢ㄤ富棰樺彉閲忥紝鍏煎浜壊涓庢殫鑹蹭富棰?
				border: 1px solid var(--border-color, #dcdfe6) !important;
				background-color: var(--bg-input, #f5f7fa) !important;

				&:hover {
					box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08) !important;
					transform: translateY(-1px) !important;
				}

				i.path-icon,
				.path-icon {
					flex-shrink: 0 !important;
					margin-right: 12px !important;
					font-size: 16px !important;
					color: var(--text-secondary, #606266) !important;
					display: inline-block !important;
					visibility: visible !important;
				}

				span.path-text,
				.path-text {
					flex: 1 !important;
					min-width: 0 !important;
					word-break: break-word !important;
					line-height: 1.6 !important;
					font-size: 14px !important;
					color: var(--text-primary, #303133) !important;
					overflow: hidden !important;
					text-overflow: ellipsis !important;
					display: -webkit-box !important;
					-webkit-line-clamp: 2 !important;
					line-clamp: 2 !important;
					-webkit-box-orient: vertical !important;
					max-height: 2.8em !important;
					visibility: visible !important;
					opacity: 1 !important;
					white-space: normal !important;
					padding-right: 8px !important;
					user-select: text !important;
				}

				.path-remove-btn {
					flex-shrink: 0 !important;
					padding: 6px 8px !important;
					margin-left: 10px !important;
					color: var(--danger-color, #f56c6c) !important;
					opacity: 0.9 !important;
					transition: all 0.16s ease !important;
					border-radius: 6px !important;
					background: transparent !important;

					&:hover {
						opacity: 1 !important;
						background-color: rgba(245, 108, 108, 0.08) !important;
					}
				}

				// 濠ф劗娲拌ぐ鏇熺壉瀵骏绱欓弮鐘插灩闂勩倖瀵滈柦顕嗙礆
				&.path-item-src {
					border: 1px solid #b3d8ff !important;
					background-color: #e6f2ff !important;

					i.path-icon,
					.path-icon {
						color: #409eff !important;
					}

					span.path-text,
					.path-text {
						color: var(--text-primary, #303133) !important;
						visibility: visible !important;
						opacity: 1 !important;
					}

					&:hover {
						border-color: #409eff !important;
						background-color: #d0e7ff !important;
						box-shadow: 0 6px 18px rgba(64, 158, 255, 0.12) !important;
					}
				}

				// 閻╊喗鐖ｉ惄顔肩秿閺嶅嘲绱?
				&.path-item-dst {
					border: 1px solid #c2e7b0 !important;
					background-color: #f0f9eb !important;

					i.path-icon,
					.path-icon {
						color: #67c23a !important;
					}

					span.path-text,
					.path-text {
						color: var(--text-primary, #303133) !important;
						visibility: visible !important;
						opacity: 1 !important;
					}

					&:hover {
						border-color: #67c23a !important;
						background-color: #e1f3d8 !important;
						box-shadow: 0 6px 18px rgba(103, 194, 58, 0.12) !important;
					}
				}
			}

		.path-select-btn {
			align-self: flex-start;
			margin-top: 0;
			max-width: 100%;
			box-sizing: border-box;

			i {
				margin-right: 6px;
			}
		}
		}

		// 閸忕厧顔愰弮褏娈戦弽宄扮础缁鎮?
		.path-select-wrapper {
			display: flex;
			flex-direction: column;
			gap: 8px;
			width: 100%;

			.path-text {
				word-break: break-all;
				line-height: 1.5;
			}

			.path-button {
				align-self: flex-start;
			}
		}

		.interval-tip {
			margin-left: 0;
			margin-top: 8px;
			display: block;
			width: 100%;
			font-size: 12px;
			color: var(--text-secondary, #606266);
		}

		// PC缁旑垰顕拠婵囶攱鐏炲懍鑵戦弽宄扮础
		::v-deep .dialog-center {
			margin: auto !important;
			top: 50% !important;
			transform: translateY(-50%) !important;
		}

		::v-deep .el-dialog {
			width: 95% !important;
			margin-top: 0 !important;
			margin-left: auto !important;
			margin-right: auto !important;
			margin-bottom: 0 !important;
			top: 15% !important;
			max-height: 90vh;
			display: flex;
			flex-direction: column;
			overflow: hidden;

			// PC 绔浐瀹氬脊绐楀搴?
			@media (min-width: 769px) {
				width: 1000px !important;
				margin-top: 0 !important;
				margin-left: auto !important;
				margin-right: auto !important;
				margin-bottom: 0 !important;
				top: 15% !important;
				max-height: 90vh;
			}

			.el-dialog__header {
				padding: 15px 20px 10px;
				flex-shrink: 0;
				font-size: 16px;
				color: var(--text-primary, #303133) !important;

				// PC 绔噺灏戝ご閮ㄥ唴杈硅窛
				@media (min-width: 769px) {
					padding: 12px 20px 8px;
				}
			}

			.el-dialog__body {
				padding: 15px;
				overflow-y: auto;
				overflow-x: hidden;
				flex: 1;
				min-height: 0;
				max-width: 100%;
				box-sizing: border-box;
				-webkit-overflow-scrolling: touch;
				color: var(--text-primary, #303133) !important;

				// PC 绔噺灏戝唴瀹瑰尯 padding锛屽苟浼樺寲婊氬姩鍖哄煙
				@media (min-width: 769px) {
					padding: 12px 20px;
					overflow-y: auto;
					max-height: calc(90vh - 110px); // 鎵ｆ帀 header 鍜?footer 楂樺害
				}
			}

			.el-dialog__footer {
				padding: 10px 20px 15px;
				flex-shrink: 0;
				border-top: 1px solid var(--border-light, #e4e7ed);
				display: flex;
				justify-content: center;
				gap: 12px;

				// PC缁旑垯绱崠鏍电窗閸戝繐鐨痯adding
				@media (min-width: 769px) {
					padding: 8px 20px 12px;
				}

				.el-button {
					flex: 1;
					max-width: 120px;
				}
			}
		}

		// 娣囶喖顦叉稉瀣閼挎粌宕熺搾鍛毉闂傤噣顣?
		::v-deep .el-select-dropdown {
			max-width: calc(95vw - 40px) !important;
			box-sizing: border-box;

			.el-select-dropdown__item {
				overflow: hidden !important;
				text-overflow: ellipsis;
				white-space: nowrap;
				max-width: 100% !important;
				box-sizing: border-box;
				padding: 0 20px !important;

				span {
					display: inline-block !important;
					overflow: hidden !important;
					text-overflow: ellipsis !important;
					white-space: nowrap !important;
					max-width: 100% !important;
					box-sizing: border-box;
				}

				span[style*="float"] {
					float: none !important;
					display: inline-block !important;
					max-width: calc(100% - 100px) !important;
					overflow: hidden !important;
					text-overflow: ellipsis !important;
					white-space: nowrap !important;
					vertical-align: top;
					margin-right: 16px !important;
					box-sizing: border-box;
				}

				.option-desc {
					float: right !important;
					max-width: 80px !important;
					overflow: hidden !important;
					text-overflow: ellipsis !important;
					white-space: nowrap !important;
				}
			}
		}

		// PC缁旑垽绱扮涵顔荤箽form-items-wrapper娑擃厾娈慺orm-item濮濓絿鈥橀弰鍓с仛
		@media (min-width: 769px) {
			.form-items-wrapper {
				// 绾喕绻歠orm-item閸愬懘鍎寸紒鎾寸€锝団€?
				::v-deep .el-form-item {
					display: flex !important;
					flex-direction: column !important;
					margin-bottom: 14px !important;
				}
			}
		}

		::v-deep .el-form {
			.el-form-item {
				margin-bottom: 18px;
				max-width: 100%;

				// PC缁旑垽绱扮涵顔荤箽flex鐢啫鐪悽鐔告櫏
				@media (min-width: 769px) {
					// 鐎硅棄瀹抽悽鐪唎rm-items-wrapper閹貉冨煑閿涘矁绻栭柌灞肩瑝鐠佸墽鐤嗛崶鍝勭暰width
				}

				.el-form-item__label {
					width: auto !important;
					text-align: left;
					padding-right: 12px;
					line-height: 32px;
					font-size: 14px;
					color: var(--text-primary, #303133) !important;
					white-space: nowrap;
				}

				// PC缁旑垯琚遍崚妤€绔风仦鈧弮璁圭礉閺嶅洨顒风€硅棄瀹崇紒鐔剁
				@media (min-width: 769px) {
					&:not(.form-item-full-width) {
						.el-form-item__label {
							width: 120px;
							flex-shrink: 0;
						}
					}
				}

				.el-form-item__content {
					margin-left: 0 !important;
					width: 100% !important;
					max-width: 100% !important;
					box-sizing: border-box;
					overflow: visible;
					position: relative;

					> * {
						max-width: 100% !important;
						box-sizing: border-box;
					}

					// 纭繚璺緞閫夋嫨鍣ㄦ牱寮忎笉琚鐩?
					.path-list-wrapper {
						.path-item-content {
							display: flex !important;
							visibility: visible !important;
							
							span.path-text,
							.path-text {
								display: -webkit-box !important;
								visibility: visible !important;
								opacity: 1 !important;
								color: #303133 !important;
							}

							i.path-icon,
							.path-icon {
								visibility: visible !important;
								opacity: 1 !important;
							}
						}
					}

					.el-input,
					.el-select,
					.el-input-group {
						width: 100% !important;
						max-width: 100% !important;
						box-sizing: border-box;
						display: block;

						.el-input__inner,
						.el-input-group__append,
						.el-input-group__prepend {
							box-sizing: border-box !important;
							max-width: 100% !important;
							width: 100% !important;
						}

						.el-input__inner {
							overflow: hidden;
							text-overflow: ellipsis;
							white-space: nowrap;
						}
					}

					.el-input-group {
						display: flex;
						width: 100% !important;
						max-width: 100% !important;

						.el-input {
							flex: 1;
							min-width: 0;
							max-width: 100% !important;
						}

						.el-input-group__append,
						.el-input-group__prepend {
							flex-shrink: 0;
						}
					}

					.el-select {
						width: 100% !important;
						max-width: 100% !important;

						.el-input {
							width: 100% !important;
							max-width: 100% !important;
						}
					}

					.label_width {
						width: 100% !important;
						max-width: 100% !important;
						box-sizing: border-box;
						overflow: visible;
						position: relative;
						display: block;

						.el-input,
						.el-input-group {
							width: 100% !important;
							max-width: 100% !important;
							display: block;
						}

						.el-select {
							width: 100% !important;
							max-width: 100% !important;
							display: block !important;
							
							.el-input {
								width: 100% !important;
								max-width: 100% !important;
								display: block !important;
								
								.el-input__inner {
									width: 100% !important;
									max-width: 100% !important;
									box-sizing: border-box !important;
								}
							}
						}

						.el-input-group {
							display: flex !important;
							width: 100% !important;

							.el-input {
								flex: 1;
								min-width: 0;
							}
						}
					}
				}
			}
		}

		.label-list-box {
			width: 100%;

			.label-list-item {
				width: 100%;
				margin-right: 0;
				margin-bottom: 8px;

				.label-list-item-left {
					flex: 1;
					min-width: 0;
					word-break: break-all;
				}
			}
		}

		.option-desc {
			display: none;
		}

		.option-main {
			max-width: 100%;
		}

		// 缁夎濮╃粩顖濈熅瀵板嫰鈧瀚ㄩ崳銊┾偓鍌炲帳
		.path-list-wrapper {
			gap: 8px;
			width: 100%;
			max-width: 100%;
			box-sizing: border-box;

			.path-item {
				width: 100%;
				max-width: 100%;
				box-sizing: border-box;
			}

			.path-item-content {
				padding: 8px 10px;
				min-height: 36px;
				width: 100%;
				max-width: 100%;
				box-sizing: border-box;

				.path-icon {
					font-size: 14px;
					margin-right: 8px;
					flex-shrink: 0;
				}

				.path-text {
					font-size: 12px;
					-webkit-line-clamp: 3;
					line-clamp: 3;
					max-height: 3.6em;
					padding-right: 4px;
					min-width: 0;
				}

				.path-remove-btn {
					padding: 2px 4px;
					font-size: 14px;
					margin-left: 4px;
					flex-shrink: 0;
				}
			}

			.path-select-btn {
				width: 100%;
				max-width: 100%;
				margin-top: 0;
				box-sizing: border-box;
			}
		}

		// 缁夎濮╃粩顖滀紖閸忓绱戦崗鎶解偓鍌炲帳
		.enable-switch-wrapper {
			width: 100%;

			::v-deep .light-switch {
				.el-switch__core {
					width: 50px !important;
					height: 26px !important;

					&::after {
						width: 22px !important;
						height: 22px !important;
					}
				}

				&.is-checked .el-switch__core::after {
					left: 26px !important;
				}

				.el-switch__label {
					font-size: 12px;
				}
			}

			.enable-disabled-tip {
				font-size: 11px;
				width: 100%;
				margin-top: 4px;
			}
		}
	}

	@media (max-width: 480px) {
		.home {
			padding: 8px;

			.top-box {
				.top-box-left {
					.el-button {
						font-size: 11px;
						padding: 6px 10px;
					}
				}

				.top-box-title {
					font-size: 14px;
				}
			}

			.pathList {
				.pathBox {
					font-size: 11px;
					padding: 1px 3px;
				}
			}

			.table-wrapper {
				margin: 0 -8px;
				padding: 0 8px;
				min-height: 250px;
				flex: 1;
			}

			::v-deep .el-table {
				font-size: 11px;

				.el-table__cell {
					padding: 6px 2px;
				}

				.el-table__header-wrapper {
					.el-table__header {
						th {
							padding: 6px 2px;
							font-size: 11px;
						}
					}
				}

				.el-table__body-wrapper {
					.el-table__row {
						td {
							padding: 6px 2px;
						}
					}
				}
			}

			.form-box {
				padding: 10px 6px;
				min-height: 70px;

				.form-box-item {
					margin-bottom: 14px;
					min-height: 30px;
					padding: 6px 0;

					.form-box-item-label {
						font-size: 12px;
						margin-bottom: 6px;
					}

					.form-box-item-value {
						font-size: 12px;
					}
				}
			}

			::v-deep .el-dialog {
				width: 98% !important;
				margin: 2vh auto 0 !important;

				.el-dialog__header {
					padding: 12px 15px 8px;
					font-size: 14px;
				}

				.el-dialog__body {
					padding: 12px;
				}

				.el-dialog__footer {
					padding: 8px 15px 12px;
					flex-direction: column;

					.el-button {
						width: 100%;
						max-width: 100%;
					}
				}
			}
		}
	}

	/* job-editor-workbench-polish */
	.job-editor-dialog {
		position: relative !important;
		top: auto !important;
		right: auto !important;
		bottom: auto !important;
		left: auto !important;
		width: min(1080px, calc(100vw - 56px)) !important;
		height: auto !important;
		max-height: calc(100vh - 12vh);
		margin: 6vh auto 0 !important;
		display: flex;
		flex-direction: column;
		border-radius: 34px !important;
		overflow: hidden;
		transform: translateZ(0);
	}

	.job-editor-dialog .el-dialog__header {
		flex: 0 0 auto;
		padding: 22px 72px 16px 30px !important;
		text-align: left;
	}

	.job-editor-dialog .el-dialog__title {
		font-size: 24px !important;
		letter-spacing: -.04em;
	}

	.job-editor-dialog .el-dialog__body {
		flex: 1 1 auto;
		min-height: 0;
		padding: 0 !important;
		overflow: hidden !important;
		max-height: none !important;
	}

	.job-editor-dialog .elform-box {
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		background:
			radial-gradient(circle at 95% 8%, var(--brand-soft), transparent 18rem),
			linear-gradient(180deg, transparent, color-mix(in srgb, var(--surface-soft) 72%, transparent));
	}

	.job-editor-hero {
		flex: 0 0 auto;
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 20px;
		padding: 22px 30px 20px;
		border-bottom: 1px solid var(--border-color);
		background: color-mix(in srgb, var(--surface-soft) 74%, transparent);
	}

	.job-editor-kicker {
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .26em;
		color: var(--brand);
	}

	.job-editor-title {
		margin-top: 8px;
		font-size: clamp(26px, 3vw, 42px);
		font-weight: 900;
		line-height: 1;
		letter-spacing: -.06em;
		color: var(--text-primary);
	}

	.job-editor-desc {
		margin-top: 12px;
		max-width: 620px;
		font-size: 14px;
		line-height: 1.7;
		color: var(--text-muted);
	}

	.job-editor-mode {
		flex: 0 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 86px;
		padding: 8px 12px;
		border: 1px solid var(--border-light);
		border-radius: 999px;
		background: var(--brand-soft);
		color: var(--brand-strong);
		font-size: 12px;
		font-weight: 900;
		white-space: nowrap;
	}

	.job-editor-dialog .elform-box > .el-form {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		overflow-x: hidden;
		overscroll-behavior: contain;
		-webkit-overflow-scrolling: touch;
		padding: 24px 30px 30px;
		box-sizing: border-box;
		scroll-padding: 24px;
	}

	.job-editor-dialog .form-items-wrapper {
		display: grid !important;
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		gap: 18px 22px !important;
		align-items: start;
	}

	.job-editor-dialog .form-items-wrapper > .el-form-item,
	.job-editor-dialog .time-window-config,
	.job-editor-dialog .method-warning-wrapper,
	.job-editor-dialog .interval-tip-wrapper {
		min-width: 0;
		margin: 0 !important;
		padding: 16px;
		border: 1px solid var(--border-color);
		border-radius: 22px;
		background: color-mix(in srgb, var(--bg-secondary) 72%, transparent);
		box-shadow: 0 10px 24px rgba(0, 0, 0, .05);
	}

	.job-editor-dialog .form-items-wrapper > .el-form-item:hover,
	.job-editor-dialog .time-window-config:hover {
		border-color: var(--border-light);
	}

	.job-editor-dialog .form-item-full-width,
	.job-editor-dialog .time-window-config,
	.job-editor-dialog .method-warning-wrapper,
	.job-editor-dialog .interval-tip-wrapper {
		grid-column: 1 / -1 !important;
	}

	.job-editor-dialog .time-window-config {
		display: grid;
		grid-template-columns: 1fr;
		gap: 16px;
	}

	.job-editor-dialog .time-window-config > .el-form-item,
	.job-editor-dialog .time-window-config > .interval-tip-wrapper {
		margin: 0 !important;
		padding: 0 !important;
		border: 0 !important;
		background: transparent !important;
		box-shadow: none !important;
	}

	.job-editor-dialog .el-form-item__label {
		float: none !important;
		display: block !important;
		width: auto !important;
		padding: 0 0 8px !important;
		line-height: 1.35 !important;
		font-size: 13px !important;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted) !important;
		text-align: left !important;
	}

	.job-editor-dialog .el-form-item__content {
		margin-left: 0 !important;
		line-height: normal;
	}

	.job-editor-dialog .path-list-wrapper {
		display: flex !important;
		flex-direction: column;
		gap: 10px;
	}

	.job-editor-dialog .path-item-content {
		min-height: 42px;
		padding: 10px 12px !important;
		border-radius: 16px !important;
		border: 1px solid var(--border-color);
		background: var(--surface-soft) !important;
		color: var(--text-primary) !important;
	}

	.job-editor-dialog .path-text {
		color: var(--text-primary) !important;
		font-size: 13px;
		line-height: 1.45;
	}

	.job-editor-dialog .path-select-btn {
		align-self: flex-start;
	}

	.job-editor-dialog .label-list-box {
		align-items: stretch;
		gap: 10px;
	}

	.job-editor-dialog .label-list-item {
		margin: 0 !important;
	}

	.job-editor-dialog .method-warning,
	.job-editor-dialog .interval-tip {
		border-radius: 18px;
		border-left-width: 0;
		line-height: 1.7;
	}

	.job-editor-dialog .el-dialog__footer {
		flex: 0 0 auto;
		position: relative;
		z-index: 2;
		padding: 16px 30px 22px !important;
		justify-content: flex-end !important;
		border-top: 1px solid var(--border-color) !important;
		background: linear-gradient(180deg, color-mix(in srgb, var(--bg-secondary) 86%, transparent), var(--bg-secondary)) !important;
		box-shadow: 0 -12px 32px rgba(0, 0, 0, .08);
	}

	.job-editor-dialog .el-dialog__footer .dialog-footer {
		display: flex;
		justify-content: flex-end;
		gap: 12px;
		width: 100%;
	}

	.job-editor-dialog .el-dialog__footer .el-button {
		min-width: 116px;
		max-width: none !important;
		flex: 0 0 auto !important;
	}

	@media (max-width: 1180px) {
		.job-editor-dialog {
			left: auto !important;
			right: auto !important;
			width: calc(100vw - 28px) !important;
			max-height: calc(100vh - 28px);
			margin: 14px auto 0 !important;
		}
	}

	@media (max-width: 768px) {
		.job-editor-dialog {
			inset: auto !important;
			width: calc(100vw - 20px) !important;
			height: auto !important;
			max-height: calc(100dvh - 20px);
			margin: 10px auto 0 !important;
			border-radius: 22px !important;
		}

		.job-editor-dialog .el-dialog__header {
			padding: 16px 58px 12px 18px !important;
		}

		.job-editor-dialog .job-editor-hero {
			padding: 16px 18px;
			gap: 12px;
		}

		.job-editor-title {
			font-size: 28px;
		}

		.job-editor-desc {
			font-size: 13px;
		}

		.job-editor-mode {
			display: none;
		}

		.job-editor-dialog .elform-box > .el-form {
			padding: 16px 14px 18px;
		}

		.job-editor-dialog .form-items-wrapper {
			grid-template-columns: 1fr !important;
			gap: 12px !important;
		}

		.job-editor-dialog .form-items-wrapper > .el-form-item,
		.job-editor-dialog .time-window-config,
		.job-editor-dialog .method-warning-wrapper,
		.job-editor-dialog .interval-tip-wrapper {
			padding: 14px;
			border-radius: 18px;
		}

		.job-editor-dialog .path-select-btn {
			width: 100%;
		}

		.job-editor-dialog .el-dialog__footer {
			padding: 12px 14px calc(12px + env(safe-area-inset-bottom)) !important;
		}

		.job-editor-dialog .el-dialog__footer .dialog-footer {
			gap: 10px;
		}

		.job-editor-dialog .el-dialog__footer .el-button {
			flex: 1 1 0 !important;
			min-width: 0;
		}
	}

	/* job-editor-path-color-guard */
	.job-editor-dialog .path-list-wrapper .path-item-content span.path-text,
	.job-editor-dialog .path-list-wrapper .path-item-content .path-text,
	.job-editor-dialog .el-form-item__content .path-list-wrapper .path-item-content span.path-text {
		color: var(--text-primary) !important;
	}

	.job-editor-dialog .path-list-wrapper .path-item-content i.path-icon,
	.job-editor-dialog .path-list-wrapper .path-item-content .path-icon,
	.job-editor-dialog .path-list-wrapper .path-item-content .path-remove-btn {
		color: var(--brand) !important;
	}

	/* manual-enable-tip-polish */
	.job-editor-dialog .enable-switch-wrapper {
		align-items: center;
		gap: 10px;
	}

	.job-editor-dialog .enable-disabled-tip {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		max-width: 100%;
		padding: 7px 10px;
		border: 1px solid var(--border-light);
		border-radius: 999px;
		background: var(--brand-soft);
		color: var(--brand-strong) !important;
		font-size: 12px !important;
		font-weight: 900;
		line-height: 1.35;
	}

	.job-editor-dialog .enable-disabled-tip i {
		font-size: 14px;
		flex: 0 0 auto;
	}

	.job-editor-dialog .enable-disabled-tip span {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@media (max-width: 768px) {
		.job-editor-dialog .enable-switch-wrapper {
			align-items: flex-start;
			flex-direction: column;
		}

		.job-editor-dialog .enable-disabled-tip {
			width: 100% !important;
			box-sizing: border-box;
			border-radius: 16px;
			padding: 9px 11px;
		}

		.job-editor-dialog .enable-disabled-tip span {
			white-space: normal;
		}
	}

	/* manual-enable-spacing-tune */
	.job-editor-dialog .enable-switch-wrapper .light-switch {
		margin-right: 4px;
	}

	.job-editor-dialog .enable-switch-wrapper .el-switch__label--left {
		margin-right: 8px;
	}

	.job-editor-dialog .enable-switch-wrapper .el-switch__label--right {
		margin-left: 8px;
	}

	.job-editor-dialog .enable-switch-wrapper .enable-disabled-tip {
		margin-left: 6px;
	}

	@media (max-width: 768px) {
		.job-editor-dialog .enable-switch-wrapper .enable-disabled-tip {
			margin-left: 0;
			margin-top: 2px;
		}
	}

	/* job-management-refresh */
	.home {
		gap: 18px;
		background:
			radial-gradient(circle at 92% 6%, var(--brand-soft), transparent 22rem),
			transparent;
	}











	.job-workbench {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		overflow-x: hidden;
		padding-right: 4px;
	}

	.job-card-list {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
		gap: clamp(14px, 2vw, 22px);
	}

	.job-card {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 16px;
		min-height: 360px;
		padding: 22px;
		border: 1px solid var(--border-color);
		border-radius: 30px;
		background: linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		overflow: hidden;
		transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease, opacity .22s ease;
	}

	.job-card::before {
		content: "";
		position: absolute;
		inset: 0 auto 0 0;
		width: 5px;
		background: linear-gradient(180deg, var(--brand), var(--accent));
	}

	.job-card:hover {
		transform: translateY(-3px);
		border-color: var(--border-light);
		box-shadow: var(--shadow-soft);
	}

	.job-card.is-disabled {
		opacity: .82;
	}

	.job-card.is-disabled::before {
		background: linear-gradient(180deg, var(--danger-color), var(--text-muted));
	}

	.job-card-topline,
	.job-card-header,
	.job-card-actions {
		position: relative;
		z-index: 1;
	}

	.job-card-topline {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}

	.job-status-pill,
	.job-method-pill,
	.job-id-badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 6px 10px;
		border-radius: 999px;
		font-size: 12px;
		font-weight: 900;
		line-height: 1;
		white-space: nowrap;
	}

	.job-status-pill {
		background: color-mix(in srgb, var(--success-color) 16%, transparent);
		color: var(--success-color);
	}

	.job-status-pill.is-disabled {
		background: color-mix(in srgb, var(--danger-color) 14%, transparent);
		color: var(--danger-color);
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 999px;
		background: currentColor;
		box-shadow: 0 0 0 5px color-mix(in srgb, currentColor 16%, transparent);
	}

	.job-method-pill,
	.job-id-badge {
		background: var(--brand-soft);
		color: var(--brand-strong);
	}

	.job-card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 14px;
	}

	.job-card-header h3 {
		margin: 0;
		font-size: clamp(22px, 2.4vw, 32px);
		line-height: 1.05;
		letter-spacing: -.05em;
		color: var(--text-primary);
		word-break: break-word;
	}

	.job-card-subtitle {
		margin-top: 9px;
		font-size: 13px;
		font-weight: 800;
		line-height: 1.5;
		color: var(--text-muted);
	}

	.job-path-panel {
		position: relative;
		z-index: 1;
		display: grid;
		grid-template-columns: 1fr;
		gap: 10px;
	}

	.job-path-block {
		padding: 13px 14px;
		border: 1px solid var(--border-color);
		border-radius: 18px;
		background: var(--surface-soft);
	}

	.path-label {
		display: flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted);
	}

	.path-label i {
		color: var(--brand);
	}

	.path-value {
		margin-top: 8px;
		font-size: 13px;
		line-height: 1.55;
		color: var(--text-primary);
		word-break: break-all;
	}

	.target-list,
	.job-exclude-row {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 9px;
	}

	.target-chip,
	.exclude-chip {
		max-width: 100%;
		padding: 6px 9px;
		border-radius: 999px;
		font-size: 12px;
		font-weight: 800;
		line-height: 1.25;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.target-chip {
		background: color-mix(in srgb, var(--accent) 16%, transparent);
		color: var(--text-primary);
	}

	.exclude-chip {
		background: color-mix(in srgb, var(--warning-color) 16%, transparent);
		color: var(--warning-color);
	}

	.target-chip.more,
	.exclude-chip.more {
		background: var(--brand-soft);
		color: var(--brand-strong);
	}

	.job-info-grid {
		position: relative;
		z-index: 1;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 10px;
	}

	.job-info-item {
		padding: 11px 12px;
		border-radius: 16px;
		background: color-mix(in srgb, var(--surface-soft) 76%, transparent);
		min-width: 0;
	}

	.job-info-item span {
		display: block;
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted);
	}

	.job-info-item strong {
		display: block;
		margin-top: 6px;
		font-size: 13px;
		line-height: 1.35;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.job-exclude-row {
		position: relative;
		z-index: 1;
		margin-top: -2px;
	}

	.job-card-actions {
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		gap: 8px;
		margin-top: auto;
	}

	.job-card-actions .el-button {
		width: 100%;
		min-width: 0;
		margin-left: 0 !important;
		padding-left: 8px;
		padding-right: 8px;
		white-space: nowrap;
	}

	.job-empty-state {
		min-height: 340px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		padding: 32px;
		border: 1px dashed var(--border-light);
		border-radius: 30px;
		background: var(--surface-soft);
		text-align: center;
	}

	.job-empty-mark {
		width: 76px;
		height: 76px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 28px;
		background: linear-gradient(135deg, var(--brand), var(--accent));
		color: #fffaf1;
		font-size: 34px;
	}

	.job-empty-title {
		font-size: 26px;
		font-weight: 900;
		color: var(--text-primary);
	}

	.job-empty-desc {
		max-width: 420px;
		line-height: 1.7;
		color: var(--text-muted);
	}

	.home > .page {
		margin-top: 0;
		padding: 2px 0 0;
		justify-content: flex-end;
	}

	@media (max-width: 1080px) {

	}

	@media (max-width: 768px) {
		.home {
			padding: 12px;
			gap: 14px;
			overflow-y: auto;
		}






		.job-workbench {
			overflow: visible;
			padding-right: 0;
		}

		.job-card-list {
			grid-template-columns: 1fr;
		}

		.job-card {
			min-height: auto;
			border-radius: 24px;
			padding: 18px;
		}

		.job-card-topline,
		.job-card-header {
			align-items: flex-start;
		}

		.job-info-grid {
			grid-template-columns: 1fr;
		}

		.job-card-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.home > .page {
			justify-content: center;
			padding-bottom: 8px;
		}
	}

	@media (max-width: 420px) {

		.job-card-actions {
			grid-template-columns: 1fr;
		}
	}

	/* job-edit-button-tune */
	.job-card-actions .job-edit-button {
		background: var(--surface-soft) !important;
		border-color: var(--border-light) !important;
		color: var(--text-secondary) !important;
		box-shadow: none !important;
	}

	.job-card-actions .job-edit-button:hover,
	.job-card-actions .job-edit-button:focus {
		background: var(--brand-soft) !important;
		border-color: var(--brand) !important;
		color: var(--brand-strong) !important;
	}
	/* job-management-compact-redesign */
	.home {
		gap: 12px;
	}











	.job-list-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 2px 4px 0;
		color: var(--text-muted);
	}

	.job-list-toolbar strong {
		margin-right: 10px;
		font-size: 16px;
		color: var(--text-primary);
	}

	.job-list-toolbar span,
	.job-list-hint {
		font-size: 12px;
		font-weight: 800;
	}

	.home .job-workbench {
		display: flex;
		flex-direction: column;
		gap: 10px;
		padding-right: 2px;
	}

	.home .job-card-list.job-compact-list {
		grid-template-columns: 1fr !important;
		gap: 10px !important;
	}

	.home .job-row-card {
		display: grid;
		grid-template-columns: 68px minmax(0, 1fr) 300px;
		align-items: stretch;
		gap: 14px;
		min-height: 0 !important;
		padding: 14px !important;
		border-radius: 22px !important;
	}

	.home .job-row-card::before {
		width: 4px;
	}

	.job-row-status {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 8px;
		border-radius: 16px;
		background: color-mix(in srgb, var(--surface-soft) 78%, transparent);
		font-size: 12px;
		font-weight: 900;
		color: var(--success-color);
	}

	.job-row-status.is-disabled {
		color: var(--danger-color);
	}

	.job-row-status .status-dot {
		width: 10px;
		height: 10px;
	}

	.job-row-main {
		position: relative;
		z-index: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 9px;
	}

	.job-row-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		min-width: 0;
	}

	.job-title-group {
		min-width: 0;
	}

	.job-title-group h3 {
		margin: 0;
		font-size: 19px;
		font-weight: 900;
		line-height: 1.2;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.job-row-badges {
		display: flex;
		align-items: center;
		gap: 8px;
		flex: 0 0 auto;
	}

	.job-route-line {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 28px minmax(0, 1.18fr);
		align-items: center;
		gap: 8px;
		padding: 9px 10px;
		border-radius: 16px;
		background: color-mix(in srgb, var(--surface-soft) 70%, transparent);
	}

	.job-route-node {
		min-width: 0;
	}

	.job-route-node span {
		display: flex;
		align-items: center;
		gap: 5px;
		margin-bottom: 5px;
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted);
	}

	.job-route-node strong {
		display: block;
		font-size: 13px;
		line-height: 1.35;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.job-route-arrow {
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--brand);
		font-weight: 900;
	}

	.target-list.compact {
		display: flex;
		flex-wrap: nowrap;
		gap: 6px;
		overflow: hidden;
	}

	.target-list.compact .target-chip {
		max-width: 180px;
		padding: 5px 8px;
		font-size: 12px;
	}

	.job-row-meta {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 6px;
	}

	.job-row-meta span {
		min-width: 0;
		padding: 7px 9px;
		border-radius: 12px;
		background: color-mix(in srgb, var(--surface-soft) 52%, transparent);
		font-size: 12px;
		font-weight: 800;
		line-height: 1.25;
		color: var(--text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.job-row-meta b {
		margin-right: 6px;
		font-size: 10px;
		letter-spacing: .06em;
		color: var(--text-muted);
	}

	.home .job-row-actions {
		position: relative;
		z-index: 1;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		align-content: center;
		gap: 7px;
		width: 300px;
		margin-top: 0;
	}

	.home .job-row-actions .el-button {
		height: 32px;
		min-height: 32px;
		padding-left: 6px;
		padding-right: 6px;
	}

	@media (max-width: 1180px) {


		.home .job-row-card {
			grid-template-columns: 56px minmax(0, 1fr);
		}

		.home .job-row-actions {
			grid-column: 1 / -1;
			width: 100%;
			grid-template-columns: repeat(5, minmax(0, 1fr));
		}
	}

	@media (max-width: 768px) {





		.home .job-row-card {
			grid-template-columns: 1fr;
			gap: 10px;
			padding: 14px !important;
		}

		.job-row-status {
			flex-direction: row;
			justify-content: flex-start;
			padding: 9px 12px;
		}

		.job-row-badges {
			flex-wrap: wrap;
		}

		.job-route-line {
			grid-template-columns: 1fr;
		}

		.job-route-arrow {
			display: none;
		}

		.job-row-meta {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.home .job-row-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 420px) {
	}

	/* job-running-state */
	.job-list-hint.has-running {
		padding: 6px 10px;
		border-radius: 999px;
		background: color-mix(in srgb, var(--brand-soft) 72%, transparent);
		color: var(--brand-strong);
	}

	.job-list-hint.has-running span {
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	.home .job-row-card.is-running {
		border-color: color-mix(in srgb, var(--brand) 42%, var(--border-color)) !important;
		box-shadow: 0 16px 42px rgba(219, 126, 62, .16), var(--shadow-card) !important;
	}

	.home .job-row-card.is-running::before {
		background: linear-gradient(180deg, var(--brand-strong), var(--accent));
	}

	.job-row-status.is-running {
		background: linear-gradient(145deg, var(--brand-soft), color-mix(in srgb, var(--surface-soft) 70%, transparent));
		color: var(--brand-strong);
	}

	.job-row-status.is-running .status-dot,
	.pulse-dot {
		background: var(--brand-strong);
		box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand) 36%, transparent);
		animation: running-pulse 1.4s ease-out infinite;
	}

	.job-running-pill {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		max-width: 260px;
		padding: 6px 10px;
		border-radius: 999px;
		background: var(--brand-soft);
		color: var(--brand-strong);
		font-size: 12px;
		font-weight: 900;
		line-height: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.pulse-dot {
		width: 7px;
		height: 7px;
		border-radius: 999px;
		flex: 0 0 auto;
	}


	@keyframes running-pulse {
		0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand) 38%, transparent); }
		70% { box-shadow: 0 0 0 8px transparent; }
		100% { box-shadow: 0 0 0 0 transparent; }
	}

	@media (max-width: 768px) {
		.job-running-pill {
			max-width: 100%;
		}
	}

	/* management-page-alignment-v2 */





	.home .job-row-card {
		grid-template-columns: 76px minmax(0, 1fr) 300px;
		align-items: center;
	}

	.home .job-row-status,
	.home .job-route-line,
	.home .job-row-meta span,
	.home .job-row-actions .el-button {
		border-radius: 14px;
	}

	.home .job-row-main {
		gap: 8px;
	}

	.home .job-row-actions {
		align-self: stretch;
		align-content: center;
	}

	@media (max-width: 1180px) {


		.home .job-row-card {
			grid-template-columns: 64px minmax(0, 1fr);
		}
	}

	@media (max-width: 768px) {


		.home .job-row-card {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 420px) {
	}


	/* time-window-call-mode */
	.job-editor-dialog .time-window-presets {
		display: flex;
		flex-direction: column;
		gap: 10px;
		min-width: 0;
	}

	.job-editor-dialog .time-window-preset-group {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.job-editor-dialog .time-window-preset-group.el-button-group {
		align-items: center;
	}

	.job-editor-dialog .time-window-preset-group.el-button-group::before,
	.job-editor-dialog .time-window-preset-group.el-button-group::after {
		display: none;
	}

	.job-editor-dialog .time-window-preset-group .el-button {
		position: relative;
		min-height: 34px;
		padding: 9px 14px;
		margin-left: 0 !important;
		border-radius: 999px !important;
		border: 1px solid rgba(124, 137, 165, 0.2) !important;
		background: rgba(255, 255, 255, 0.72) !important;
		color: var(--text-secondary) !important;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 6px 16px rgba(23, 37, 84, 0.04) !important;
		font-weight: 900;
		letter-spacing: 0.01em;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .time-window-preset-group .el-button:hover,
	.job-editor-dialog .time-window-preset-group .el-button:focus {
		border-color: rgba(73, 109, 222, 0.34) !important;
		background: rgba(255, 255, 255, 0.96) !important;
		color: var(--brand-strong) !important;
		transform: translateY(-1px);
	}

	.job-editor-dialog .time-window-preset-group .el-button--primary {
		border-color: rgba(73, 109, 222, 0.42) !important;
		background: linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 78%, #fff), var(--brand-soft)) !important;
		color: var(--brand-strong) !important;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7), 0 10px 22px rgba(73, 109, 222, 0.12) !important;
	}

	.job-editor-dialog .time-window-preset-group .el-button--primary::before {
		content: "";
		display: inline-block;
		width: 6px;
		height: 6px;
		margin-right: 7px;
		border-radius: 999px;
		background: var(--brand);
		vertical-align: 1px;
	}

	.job-editor-dialog .time-window-preset-hint {
		padding: 10px 12px;
		border-radius: 16px;
		background: var(--surface-soft);
		color: var(--text-secondary);
		font-size: 12px;
		font-weight: 800;
		line-height: 1.6;
	}

	.job-editor-dialog .cron-presets {
		gap: 12px;
	}

	.job-editor-dialog .cron-shortcuts,
	.job-editor-dialog .cron-builder {
		display: flex;
		flex-direction: column;
		gap: 12px;
		width: 100%;
		min-width: 0;
	}

	.job-editor-dialog .cron-shortcut-group,
	.job-editor-dialog .cron-mode-group {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		width: 100%;
	}

	.job-editor-dialog .cron-shortcut-group::before,
	.job-editor-dialog .cron-shortcut-group::after,
	.job-editor-dialog .cron-mode-group::before,
	.job-editor-dialog .cron-mode-group::after {
		display: none;
	}

	.job-editor-dialog .cron-shortcut-group .el-button,
	.job-editor-dialog .cron-mode-group .el-radio-button {
		margin: 0 !important;
	}

	.job-editor-dialog .cron-shortcut-group .el-button {
		min-height: 34px;
		padding: 9px 14px;
		border-radius: 999px !important;
		border: 1px solid rgba(124, 137, 165, 0.2) !important;
		background: rgba(255, 255, 255, 0.72) !important;
		color: var(--text-secondary) !important;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 6px 16px rgba(23, 37, 84, 0.04) !important;
		font-weight: 900 !important;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .cron-shortcut-group .el-button:hover,
	.job-editor-dialog .cron-shortcut-group .el-button:focus {
		border-color: rgba(73, 109, 222, 0.34) !important;
		background: rgba(255, 255, 255, 0.96) !important;
		color: var(--brand-strong) !important;
		transform: translateY(-1px);
	}

	.job-editor-dialog .cron-shortcut-group .el-button--primary {
		border-color: rgba(73, 109, 222, 0.42) !important;
		background: linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 78%, #fff), var(--brand-soft)) !important;
		color: var(--brand-strong) !important;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7), 0 10px 22px rgba(73, 109, 222, 0.1) !important;
	}

	.job-editor-dialog .cron-shortcut-hint,
	.job-editor-dialog .cron-builder-note,
	.job-editor-dialog .cron-builder-custom-tip,
	.job-editor-dialog .cron-preview-hint {
		color: var(--text-secondary);
		font-size: 12px;
		font-weight: 800;
		line-height: 1.6;
	}

	.job-editor-dialog .cron-builder {
		padding: 14px;
		border: 1px solid var(--border-color);
		border-radius: 22px;
		background:
			radial-gradient(circle at 92% 10%, rgba(73, 109, 222, .12), transparent 14rem),
			linear-gradient(145deg, rgba(255, 255, 255, .86), var(--surface-soft));
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, .7);
		box-sizing: border-box;
	}

	.job-editor-dialog .cron-builder-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		min-width: 0;
	}

	.job-editor-dialog .cron-builder-title {
		color: var(--text-primary);
		font-size: 16px;
		font-weight: 900;
		letter-spacing: -.02em;
	}

	.job-editor-dialog .cron-builder-desc {
		margin-top: 4px;
		color: var(--text-secondary);
		font-size: 13px;
		font-weight: 800;
		line-height: 1.5;
	}

	.job-editor-dialog .cron-advanced-toggle.el-button {
		flex: 0 0 auto;
		border-radius: 999px !important;
		border-color: rgba(124, 137, 165, 0.22) !important;
		background: rgba(255, 255, 255, .76) !important;
		color: var(--text-secondary) !important;
		font-weight: 900 !important;
	}

	.job-editor-dialog .cron-mode-group .el-radio-button__inner {
		min-height: 34px;
		padding: 9px 14px;
		border: 1px solid rgba(124, 137, 165, 0.2) !important;
		border-left: 1px solid rgba(124, 137, 165, 0.2) !important;
		border-radius: 999px !important;
		background: rgba(255, 255, 255, 0.72) !important;
		color: var(--text-secondary) !important;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 6px 16px rgba(23, 37, 84, 0.04) !important;
		font-weight: 900 !important;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .cron-mode-group .el-radio-button:first-child .el-radio-button__inner,
	.job-editor-dialog .cron-mode-group .el-radio-button:last-child .el-radio-button__inner {
		border-radius: 999px !important;
	}

	.job-editor-dialog .cron-mode-group .el-radio-button__inner:hover {
		border-color: rgba(73, 109, 222, 0.34) !important;
		background: rgba(255, 255, 255, 0.96) !important;
		color: var(--brand-strong) !important;
	}

	.job-editor-dialog .cron-mode-group .el-radio-button__orig-radio:checked + .el-radio-button__inner {
		border-color: rgba(73, 109, 222, 0.42) !important;
		border-left-color: rgba(73, 109, 222, 0.42) !important;
		background: linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 78%, #fff), var(--brand-soft)) !important;
		color: var(--brand-strong) !important;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7), 0 10px 22px rgba(73, 109, 222, 0.1) !important;
	}

	.job-editor-dialog .cron-builder-body {
		display: flex;
		flex-direction: column;
		gap: 10px;
		min-width: 0;
	}

	.job-editor-dialog .cron-builder-row {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 10px;
	}

	.job-editor-dialog .cron-builder-row.is-single {
		grid-template-columns: minmax(0, 1fr);
	}

	.job-editor-dialog .cron-builder-field {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
		padding: 10px;
		border: 1px solid rgba(124, 137, 165, 0.18);
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.7);
		box-sizing: border-box;
	}

	.job-editor-dialog .cron-builder-field.is-full {
		width: 100%;
	}

	.job-editor-dialog .cron-field-label {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		flex: 0 0 auto;
		min-width: 42px;
		height: 30px;
		padding: 0 10px;
		border-radius: 12px;
		background: var(--surface-soft);
		color: var(--text-secondary);
		font-size: 12px;
		font-weight: 900;
	}

	.job-editor-dialog .cron-field-suffix {
		flex: 0 0 auto;
		color: var(--text-muted);
		font-size: 12px;
		font-weight: 900;
	}

	.job-editor-dialog .cron-time-picker,
	.job-editor-dialog .cron-multi-select,
	.job-editor-dialog .cron-interval-input {
		flex: 1 1 auto;
		width: 100% !important;
		min-width: 0 !important;
	}

	.job-editor-dialog .cron-builder ::v-deep .el-input__inner {
		border-radius: 13px;
		border-color: rgba(124, 137, 165, 0.24);
		background: rgba(255, 255, 255, 0.88);
		font-weight: 800;
	}

	.job-editor-dialog .cron-preview-box {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 12px;
		border: 1px dashed rgba(73, 109, 222, 0.26);
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.62);
	}

	.job-editor-dialog .cron-preview-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
		color: var(--text-muted);
		font-size: 12px;
		font-weight: 800;
	}

	.job-editor-dialog .cron-preview-head strong {
		color: var(--text-primary);
		font-size: 14px;
		font-weight: 900;
	}

	.job-editor-dialog .cron-preview-list {
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		gap: 8px;
	}

	.job-editor-dialog .cron-preview-item {
		min-width: 0;
		padding: 9px 10px;
		border-radius: 14px;
		background: var(--surface-soft);
		border: 1px solid rgba(124, 137, 165, 0.16);
	}

	.job-editor-dialog .cron-preview-index {
		display: block;
		margin-bottom: 3px;
		color: var(--brand-strong);
		font-size: 11px;
		font-weight: 900;
	}

	.job-editor-dialog .cron-preview-time {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--text-primary);
		font-size: 12px;
		font-weight: 900;
	}

	.job-editor-dialog .cron-preview-empty {
		padding: 10px;
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.7);
		color: var(--text-muted);
		font-size: 12px;
		font-weight: 800;
		text-align: center;
	}

	.job-editor-dialog .cron-advanced-panel {
		display: contents;
	}

	.job-editor-dialog .cron-advanced-title {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		width: 100%;
		color: var(--text-secondary);
		font-size: 13px;
		font-weight: 800;
	}

	.job-editor-dialog .time-window-box,
	.job-editor-dialog .time-window-range-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
		min-width: 0;
	}

	.job-editor-dialog .time-window-mode,
	.job-editor-dialog .time-window-checks {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.job-editor-dialog .time-window-checks.is-days {
		max-height: 150px;
		overflow-y: auto;
		padding: 4px;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.45);
	}

	.job-editor-dialog .time-window-mode .el-radio-button,
	.job-editor-dialog .time-window-checks .el-checkbox-button {
		margin: 0 !important;
	}

	.job-editor-dialog .time-window-mode .el-radio-button__inner,
	.job-editor-dialog .time-window-checks .el-checkbox-button__inner {
		min-height: 34px;
		padding: 9px 14px;
		border-radius: 999px !important;
		border: 1px solid rgba(124, 137, 165, 0.2) !important;
		background: rgba(255, 255, 255, 0.72) !important;
		color: var(--text-secondary) !important;
		box-shadow: none !important;
		font-weight: 900;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .time-window-mode .el-radio-button:first-child .el-radio-button__inner,
	.job-editor-dialog .time-window-mode .el-radio-button:last-child .el-radio-button__inner,
	.job-editor-dialog .time-window-checks .el-checkbox-button:first-child .el-checkbox-button__inner,
	.job-editor-dialog .time-window-checks .el-checkbox-button:last-child .el-checkbox-button__inner {
		border-radius: 999px !important;
	}

	.job-editor-dialog .time-window-mode .el-radio-button__inner:hover,
	.job-editor-dialog .time-window-checks .el-checkbox-button__inner:hover {
		border-color: rgba(73, 109, 222, 0.34) !important;
		background: rgba(255, 255, 255, 0.96) !important;
		color: var(--brand-strong) !important;
		transform: translateY(-1px);
	}

	.job-editor-dialog .time-window-mode .el-radio-button__orig-radio:checked + .el-radio-button__inner,
	.job-editor-dialog .time-window-checks .el-checkbox-button.is-checked .el-checkbox-button__inner {
		background: linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 78%, #fff), var(--brand-soft)) !important;
		border-color: rgba(73, 109, 222, 0.42) !important;
		color: var(--brand-strong) !important;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7), 0 10px 22px rgba(73, 109, 222, 0.1) !important;
	}

	.job-editor-dialog .time-window-mode.el-radio-group .el-radio-button.el-radio-button--small .el-radio-button__inner,
	.job-editor-dialog .time-window-checks.el-checkbox-group .el-checkbox-button .el-checkbox-button__inner {
		border: 1px solid rgba(124, 137, 165, 0.2) !important;
		border-left: 1px solid rgba(124, 137, 165, 0.2) !important;
		border-radius: 999px !important;
		background: rgba(255, 255, 255, 0.72) !important;
		color: var(--text-secondary) !important;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 6px 16px rgba(23, 37, 84, 0.04) !important;
		font-weight: 900 !important;
	}

	.job-editor-dialog .time-window-mode.el-radio-group .el-radio-button.el-radio-button--small.is-active .el-radio-button__inner,
	.job-editor-dialog .time-window-checks.el-checkbox-group .el-checkbox-button.is-checked .el-checkbox-button__inner {
		border-color: rgba(73, 109, 222, 0.42) !important;
		border-left-color: rgba(73, 109, 222, 0.42) !important;
		background: linear-gradient(180deg, color-mix(in srgb, var(--brand-soft) 78%, #fff), var(--brand-soft)) !important;
		color: var(--brand-strong) !important;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7), 0 10px 22px rgba(73, 109, 222, 0.1) !important;
	}

	.job-editor-dialog .time-window-range {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto;
		align-items: center;
		gap: 12px;
		padding: 10px;
		border: 1px solid var(--border-color);
		border-radius: 18px;
		background: var(--surface-soft);
	}

	.job-editor-dialog .time-window-input {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		gap: 8px;
		min-width: 0;
	}

	.job-editor-dialog .time-window-input-label {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 42px;
		height: 32px;
		padding: 0 10px;
		border-radius: 12px;
		background: #fff;
		color: var(--text-secondary);
		font-size: 12px;
		font-weight: 900;
		border: 1px solid rgba(124, 137, 165, 0.18);
	}

	.job-editor-dialog .time-window-input ::v-deep .el-input__inner {
		height: 34px;
		border-radius: 12px;
		font-weight: 900;
		letter-spacing: 0.02em;
		text-align: center;
	}

	.job-editor-dialog .time-window-separator {
		font-size: 12px;
		font-weight: 900;
		color: var(--text-muted);
	}

	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain {
		border-radius: 999px !important;
		border: 1px solid rgba(220, 68, 68, 0.42) !important;
		background: rgba(255, 241, 241, 0.98) !important;
		color: #b83434 !important;
		font-weight: 900 !important;
		box-shadow: none !important;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain:hover,
	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain:focus {
		border-color: rgba(210, 48, 48, 0.56) !important;
		background: rgba(255, 226, 226, 1) !important;
		color: #9f2525 !important;
	}

	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain.is-disabled,
	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain.is-disabled:hover,
	.job-editor-dialog .time-window-delete.el-button.el-button--default.is-plain.is-disabled:focus {
		border-color: rgba(124, 137, 165, 0.14) !important;
		background: rgba(255, 255, 255, 0.58) !important;
		color: var(--text-muted) !important;
	}

	.job-editor-dialog .time-window-format-tip {
		margin-top: -2px;
		padding: 9px 12px;
		border: 1px dashed rgba(124, 137, 165, 0.3);
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.64);
		color: var(--text-secondary);
		font-size: 12px;
		font-weight: 800;
		line-height: 1.6;
	}

	.job-editor-dialog .time-window-mini-presets {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 10px 12px;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.72);
		border: 1px solid rgba(124, 137, 165, 0.18);
	}

	.job-editor-dialog .time-window-mini-label {
		font-size: 12px;
		font-weight: 900;
		color: var(--text-secondary);
	}

	.job-editor-dialog .time-window-mini-group {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.job-editor-dialog .time-window-mini-group ::v-deep .el-button {
		border-radius: 999px;
		border-color: rgba(124, 137, 165, 0.22);
		color: var(--text-secondary);
		font-weight: 800;
	}

	.job-editor-dialog .time-window-add {
		align-self: flex-start;
		border-radius: 999px;
		border: 1px solid rgba(124, 137, 165, 0.24);
		background: rgba(255, 255, 255, 0.84);
		color: var(--text-secondary);
		font-weight: 800;
		box-shadow: none;
		transition: all 0.18s ease;
	}

	.job-editor-dialog .time-window-add:hover,
	.job-editor-dialog .time-window-add:focus {
		border-color: rgba(73, 109, 222, 0.32);
		background: var(--brand-soft);
		color: var(--brand-strong);
	}

	@media (max-width: 768px) {
		.job-editor-dialog .time-window-preset-group,
		.job-editor-dialog .time-window-mode,
		.job-editor-dialog .time-window-checks,
		.job-editor-dialog .cron-shortcut-group,
		.job-editor-dialog .cron-mode-group {
			gap: 7px;
		}

		.job-editor-dialog .time-window-preset-group .el-button,
		.job-editor-dialog .time-window-mode .el-radio-button,
		.job-editor-dialog .time-window-checks .el-checkbox-button,
		.job-editor-dialog .cron-shortcut-group .el-button,
		.job-editor-dialog .cron-mode-group .el-radio-button {
			flex: 1 1 calc(50% - 7px);
			min-width: 0;
		}

		.job-editor-dialog .time-window-preset-group .el-button,
		.job-editor-dialog .time-window-mode .el-radio-button__inner,
		.job-editor-dialog .time-window-checks .el-checkbox-button__inner,
		.job-editor-dialog .cron-shortcut-group .el-button,
		.job-editor-dialog .cron-mode-group .el-radio-button__inner {
			width: 100%;
			padding: 9px 10px;
			text-align: center;
			white-space: nowrap;
		}

		.job-editor-dialog .time-window-checks.is-days .el-checkbox-button {
			flex-basis: calc(20% - 7px);
		}

		.job-editor-dialog .time-window-range {
			grid-template-columns: 1fr;
			align-items: stretch;
		}

		.job-editor-dialog .time-window-input {
			grid-template-columns: 54px minmax(0, 1fr);
		}

		.job-editor-dialog .time-window-separator {
			text-align: center;
		}

		.job-editor-dialog .time-window-delete {
			width: 100%;
		}

		.job-editor-dialog .time-window-add {
			width: 100%;
		}

		.job-editor-dialog .time-window-mini-group ::v-deep .el-button {
			width: calc(50% - 4px);
		}

		.job-editor-dialog .cron-builder {
			padding: 12px;
			border-radius: 18px;
		}

		.job-editor-dialog .cron-builder-head,
		.job-editor-dialog .cron-preview-head {
			flex-direction: column;
			align-items: stretch;
		}

		.job-editor-dialog .cron-advanced-toggle.el-button {
			width: 100%;
		}

		.job-editor-dialog .cron-builder-row,
		.job-editor-dialog .cron-preview-list {
			grid-template-columns: 1fr;
		}

		.job-editor-dialog .cron-builder-field {
			flex-wrap: wrap;
		}
	}

	/* job-editor-dialog-placement-v2: align with engine/notify dialogs */
	.job-editor-dialog {
		position: relative !important;
		top: auto !important;
		right: auto !important;
		bottom: auto !important;
		left: auto !important;
		width: min(1080px, calc(100vw - 56px)) !important;
		height: auto !important;
		max-height: calc(100vh - 12vh);
		margin: 6vh auto 0 !important;
		border-radius: 30px !important;
	}

	.job-editor-dialog .el-dialog__header {
		padding: 20px 70px 14px 28px !important;
	}

	.job-editor-dialog .el-dialog__body {
		max-height: calc(100vh - 6vh - 126px) !important;
	}

	.job-editor-dialog .elform-box {
		max-height: inherit;
	}

	.job-editor-dialog .elform-box > .el-form {
		max-height: calc(100vh - 6vh - 292px);
	}

	@media (min-width: 769px) {
		.job-editor-dialog .elform-box > .el-form {
			padding-bottom: 64px;
			scroll-padding-bottom: 64px;
		}

		.job-editor-dialog .el-dialog__footer {
			margin-top: 14px;
		}
	}

	@media (max-width: 1180px) {
		.job-editor-dialog {
			left: auto !important;
			right: auto !important;
			width: calc(100vw - 28px) !important;
			margin: 14px auto 0 !important;
			max-height: calc(100vh - 28px);
		}

		.job-editor-dialog .el-dialog__body {
			max-height: calc(100vh - 148px) !important;
		}

		.job-editor-dialog .elform-box > .el-form {
			max-height: calc(100vh - 316px);
		}
	}

	@media (max-width: 768px) {
		.job-editor-dialog {
			inset: auto !important;
			width: calc(100vw - 20px) !important;
			height: auto !important;
			box-sizing: border-box !important;
			max-height: calc(100dvh - 20px);
			margin: 10px auto 0 !important;
			border-radius: 22px !important;
			overflow-x: hidden !important;
		}

		.job-editor-dialog .el-dialog__body {
			max-height: calc(100dvh - 132px) !important;
			overflow-x: hidden !important;
		}

		.job-editor-dialog .elform-box > .el-form {
			max-height: calc(100dvh - 288px);
			width: 100% !important;
			max-width: 100% !important;
			box-sizing: border-box !important;
			overflow-x: hidden !important;
		}

		.job-editor-dialog .form-items-wrapper {
			width: 100% !important;
			max-width: 100% !important;
			min-width: 0 !important;
			box-sizing: border-box !important;
		}

		.job-editor-dialog .form-items-wrapper > .el-form-item,
		.job-editor-dialog .time-window-config,
		.job-editor-dialog .method-warning-wrapper,
		.job-editor-dialog .interval-tip-wrapper {
			width: 100% !important;
			max-width: 100% !important;
			min-width: 0 !important;
			box-sizing: border-box !important;
			overflow: hidden;
		}

		.job-editor-dialog .el-form-item__content,
		.job-editor-dialog .label_width,
		.job-editor-dialog .el-input,
		.job-editor-dialog .el-select,
		.job-editor-dialog .el-input-group,
		.job-editor-dialog .path-list-wrapper,
		.job-editor-dialog .label-list-box {
			width: 100% !important;
			max-width: 100% !important;
			min-width: 0 !important;
			box-sizing: border-box !important;
		}

		.job-editor-dialog .el-input-group {
			display: flex !important;
		}

		.job-editor-dialog .el-input-group .el-input {
			flex: 1 1 auto;
			min-width: 0 !important;
		}

		.job-editor-dialog .el-input-group__append,
		.job-editor-dialog .el-input-group__prepend {
			flex: 0 0 auto;
			width: auto !important;
		}

		.job-editor-dialog .path-item-content,
		.job-editor-dialog .label-list-item {
			max-width: 100% !important;
			min-width: 0 !important;
			box-sizing: border-box !important;
		}
	}

	/* job-list-polish-v3: compact, scan-friendly management rows */
	.home .job-workbench {
		overflow: visible;
		padding-right: 0;
	}

	.home .job-list-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		margin-bottom: 10px;
		padding: 0 2px;
		color: var(--text-muted);
		font-size: 12px;
	}

	.home .job-list-toolbar strong {
		display: block;
		margin-bottom: 2px;
		color: var(--text-primary);
		font-size: 15px;
		font-weight: 900;
		letter-spacing: -.01em;
	}

	.home .job-card-list.job-compact-list {
		display: grid;
		grid-template-columns: 1fr !important;
		gap: 10px !important;
	}

	.home .job-row-card {
		display: grid !important;
		grid-template-columns: 72px minmax(0, 1fr) minmax(250px, 292px) !important;
		align-items: stretch;
		gap: 12px;
		min-height: 0 !important;
		padding: 12px !important;
		border-radius: 22px !important;
		overflow: hidden;
	}

	.home .job-row-card::before {
		width: 4px;
	}

	.home .job-row-status,
	.home .job-row-main,
	.home .job-row-actions {
		position: relative;
		z-index: 1;
	}

	.home .job-row-status {
		min-height: 0;
		height: 100%;
		padding: 10px 8px;
		border-radius: 14px;
		background: var(--surface-soft);
		align-self: stretch;
		box-sizing: border-box;
		overflow: hidden;
	}

	.home .job-row-main {
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 8px;
		min-width: 0;
	}

	.home .job-row-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 10px;
		min-width: 0;
	}

	.home .job-title-group {
		min-width: 0;
	}

	.home .job-title-group h3 {
		margin: 0;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 18px;
		font-weight: 900;
		line-height: 1.2;
		letter-spacing: -.035em;
		color: var(--text-primary);
	}

	.home .job-card-subtitle {
		margin-top: 4px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 12px;
	}

	.home .job-row-badges {
		display: flex;
		flex-wrap: wrap;
		justify-content: flex-end;
		gap: 6px;
		flex: 0 0 auto;
		max-width: 42%;
	}

	.home .job-status-pill,
	.home .job-method-pill,
	.home .job-running-pill {
		min-height: 26px;
		padding: 6px 9px;
		font-size: 11px;
	}

	.home .job-route-line {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr);
		align-items: stretch;
		gap: 8px;
	}

	.home .job-route-node {
		min-width: 0;
		padding: 8px 10px;
		border-radius: 14px;
		background: var(--surface-soft);
		border: 1px solid var(--border-color);
	}

	.home .job-route-node span {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 5px;
		color: var(--text-muted);
		font-size: 11px;
		font-weight: 900;
	}

	.home .job-route-node strong,
	.home .target-chip {
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.home .job-route-node strong {
		display: block;
		color: var(--text-primary);
		font-size: 12px;
		line-height: 1.35;
	}

	.home .job-route-arrow {
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--brand);
	}

	.home .target-list.compact {
		display: flex;
		flex-wrap: nowrap;
		gap: 6px;
		margin-top: 0;
		overflow: hidden;
	}

	.home .target-chip {
		min-width: 0;
		padding: 4px 7px;
		font-size: 11px;
	}

	.home .job-row-meta {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 6px;
	}

	.home .job-row-meta span {
		min-width: 0;
		padding: 7px 8px;
		border-radius: 12px;
		background: color-mix(in srgb, var(--surface-soft) 78%, transparent);
		color: var(--text-primary);
		font-size: 12px;
		font-weight: 800;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.home .job-row-meta b {
		display: block;
		margin-bottom: 3px;
		color: var(--text-muted);
		font-size: 10px;
		font-weight: 900;
		letter-spacing: .08em;
	}

	.home .job-row-actions {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		align-content: center;
		gap: 7px !important;
		align-self: stretch;
		margin-top: 0;
	}

	.home .job-row-actions .el-button {
		width: 100%;
		min-height: 32px;
		padding-left: 8px;
		padding-right: 8px;
		border-radius: 14px !important;
	}

	.home .job-loading-state,
	.home .job-empty-state {
		grid-column: 1 / -1;
		min-height: 92px !important;
		padding: 14px !important;
		border-radius: 22px !important;
		box-sizing: border-box;
	}

	.home .job-loading-state {
		position: relative;
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		gap: 14px;
		border: 1px solid var(--border-color);
		background:
			radial-gradient(circle at 12% 18%, var(--brand-soft), transparent 16rem),
			linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		overflow: hidden;
	}

	.home .job-loading-mark {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 54px;
		height: 54px;
		border-radius: 18px;
		background: linear-gradient(135deg, var(--brand), var(--accent));
		color: #fffaf1;
		font-size: 22px;
		box-shadow: 0 14px 28px rgba(169, 79, 34, .18);
	}

	.home .job-loading-copy {
		min-width: 0;
	}

	.home .job-loading-title {
		font-size: 18px;
		font-weight: 900;
		color: var(--text-primary);
	}

	.home .job-loading-desc {
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
	}

	.home .job-loading-state::after {
		content: "";
		position: absolute;
		inset: 0;
		transform: translateX(-110%);
		background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--brand-soft) 62%, transparent), transparent);
		animation: jobLoadingSweep 1.35s ease-in-out infinite;
		pointer-events: none;
	}

	.home .job-empty-state {
		display: grid !important;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		justify-content: stretch;
		justify-items: start;
		gap: 14px;
		border: 1px dashed var(--border-light);
		background:
			radial-gradient(circle at 12% 18%, var(--brand-soft), transparent 16rem),
			var(--surface-soft) !important;
		text-align: left;
	}

	.home .job-empty-mark {
		width: 54px;
		height: 54px;
		border-radius: 18px !important;
		font-size: 22px;
	}

	.home .job-empty-title {
		font-size: 18px;
	}

	.home .job-empty-desc {
		max-width: none;
		margin-top: 4px;
		font-size: 13px;
	}

	@keyframes jobLoadingSweep {
		to {
			transform: translateX(110%);
		}
	}

	@media (max-width: 1180px) {
		.home .job-row-card {
			grid-template-columns: 62px minmax(0, 1fr) !important;
		}

		.home .job-row-actions {
			grid-column: 1 / -1;
			grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
		}
	}

	@media (max-width: 768px) {
		.home .job-list-toolbar {
			align-items: stretch;
			flex-direction: column;
		}

		.home .job-row-card {
			grid-template-columns: 1fr !important;
			padding: 14px !important;
		}

		.home .job-row-status {
			min-height: 0;
			flex-direction: row;
			justify-content: flex-start;
			padding: 9px 12px;
		}

		.home .job-row-head {
			flex-direction: column;
		}

		.home .job-row-badges {
			justify-content: flex-start;
			max-width: 100%;
		}

		.home .job-route-line,
		.home .job-row-meta {
			grid-template-columns: 1fr;
		}

		.home .job-route-arrow {
			display: none;
		}

		.home .job-row-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		}

		.home .job-loading-state,
		.home .job-empty-state {
			grid-template-columns: 1fr;
			justify-items: center;
			text-align: center;
		}

	}

	@media (max-width: 420px) {
		.home .job-row-actions {
			grid-template-columns: 1fr !important;
		}
	}











	.home .job-stat {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		overflow: hidden;
		text-align: left;
	}







	@media (max-width: 1180px) {

	}

	@media (max-width: 768px) {

	}

	@media (max-width: 480px) {
	}

	/* pagination-stability: keep list scrollable and pagination visible */
	@media (min-width: 769px) {
		.home .job-workbench {
			flex: 1 1 auto !important;
			min-height: 0 !important;
			overflow-y: auto !important;
			overflow-x: hidden !important;
			padding-right: 2px;
		}

		.home > .page {
			flex: 0 0 auto !important;
			margin-top: 0 !important;
			padding: 10px 0 2px !important;
			border-top: 1px solid var(--border-color);
			background: color-mix(in srgb, var(--bg-primary) 84%, transparent);
			display: flex;
			justify-content: flex-end;
			align-items: center;
			box-sizing: border-box;
			overflow-x: auto;
			overflow-y: hidden;
		}

		.home > .page .el-pagination {
			white-space: nowrap;
		}
	}

	@media (max-width: 768px) {
		.home > .page {
			flex: 0 0 auto !important;
			margin-top: 10px !important;
			padding: 8px 0 2px !important;
			border-top: 1px solid var(--border-color);
			background: color-mix(in srgb, var(--bg-primary) 84%, transparent);
			justify-content: center !important;
			overflow-x: auto;
			overflow-y: hidden;
		}

		.home > .page .el-pagination {
			white-space: nowrap;
		}
	}

	/* page-scroll-behavior: let hero/list/pagination scroll as one page */
	.home {
		overflow-y: auto !important;
		overflow-x: hidden !important;
	}

	.home .job-workbench {
		flex: 0 0 auto !important;
		min-height: auto !important;
		overflow: visible !important;
		padding-right: 0 !important;
	}

</style>
