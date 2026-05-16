<template>
	<div class="engine">
		<div class="engine-shell">
			<ManagementHero
				kicker="OPENLIST CONNECTIONS"
				title="引擎管理"
				description="管理 TaoSync 可调用的 OpenList 引擎。先连接引擎，再到作业管理里选择源目录和目标目录。"
				:statValue="openlistCount || openlistList.length"
				statLabel="已连接引擎"
				actionText="连接新引擎"
				@action="addShow"
			/>

			<ManagementListToolbar
				:show="openlistCount > 0"
				title="引擎列表"
				:summary="engineToolbarSummary"
				hint="按连接聚合展示，常用操作在右侧"
			/>

			<div class="engine-grid" v-loading="getLoading && openlistCount > 0">
				<div class="engine-loading-state" v-if="getLoading && openlistCount == 0">
					<div class="engine-loading-mark"><i class="el-icon-loading"></i></div>
					<div class="engine-loading-copy">
						<div class="engine-loading-title">正在读取引擎列表</div>
						<div class="engine-loading-desc">保持页面布局稳定，连接信息马上回来。</div>
					</div>
				</div>
				<EmptyStateCard
					v-else-if="hasLoaded && openlistCount == 0"
					customClass="engine-empty-state"
					icon="el-icon-connection"
					title="还没有连接引擎"
					description="连接 OpenList 后，就可以在作业管理中选择源目录和目标目录。"
				/>
				<template v-else>
					<div class="engine-card" v-for="item in openlistList" :key="item.id">
						<div class="engine-card-glow"></div>
						<div class="engine-card-head">
							<div class="engine-logo-wrap">
								<el-image src="/OpenList.svg" fit="contain" class="engine-logo"></el-image>
							</div>
							<div class="engine-card-title">
								<div class="engine-name-row">
									<span class="engine-user">{{item.userName}}</span>
									<span class="engine-tag">OpenList</span>
								</div>
								<div class="engine-remark" v-if="item.remark">{{item.remark}}</div>
								<div class="engine-remark muted" v-else>未设置备注</div>
							</div>
						</div>

						<div class="engine-url" :title="item.url">
							<i class="el-icon-link"></i>
							<span>{{item.url}}</span>
						</div>

						<div class="engine-meta">
							<div class="engine-meta-item">
								<span>引擎 ID</span>
								<strong>#{{item.id}}</strong>
							</div>
							<div class="engine-meta-item">
								<span>创建时间</span>
								<strong>{{formatEngineTime(item.createTime)}}</strong>
							</div>
						</div>

						<div class="engine-card-actions">
							<el-button class="mgmt-edit-button" size="small" icon="el-icon-edit" @click="editShowDialog(item)">编辑</el-button>
							<el-button class="mgmt-danger-button" size="small" type="danger" plain icon="el-icon-delete" @click="delOpenList(item.id)">删除</el-button>
						</div>
					</div>
				</template>
			</div>
			<div class="page" v-if="openlistCount > 0">
				<el-pagination
					@size-change="handleSizeChange"
					@current-change="handleCurrentChange"
					:current-page="params.pageNum"
					:page-size="params.pageSize"
					:total="openlistCount"
					:layout="paginationLayout"
					:page-sizes="[10, 20, 50, 100]"
				>
				</el-pagination>
			</div>

			<el-dialog :close-on-click-modal="false" :visible.sync="editShow" :title="editFlag ? '编辑引擎' : '连接新引擎'" width="600px"
				custom-class="tao-dialog tao-form-dialog engine-form-dialog" :before-close="closeShow" :append-to-body="true">
				<div class="elform-box engine-dialog-form">
					<el-form :model="editData" :rules="editFlag ? editRule : addRule" ref="addRule" v-if="editShow"
						label-width="66px">
						<el-form-item prop="url" label="地址">
							<el-input v-model="editData.url" placeholder="请输入地址，例如 http://127.0.0.1:5244"></el-input>
						</el-form-item>
						<el-form-item prop="remark" label="备注">
							<el-input v-model="editData.remark" placeholder="备注便于识别引擎，非必填"></el-input>
						</el-form-item>
						<el-form-item prop="token" label="令牌">
							<el-input v-model="editData.token" show-password
								:placeholder="editFlag ? '请输入令牌，留空表示不修改' : '请输入令牌，请到 OpenList 管理-设置-其他中复制，保存后不要重置令牌'"
								@keyup.enter.native="submit"></el-input>
						</el-form-item>
					</el-form>
				</div>
				<span slot="footer" class="dialog-footer">
					<el-button @click="closeShow">取消</el-button>
					<el-button type="primary" @click="submit" :loading="editLoading">确定</el-button>
				</span>
			</el-dialog>
		</div>
	</div>
