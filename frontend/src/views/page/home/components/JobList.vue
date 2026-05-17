<template>
	<div class="job-workbench">
		<ManagementListToolbar
			:show="jobData.dataList.length > 0"
			title="作业列表"
			:summary="toolbarSummary"
			:hint="toolbarHint"
			:hintIcon="runningJobCount > 0 ? 'el-icon-loading' : ''"
			:hintAccent="runningJobCount > 0"
		/>
		<div class="job-card-list job-compact-list" v-loading="loading && jobData.dataList.length > 0">
			<div class="job-loading-state" v-if="loading && jobData.dataList.length == 0">
				<div class="job-loading-mark"><i class="el-icon-loading"></i></div>
				<div class="job-loading-copy">
					<div class="job-loading-title">正在读取作业列表</div>
					<div class="job-loading-desc">保持页面布局稳定，作业信息马上回来。</div>
				</div>
			</div>
			<EmptyStateCard
				v-else-if="hasLoaded && jobData.dataList.length == 0"
				customClass="job-empty-state"
				icon="el-icon-folder-add"
				title="还没有同步作业"
				description="先连接 OpenList 引擎，再创建一个源目录到目标目录的同步作业。"
			/>

			<template v-else>
			<article class="job-card job-row-card" v-for="row in jobData.dataList" :key="row.id" :class="{'is-disabled': !row.enable, 'is-running': jobRunning(row)}">
				<div :class="['job-row-status', jobRunning(row) ? 'is-running' : (row.enable ? 'is-enabled' : 'is-disabled')]">
					<span class="status-dot"></span>
					<span>{{jobRunning(row) ? '执行中' : (row.enable ? '启用' : '禁用')}}</span>
				</div>

				<div class="job-row-main">
					<div class="job-row-head">
						<div class="job-title-group">
							<h3>{{row.remark || `作业 #${row.id}`}}</h3>
							<div class="job-card-subtitle">#{{row.id}} · {{callModeText(row)}} · {{scheduleText(row)}}</div>
						</div>
						<div class="job-row-badges">
							<div :class="['job-status-pill', row.enable ? 'is-enabled' : 'is-disabled']">
								<span class="status-dot"></span>{{row.enable ? '启用中' : '已禁用'}}
							</div>
							<div class="job-running-pill" v-if="jobRunning(row)"><span class="pulse-dot"></span>{{runningTaskText(row)}}</div>
							<div class="job-method-pill">{{methodText(row.method)}}</div>
						</div>
					</div>

					<div class="job-route-line">
						<div class="job-route-node source">
							<span><i class="el-icon-upload2"></i>源目录</span>
							<strong :title="row.srcPath">{{row.srcPath}}</strong>
						</div>
						<div class="job-route-arrow"><i class="el-icon-right"></i></div>
						<div class="job-route-node target">
							<span><i class="el-icon-download"></i>目标目录</span>
							<div class="target-list compact">
								<span class="target-chip" v-for="item in destinationList(row).slice(0, 3)" :key="item" :title="item">{{item}}</span>
								<span class="target-chip more" v-if="destinationList(row).length > 3">+{{destinationList(row).length - 3}}</span>
							</div>
						</div>
					</div>

					<button
						type="button"
						class="job-detail-toggle"
						:class="{ 'is-open': isDetailOpen(row.id) }"
						@click="toggleDetails(row.id)"
					>
						<span>查看更多同步规则</span>
						<i class="el-icon-arrow-down"></i>
					</button>

					<div class="job-meta-panel" :class="{ 'is-open': isDetailOpen(row.id) }">
						<div class="job-row-meta">
							<span><b>源扫描</b>{{cacheText(row.useCacheS, row.scanIntervalS)}}</span>
							<span><b>目标扫描</b>{{cacheText(row.useCacheT, row.scanIntervalT)}}</span>
							<span><b>排除</b>{{excludeList(row).length ? `${excludeList(row).length} 项` : '无'}}</span>
							<span><b>创建</b>{{row.createTime | timeStampFilter}}</span>
						</div>
					</div>
				</div>

				<div class="job-card-actions job-row-actions">
					<el-button icon="el-icon-caret-right" type="primary" @click="$emit('put-job', row)" :loading="btnLoading" size="small">执行</el-button>
					<el-button icon="el-icon-view" type="success" @click="$emit('detail', row.id)" :loading="btnLoading" size="small">任务</el-button>
					<template v-if="row.isCron != 2">
						<el-button type="warning" icon="el-icon-video-pause" :loading="btnLoading" size="small" v-if="row.enable"
							@click="$emit('disable-job-show', row, false)">禁用</el-button>
						<el-button type="success" icon="el-icon-video-play" :loading="btnLoading" size="small" v-else
							@click="$emit('put-job', row, false)">启用</el-button>
					</template>
					<el-button class="job-edit-button" plain icon="el-icon-edit" :loading="btnLoading" size="small" @click="$emit('edit-job-show', row)">编辑</el-button>
					<el-button class="mgmt-danger-button" type="danger" plain icon="el-icon-delete" :loading="btnLoading" size="small" @click="$emit('disable-job-show', row, true)">删除</el-button>
				</div>
			</article>
			</template>
		</div>
	</div>