</template>
<script>
	import {
		openlistGet,
		openlistPost,
		openlistPut,
		openlistDelete
	} from "@/api/job";
	import {
		parseTime
	} from "@/utils/utils";
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	import EmptyStateCard from '@/views/components/EmptyStateCard.vue';
	import ManagementHero from '@/views/components/ManagementHero.vue';
	import ManagementListToolbar from '@/views/components/ManagementListToolbar.vue';
	export default {
		name: 'Engine',
		components: {
			ManagementHero,
			EmptyStateCard,
			ManagementListToolbar
		},
		computed: {
			paginationLayout() {
				return this.isMobile ? 'sizes, prev, pager, next' : 'total, sizes, prev, pager, next, jumper';
			},
			engineToolbarSummary() {
				return '当前页 ' + this.openlistList.length + ' 个，共 ' + this.openlistCount + ' 个';
			}
		},
		data() {
			return {
				openlistList: [],
				openlistCount: 0,
				params: {
					pageSize: 10,
					pageNum: 1
				},
				getLoading: false,
				hasLoaded: false,
				isMobile: false,
				loadingController: null,
				deleteLoading: false,
				editLoading: false,
				editData: null,
				editFlag: false,
				editShow: false,
				editRule: {
					url: [{
						required: true,
						message: '请输入地址',
						trgger: 'blur'
					}]
				},
				addRule: {
					url: [{
						required: true,
						message: '请输入地址',
						trgger: 'blur'
					}],
					token: [{
						required: true,
						message: '请输入令牌，请到 OpenList 管理-设置-其他中复制',
						trgger: 'blur'
					}]
				}
			};
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.getLoading = true; },
				hide: () => { this.getLoading = false; }
			});
			this.getOpenListList();
		},
		mounted() {
			this.checkMobile();
			window.addEventListener('resize', this.checkMobile);
		},
		beforeDestroy() {
			window.removeEventListener('resize', this.checkMobile);
			if (this.loadingController) {
				this.loadingController.dispose();
			}
		},
		methods: {
			getOpenListList(retryWhenEmpty = true) {
				const loadToken = this.hasLoaded ? 0 : this.loadingController.start();
				openlistGet(this.params).then(res => {
					this.hasLoaded = true;
					const pageData = Array.isArray(res.data) ? {
						dataList: res.data,
						count: res.data.length
					} : (res.data || { dataList: [], count: 0 });
					this.openlistList = pageData.dataList || [];
					this.openlistCount = pageData.count || 0;
					const maxPage = Math.max(1, Math.ceil(this.openlistCount / this.params.pageSize));
					if (retryWhenEmpty && this.openlistCount > 0 && this.openlistList.length === 0 && this.params.pageNum > maxPage) {
						this.params.pageNum = maxPage;
						if (loadToken) {
							this.loadingController.finish(loadToken);
						} else {
							this.getLoading = false;
						}
						this.getOpenListList(false);
						return;
					}
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else {
						this.getLoading = false;
					}
				}).catch(err => {
					this.hasLoaded = true;
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else {
						this.getLoading = false;
					}
				})
			},
			addShow() {
				this.editFlag = false;
				this.editData = {
					remark: '',
					url: '',
					token: ''
				}
				this.editShow = true;
			},
			editShowDialog(row) {
				this.editData = {
					...row,
					token: ''
				};
				this.editFlag = true;
				this.editShow = true;
			},
			closeShow() {
				this.editShow = false;
			},
			submit() {
				this.$refs.addRule.validate((valid) => {
					if (valid) {
						this.editData.url = this.ensureHttpPrefix(this.editData.url);
						this.editLoading = true;
						if (this.editFlag) {
							openlistPut(this.editData).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getOpenListList();
							}).catch(err => {
								this.editLoading = false;
							})
						} else {
							openlistPost(this.editData).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getOpenListList();
							}).catch(err => {
								this.editLoading = false;
							})
						}
					}
				})
			},
			delOpenList(openlistId) {
				this.$confirm('操作不可逆，将永久删除该引擎。请确认没有作业正在使用该引擎，否则可能导致同步失败，仍要删除吗？', '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					this.deleteLoading = true;
					openlistDelete(openlistId).then(res => {
						this.deleteLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getOpenListList();
					}).catch(err => {
						this.deleteLoading = false;
					})
				});
			},
			formatEngineTime(value) {
				return value ? parseTime(value) : '--';
			},
			handleSizeChange(val) {
				this.params.pageSize = val;
				this.params.pageNum = 1;
				this.getOpenListList();
			},
			handleCurrentChange(val) {
				this.params.pageNum = val;
				this.getOpenListList();
			},
			checkMobile() {
				this.isMobile = window.innerWidth <= 768;
			},
			ensureHttpPrefix(url) {
				if (!/^https?:\/\//i.test(url)) {
					if (url.startsWith('//')) {
						return 'http:' + url;
					}
					return 'http://' + url;
				}
				return url;
			}
		}
	}