</template>

<script>
	import EmptyStateCard from '@/views/components/EmptyStateCard.vue';
	import ManagementListToolbar from '@/views/components/ManagementListToolbar.vue';
	export default {
		name: 'JobList',
		components: {
			EmptyStateCard,
			ManagementListToolbar
		},
		data() {
			return {
				openDetailIds: []
			};
		},
		computed: {
			enabledCount() {
				return (this.jobData.dataList || []).filter(item => item.enable).length;
			},
			disabledCount() {
				return (this.jobData.dataList || []).filter(item => !item.enable).length;
			},
			toolbarSummary() {
				const current = this.jobData.dataList.length;
				const total = this.jobData.count || current;
				return '当前页 ' + current + ' 个，共 ' + total + ' 个，启用 ' + this.enabledCount + ' 个，禁用 ' + this.disabledCount + ' 个';
			},
			toolbarHint() {
				return this.runningJobCount > 0 ? this.runningJobCount + ' 个作业正在执行' : '按作业分组展示，常用操作在右侧';
			}
		},
		props: {
			jobData: {
				type: Object,
				required: true
			},
			loading: {
				type: Boolean,
				default: false
			},
			hasLoaded: {
				type: Boolean,
				default: false
			},
			btnLoading: {
				type: Boolean,
				default: false
			},
			runningJobCount: {
				type: Number,
				default: 0
			},
			jobRunning: {
				type: Function,
				required: true
			},
			methodText: {
				type: Function,
				required: true
			},
			callModeText: {
				type: Function,
				required: true
			},
			scheduleText: {
				type: Function,
				required: true
			},
			runningTaskText: {
				type: Function,
				required: true
			},
			destinationList: {
				type: Function,
				required: true
			},
			excludeList: {
				type: Function,
				required: true
			},
			cacheText: {
				type: Function,
				required: true
			}
		},
		methods: {
			isDetailOpen(jobId) {
				return this.openDetailIds.includes(jobId);
			},
			toggleDetails(jobId) {
				if (this.isDetailOpen(jobId)) {
					this.openDetailIds = this.openDetailIds.filter(item => item !== jobId);
					return;
				}
				this.openDetailIds = [...this.openDetailIds, jobId];
			}
		}
	}
</script>

<style lang="scss" scoped>
	.job-detail-toggle {
		display: inline-flex;
		align-items: center;
		align-self: flex-start;
		gap: 6px;
		padding: 0;
		border: 0;
		background: transparent;
		color: var(--text-muted);
		font-size: 12px;
		font-weight: 800;
		line-height: 1.4;
		cursor: pointer;
		transition: color .18s ease, transform .18s ease;
	}

	.job-detail-toggle:hover {
		color: var(--brand-strong);
	}

	.job-detail-toggle i {
		font-size: 12px;
		transition: transform .22s ease;
	}

	.job-detail-toggle.is-open {
		color: var(--brand-strong);
	}

	.job-detail-toggle.is-open i {
		transform: rotate(180deg);
	}

	.job-meta-panel {
		display: grid;
		grid-template-rows: 0fr;
		transition: grid-template-rows .24s ease;
	}

	.job-meta-panel.is-open {
		grid-template-rows: 1fr;
	}

	.job-meta-panel .job-row-meta {
		min-height: 0;
		overflow: hidden;
	}
</style>