</script>

<style lang="scss" scoped>
	.engine {
		width: 100%;
		height: 100%;
		box-sizing: border-box;
		overflow-y: auto;
		padding: clamp(14px, 2.4vw, 28px);
	}

	.engine-shell {
		min-height: 100%;
		display: flex;
		flex-direction: column;
		gap: clamp(16px, 2vw, 24px);
	}

	.page {
		flex: 0 0 auto;
		margin-top: 0;
		padding: 10px 0 2px;
		border-top: 1px solid var(--border-color);
		background: color-mix(in srgb, var(--bg-primary) 84%, transparent);
		display: flex;
		align-items: center;
		justify-content: flex-end;
		box-sizing: border-box;
		overflow-x: auto;
		overflow-y: hidden;
	}

	.page ::v-deep .el-pagination {
		white-space: nowrap;
	}










	.engine-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: clamp(16px, 2vw, 24px);
	}

	.engine-card {
		min-height: 248px;
		border-radius: 32px;
		position: relative;
		overflow: hidden;
	}

	.engine-card {
		display: flex;
		flex-direction: column;
		gap: 18px;
		padding: 24px;
		border: 1px solid var(--border-color);
		background: linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
	}

	.engine-card:hover {
		transform: translateY(-3px);
		border-color: var(--border-light);
		box-shadow: var(--shadow-soft);
	}

	.engine-loading-state,
	.engine-empty-state {
		display: grid !important;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		gap: 14px;
		min-height: 0 !important;
		padding: 14px !important;
		border-radius: 22px !important;
	}

	.engine-loading-state {
		grid-column: 1 / -1;
		position: relative;
		min-height: 92px !important;
		border: 1px solid var(--border-color);
		background:
			radial-gradient(circle at 12% 18%, var(--brand-soft), transparent 16rem),
			linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		overflow: hidden;
	}

	.engine-empty-state {
		grid-column: 1 / -1;
		box-shadow: none;
	}

	.engine-loading-mark {
		width: 54px;
		height: 54px;
		font-size: 22px;
	}

	.engine-loading-mark {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 18px;
		background: linear-gradient(135deg, var(--brand), var(--accent));
		color: #fffaf1;
		box-shadow: 0 14px 28px rgba(169, 79, 34, .18);
	}

	.engine-loading-copy {
		min-width: 0;
	}

	.engine-loading-title {
		font-size: 18px;
		font-weight: 900;
		color: var(--text-primary);
	}

	.engine-loading-desc {
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
	}

	.engine-loading-state::after {
		content: "";
		position: absolute;
		inset: 0;
		transform: translateX(-110%);
		background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--brand-soft) 62%, transparent), transparent);
		animation: engineLoadingSweep 1.35s ease-in-out infinite;
		pointer-events: none;
	}

	@keyframes engineLoadingSweep {
		to {
			transform: translateX(110%);
		}
	}

	.engine-card-glow {
		position: absolute;
		inset: -40% -30% auto auto;
		width: 190px;
		height: 190px;
		border-radius: 999px;
		background: var(--brand-soft);
		filter: blur(4px);
		pointer-events: none;
	}

	.engine-card-head {
		display: flex;
		align-items: center;
		gap: 16px;
		position: relative;
		z-index: 1;
	}

	.engine-logo-wrap {
		width: 66px;
		height: 66px;
		border-radius: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: color-mix(in srgb, var(--brand-soft) 70%, transparent);
		border: 1px solid var(--border-light);
		flex: 0 0 auto;
	}

	.engine-logo {
		width: 42px;
		height: 42px;
	}

	.engine-card-title {
		min-width: 0;
		flex: 1;
	}

	.engine-name-row {
		display: flex;
		align-items: center;
		gap: 10px;
		min-width: 0;
	}

	.engine-user {
		font-size: 23px;
		font-weight: 900;
		line-height: 1.1;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.engine-tag {
		padding: 4px 8px;
		border-radius: 999px;
		background: var(--brand-soft);
		color: var(--brand-strong);
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .08em;
		flex: 0 0 auto;
	}

	.engine-remark {
		margin-top: 7px;
		font-size: 13px;
		font-weight: 800;
		color: var(--remark-color);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.engine-remark.muted {
		color: var(--text-muted);
		font-weight: 700;
	}

	.engine-url {
		position: relative;
		z-index: 1;
		display: flex;
		align-items: flex-start;
		gap: 10px;
		min-height: 48px;
		padding: 13px 14px;
		border: 1px solid var(--border-color);
		border-radius: 18px;
		background: var(--surface-soft);
		color: var(--text-secondary);
		font-size: 13px;
		line-height: 1.55;
		word-break: break-all;
	}

	.engine-url i {
		margin-top: 3px;
		color: var(--brand);
		flex: 0 0 auto;
	}

	.engine-meta {
		display: grid;
		grid-template-columns: 88px 1fr;
		gap: 10px;
		position: relative;
		z-index: 1;
	}

	.engine-meta-item {
		padding: 10px 12px;
		border-radius: 16px;
		background: color-mix(in srgb, var(--surface-soft) 76%, transparent);
	}

	.engine-meta-item span {
		display: block;
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted);
	}

	.engine-meta-item strong {
		display: block;
		margin-top: 5px;
		font-size: 13px;
		line-height: 1.35;
		color: var(--text-primary);
		word-break: break-all;
	}

	.engine-card-actions {
		display: flex;
		justify-content: flex-end;
		gap: 10px;
		margin-top: auto;
		position: relative;
		z-index: 1;
	}

	.engine-dialog-form {
		padding-top: 4px;
	}

	@media (max-width: 768px) {
		.engine {
			padding: 12px;
		}

		.page {
			margin-top: 10px;
			padding: 8px 0 2px;
			justify-content: center;
		}





		.engine-grid {
			grid-template-columns: 1fr;
		}

		.engine-card {
			min-height: auto;
			border-radius: 24px;
			padding: 18px;
		}

		.engine-card-head {
			align-items: flex-start;
		}

		.engine-logo-wrap {
			width: 54px;
			height: 54px;
			border-radius: 19px;
		}

		.engine-logo {
			width: 34px;
			height: 34px;
		}

		.engine-user {
			font-size: 20px;
		}

		.engine-meta {
			grid-template-columns: 1fr;
		}

		.engine-card-actions {
			justify-content: stretch;
		}

		.engine-card-actions .el-button {
			flex: 1;
		}

		::v-deep .el-dialog {
			width: calc(100vw - 20px) !important;
			margin: 10px auto 0 !important;
		}
	}

	@media (max-width: 420px) {

		.engine-name-row {
			align-items: flex-start;
			flex-direction: column;
			gap: 6px;
		}
	}
	/* engine-compact-row-card: align with job management cards */
	.engine-shell {
		gap: 12px !important;
	}







	.engine-grid {
		grid-template-columns: 1fr !important;
		gap: 10px !important;
	}

	.engine-card {
		display: grid !important;
		grid-template-columns: minmax(240px, .85fr) minmax(260px, 1fr) minmax(180px, .52fr) 154px;
		align-items: center;
		gap: 14px;
		min-height: 0 !important;
		padding: 14px !important;
		border-radius: 22px !important;
	}

	.engine-card::before {
		content: "";
		position: absolute;
		inset: 0 auto 0 0;
		width: 4px;
		background: linear-gradient(180deg, var(--brand), var(--accent));
	}

	.engine-card-glow {
		display: none;
	}

	.engine-card-head,
	.engine-url,
	.engine-meta,
	.engine-card-actions {
		position: relative;
		z-index: 1;
	}

	.engine-card-head {
		gap: 12px;
		min-width: 0;
	}

	.engine-logo-wrap {
		width: 54px;
		height: 54px;
		border-radius: 18px !important;
	}

	.engine-logo {
		width: 34px;
		height: 34px;
	}

	.engine-user {
		font-size: 19px;
	}

	.engine-remark {
		margin-top: 4px;
		font-size: 12px;
	}

	.engine-url {
		min-height: 0;
		padding: 9px 10px;
		border-radius: 16px;
		align-items: center;
		font-size: 13px;
		line-height: 1.35;
		word-break: normal;
		min-width: 0;
	}

	.engine-url span {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.engine-url i {
		margin-top: 0;
	}

	.engine-meta {
		grid-template-columns: 1fr;
		gap: 6px;
	}

	.engine-meta-item {
		padding: 7px 9px;
		border-radius: 12px;
	}

	.engine-meta-item span {
		font-size: 10px;
	}

	.engine-meta-item strong {
		margin-top: 3px;
		font-size: 12px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.engine-card-actions {
		display: grid;
		grid-template-columns: 1fr;
		gap: 7px !important;
		margin-top: 0;
	}

	.engine-card-actions .el-button {
		width: 100%;
		min-height: 32px;
		margin-left: 0 !important;
	}


	@media (max-width: 1180px) {
		.engine-card {
			grid-template-columns: minmax(240px, 1fr) minmax(260px, 1fr) 150px;
		}

		.engine-card-actions {
			grid-column: 1 / -1;
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 768px) {

		.engine-card {
			grid-template-columns: 1fr;
			gap: 10px;
			padding: 14px !important;
		}

		.engine-loading-state,
		.engine-empty-state {
			grid-template-columns: 1fr !important;
			gap: 10px;
		}

		.engine-loading-state,
		.engine-empty-state {
			text-align: center;
			justify-items: center;
		}

		.engine-card-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

	}

	@media (max-width: 420px) {
	}

	/* management-page-alignment-v2 */




	.engine-card {
		grid-template-columns: 76px minmax(210px, .85fr) minmax(260px, 1fr) minmax(176px, .52fr) 154px !important;
		align-items: center;
	}

	.engine-card-head {
		display: contents;
	}

	.engine-logo-wrap {
		position: relative;
		z-index: 1;
		grid-column: 1;
		justify-self: center;
	}

	.engine-card-title {
		position: relative;
		z-index: 1;
		grid-column: 2;
		min-width: 0;
	}

	.engine-url {
		grid-column: 3;
	}

	.engine-meta {
		grid-column: 4;
	}

	.engine-card-actions {
		grid-column: 5;
		align-self: stretch;
		align-content: center;
	}

	.engine-url,
	.engine-meta-item,
	.engine-card-actions .el-button {
		border-radius: 14px;
	}

	@media (max-width: 1180px) {

		.engine-card {
			grid-template-columns: 64px minmax(220px, 1fr) minmax(260px, 1fr) !important;
		}

		.engine-logo-wrap { grid-column: 1; }
		.engine-card-title { grid-column: 2; }
		.engine-url { grid-column: 3; }
		.engine-meta { grid-column: 1 / -1; }
		.engine-card-actions { grid-column: 1 / -1; }
	}

	@media (max-width: 768px) {

		.engine-logo-wrap,
		.engine-card-title,
		.engine-url,
		.engine-meta,
		.engine-card-actions {
			grid-column: auto;
		}

		.engine-card-head {
			display: flex;
		}
	}


	/* overview-boundary-fix */

	@media (max-width: 768px) {
		.engine-card {
			display: flex !important;
			flex-direction: column;
			align-items: stretch !important;
			gap: 12px;
			min-height: auto !important;
			padding: 14px !important;
		}

		.engine-card-head {
			display: flex !important;
			align-items: flex-start !important;
			gap: 12px;
		}

		.engine-logo-wrap,
		.engine-card-title,
		.engine-url,
		.engine-meta,
		.engine-card-actions {
			grid-column: auto !important;
			justify-self: auto !important;
			width: 100%;
		}

		.engine-logo-wrap {
			width: 54px !important;
			flex: 0 0 54px;
		}

		.engine-card-title {
			min-width: 0;
			flex: 1 1 auto;
		}

		.engine-name-row {
			flex-wrap: wrap;
		}

		.engine-url {
			word-break: break-all;
		}

		.engine-url span,
		.engine-meta-item strong {
			white-space: normal;
			overflow: visible;
			text-overflow: clip;
			word-break: break-all;
		}

		.engine-meta {
			grid-template-columns: 1fr !important;
		}

		.engine-card-actions {
			display: grid !important;
			grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
			align-self: auto;
		}
	}

	@media (max-width: 420px) {
		.engine-card-actions {
			grid-template-columns: 1fr !important;
		}
	}

</style>


