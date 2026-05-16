<template>
	<div class="notify">
		<div class="notify-shell">
			<ManagementHero
				kicker="DELIVERY CHANNELS"
				title="通知配置"
				description="配置同步结果的送达渠道。建议至少启用一个渠道，用于接收作业完成、失败与测试消息。"
				:statValue="dataCount || dataList.length"
				statLabel="通知渠道"
				actionText="新增通知渠道"
				@action="addShow"
			/>

			<ManagementListToolbar
				:show="dataCount > 0"
				title="渠道列表"
				:summary="notifyToolbarSummary"
				hint="按通知渠道聚合展示，常用操作在右侧"
			/>

			<div class="notify-grid" v-loading="loading && dataCount > 0">
				<div class="notify-loading-state" v-if="loading && dataCount == 0">
					<div class="notify-loading-mark"><i class="el-icon-loading"></i></div>
					<div class="notify-loading-copy">
						<div class="notify-loading-title">正在读取通知配置</div>
						<div class="notify-loading-desc">保持页面布局稳定，通知渠道信息马上回来。</div>
					</div>
				</div>
				<EmptyStateCard
					v-else-if="hasLoaded && dataCount == 0"
					customClass="notify-empty-state"
					icon="el-icon-message"
					title="还没有通知渠道"
					description="新增一个 Server 酱、钉钉或企业微信渠道，用来接收同步完成、失败与测试消息。"
				/>
				<template v-else>
					<div class="notify-card" v-for="item in dataList" :key="item.id" :class="`notify-method-${item.method}`">
						<div class="notify-card-glow"></div>
						<div class="notify-card-head">
							<div class="notify-logo-wrap">
								<el-image :src="`/notify/${item.method}.png`" fit="contain" class="notify-logo"></el-image>
							</div>
							<div class="notify-title-box">
								<div class="notify-name-row">
									<span class="notify-name">{{channelMethodName(item.method)}}</span>
									<span :class="`notify-status ${item.enable == 1 ? 'is-on' : 'is-off'}`">{{item.enable == 1 ? '启用中' : '已停用'}}</span>
								</div>
								<div class="notify-subtitle">{{channelSummary(item)}}</div>
							</div>
						</div>

						<div class="notify-meta">
							<div class="notify-meta-item">
								<span>渠道 ID</span>
								<strong>#{{item.id}}</strong>
							</div>
							<div class="notify-meta-item">
								<span>发送策略</span>
								<strong>{{channelPolicy(item)}}</strong>
							</div>
						</div>

						<div class="notify-actions">
							<el-button class="mgmt-edit-button" size="small" icon="el-icon-edit" @click="editShowDialog(item)">编辑</el-button>
							<el-button size="small" :type="item.enable == 0 ? 'success' : 'warning'" :icon="item.enable == 0 ? 'el-icon-open' : 'el-icon-turn-off'" @click="enableNotify(item.id, item.enable == 0 ? 1 : 0)">{{item.enable == 0 ? '启用' : '禁用'}}</el-button>
							<el-button class="mgmt-test-button" size="small" icon="el-icon-position" :loading="tstLoading" @click="tstCu(item)">测试</el-button>
							<el-button class="mgmt-danger-button" size="small" type="danger" plain icon="el-icon-delete" @click="delCu(item.id)">删除</el-button>
						</div>
					</div>
				</template>
			</div>
			<div class="page" v-if="dataCount > 0">
				<el-pagination
					@size-change="handleSizeChange"
					@current-change="handleCurrentChange"
					:current-page="params.pageNum"
					:page-size="params.pageSize"
					:total="dataCount"
					:layout="paginationLayout"
					:page-sizes="[10, 20, 50, 100]"
				>
				</el-pagination>
			</div>

			<el-dialog :close-on-click-modal="false" top="6vh" :visible.sync="editShow" :title="editFlag ? '编辑通知渠道' : '新增通知渠道'"
				width="680px" custom-class="tao-dialog tao-form-dialog notify-form-dialog" :before-close="closeShow" :append-to-body="true">
				<div class="elform-box">
					<el-form :model="editData" :rules="editRule[editData.method]" ref="addRule" v-if="editShow"
						label-width="100px">
						<el-form-item prop="enable" label="是否启用">
							<el-switch v-model="editData.enable" :active-value="1" :inactive-value="0">
							</el-switch>
						</el-form-item>
						<el-form-item prop="method" label="方式">
							<el-select v-model="editData.method" @change="methodChange" style="width: 100%;">
								<el-option :key="meItem - 1" :value="meItem - 1" :label="meItem - 1 | notifyMethodFilter"
									v-for="meItem in notifyMethodLength"></el-option>
							</el-select>
						</el-form-item>
						<template v-if="editData.method == 0">
							<el-form-item prop="params.url" label="请求地址">
								<el-input v-model="editData.params.url" placeholder="请输入请求地址"></el-input>
							</el-form-item>
							<el-form-item prop="params.method" label="请求方法">
								<el-select v-model="editData.params.method" style="width: 100%;">
									<el-option key="POST" value="POST" label="POST"></el-option>
									<el-option key="PUT" value="PUT" label="PUT"></el-option>
									<el-option key="GET" value="GET" label="GET"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item v-if="editData.params.method != 'GET'" prop="params.contentType" label="请求体类型">
								<el-select v-model="editData.params.contentType" style="width: 100%;">
									<el-option key="application/json" value="application/json" label="application/json"></el-option>
									<el-option key="application/x-www-form-urlencoded" value="application/x-www-form-urlencoded"
										label="application/x-www-form-urlencoded"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item prop="params.titleName" label="标题参数名">
								<el-input v-model="editData.params.titleName" placeholder="请输入标题参数名"></el-input>
							</el-form-item>
							<el-form-item prop="params.needContent" label="是否需要内容">
								<el-select v-model="editData.params.needContent" style="width: 100%;">
									<el-option :key="true" :value="true" label="需要"></el-option>
									<el-option :key="false" :value="false" label="不需要"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item prop="params.contentName" v-if="editData.params.needContent" label="内容参数名">
								<el-input v-model="editData.params.contentName" placeholder="请输入内容参数名"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="editData.method == 1">
							<div class="tip-box">同时支持 <a href="https://sct.ftqq.com/r/15503" target="_blank">Server 酱 Turbo</a> 与 <a href="https://sc3.ft07.com/" target="_blank">Server 酱 3</a>，按你的密钥配置即可。</div>
							<el-form-item prop="params.sendKey" label="SendKey">
								<el-input v-model="editData.params.sendKey" placeholder="请输入 SendKey"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="editData.method == 2">
							<div class="tip-box"><a
									href="https://open.dingtalk.com/document/orgapp/custom-bot-creation-and-installation"
									target="_blank">配置指南</a> 安全设置请选择“自定义关键字”，关键字内容填写 `TaoSync`，不要包含反引号。</div>
							<el-form-item prop="params.url" label="WebHook">
								<el-input v-model="editData.params.url"
									placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxxx"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="editData.method == 3">
							<div class="tip-box"><a
									href="https://sct.ftqq.com/forward"
									target="_blank">配置指南</a> 请在企业微信管理后台获取相关参数。</div>
							<el-form-item prop="params.corpid" label="企业 ID">
								<el-input v-model="editData.params.corpid"
									placeholder="请输入企业 ID"></el-input>
							</el-form-item>
							<el-form-item prop="params.agentid" label="应用 ID">
								<el-input v-model="editData.params.agentid"
									placeholder="请输入应用 ID 或 AgentId"></el-input>
							</el-form-item>
							<el-form-item prop="params.corpsecret" label="应用 Secret">
								<el-input v-model="editData.params.corpsecret"
									placeholder="请输入应用 Secret" type="password"></el-input>
							</el-form-item>
							<el-form-item prop="params.touser" label="接收用户">
								<el-input v-model="editData.params.touser"
									placeholder="请输入接收用户 ID，多个用户用 | 分隔，@all 表示全部"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="editData.method == 4">
							<div class="tip-box"><a
									href="https://open.larksuite.com/document/client-docs/bot-v3/add-custom-bot"
									target="_blank">配置指南</a> 安全设置请选择“自定义关键字”，关键字内容填写 `TaoSync`，不要包含反引号。</div>
							<el-form-item prop="params.url" label="WebHook">
								<el-input v-model="editData.params.url"
									placeholder="https://open.larksuite.com/open-apis/bot/v2/hook/xxxxxxxxxx"></el-input>
							</el-form-item>
						</template>
						<el-form-item prop="params.notSendNull" label="忽略无同步">
							<el-switch v-model="editData.params.notSendNull" :active-value="1" :inactive-value="0">
							</el-switch>
						</el-form-item>
					</el-form>
				</div>
				<span slot="footer" class="dialog-footer">
					<el-button @click="closeShow">取消</el-button>
					<el-button type="success" :loading="tstLoading" @click="tstCu()">测试</el-button>
					<el-button type="primary" @click="submit" :loading="editLoading">确定</el-button>
				</span>
			</el-dialog>
		</div>
	</div>
</template>
<script>
	import {
		getNotifyList,
		delNotify,
		putEnableNotify,
		postAddNotify,
		putEditNotify
	} from '@/api/notify';
	import notifyMethod from '@/utils/notifyMethod';
	import { createDelayedLoadingController } from '@/utils/loadingFeedback';
	import EmptyStateCard from '@/views/components/EmptyStateCard.vue';
	import ManagementHero from '@/views/components/ManagementHero.vue';
	import ManagementListToolbar from '@/views/components/ManagementListToolbar.vue';
	export default {
		name: 'Notify',
		components: {
			ManagementHero,
			EmptyStateCard,
			ManagementListToolbar
		},
		computed: {
			paginationLayout() {
				return this.isMobile ? 'sizes, prev, pager, next' : 'total, sizes, prev, pager, next, jumper';
			},
			enabledChannelCount() {
				return (this.dataList || []).filter(item => item.enable == 1).length;
			},
			disabledChannelCount() {
				return (this.dataList || []).filter(item => item.enable != 1).length;
			},
			notifyToolbarSummary() {
				return '当前页 ' + this.dataList.length + ' 个，共 ' + this.dataCount + ' 个，启用 ' + this.enabledChannelCount + ' 个，禁用 ' + this.disabledChannelCount + ' 个';
			}
		},
		data() {
			return {
				notifyMethodLength: notifyMethod.length,
				dataList: [],
				dataCount: 0,
				params: {
					pageSize: 10,
					pageNum: 1
				},
				loading: false,
				hasLoaded: false,
				isMobile: false,
				loadingController: null,
				deleteLoading: false,
				editLoading: false,
				tstLoading: false,
				enableLoading: false,
				editData: null,
				editFlag: false,
				editShow: false,
				editRule: [{
					params: {
						url: [{
							type: 'string',
							required: true,
							message: '请输入地址'
						}],
						titleName: [{
							type: 'string',
							required: true,
							message: '请输入标题参数名'
						}],
						contentName: [{
							type: 'string',
							required: true,
							message: '请输入内容参数名'
						}]
					}
				}, {
					params: {
						sendKey: [{
							type: 'string',
							required: true,
							message: '请输入 SendKey'
						}]
					}
				}, {
					params: {
						url: [{
							type: 'string',
							required: true,
							message: '请输入 WebHook 地址'
						}]
					}
				}, {
					params: {
						corpid: [{
							type: 'string',
							required: true,
							message: '请输入企业 ID'
						}],
						agentid: [{
							type: 'string',
							required: true,
							message: '请输入应用 ID 或 AgentId'
						}],
						corpsecret: [{
							type: 'string',
							required: true,
							message: '请输入应用 Secret'
						}],
						touser: [{
							type: 'string',
							required: false
						}]
					}
				}, {
					params: {
						url: [{
							type: 'string',
							required: true,
							message: '请输入 WebHook 地址'
						}]
					}
				}]
			};
		},
		created() {
			this.loadingController = createDelayedLoadingController({
				show: () => { this.loading = true; },
				hide: () => { this.loading = false; }
			});
			this.getData();
		},
		mounted() {
			this.checkMobile();
			window.addEventListener('resize', this.checkMobile);
		},
		watch: {
			editShow(val) {
				if (typeof document !== 'undefined') {
					document.body.classList.toggle('notify-dialog-open', !!val);
				}
			}
		},
		beforeDestroy() {
			window.removeEventListener('resize', this.checkMobile);
			if (typeof document !== 'undefined') {
				document.body.classList.remove('notify-dialog-open');
			}
			if (this.loadingController) {
				this.loadingController.dispose();
			}
		},
		methods: {
			channelMethodName(method) {
				return notifyMethod[method] || '未知渠道';
			},
			parseNotifyParams(item) {
				if (!item || item.params == null) {
					return {};
				}
				if (typeof item.params === 'object') {
					return item.params;
				}
				try {
					return JSON.parse(item.params);
				} catch (e) {
					return {};
				}
			},
			channelSummary(item) {
				const params = this.parseNotifyParams(item);
				if (item.method === 0) {
					return params.url ? `${params.method || 'POST'} 路 ${params.url}` : '自定义 Webhook，按你的接口格式发送';
				}
				if (item.method === 1) {
					return params.sendKey ? `SendKey 路 ${String(params.sendKey).slice(0, 8)}...` : '通过 Server 酱推送到微信';
				}
				if (item.method === 2 || item.method === 4) {
					return params.url ? params.url : `${this.channelMethodName(item.method)} WebHook 地址未展示`;
				}
				if (item.method === 3) {
					return params.agentid ? `应用 ID 路 ${params.agentid}` : '企业微信应用消息';
				}
				return '通知渠道';
			},
			channelPolicy(item) {
				const params = this.parseNotifyParams(item);
				return params.notSendNull ? '忽略无同步' : '全部结果';
			},
			getData(retryWhenEmpty = true) {
				const loadToken = this.hasLoaded ? 0 : this.loadingController.start();
				getNotifyList(this.params).then(res => {
					this.hasLoaded = true;
					const pageData = Array.isArray(res.data) ? {
						dataList: res.data,
						count: res.data.length
					} : (res.data || { dataList: [], count: 0 });
					this.dataList = pageData.dataList || [];
					this.dataCount = pageData.count || 0;
					const maxPage = Math.max(1, Math.ceil(this.dataCount / this.params.pageSize));
					if (retryWhenEmpty && this.dataCount > 0 && this.dataList.length === 0 && this.params.pageNum > maxPage) {
						this.params.pageNum = maxPage;
						if (loadToken) {
							this.loadingController.finish(loadToken);
						} else {
							this.loading = false;
						}
						this.getData(false);
						return;
					}
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
				}).catch(err => {
					this.hasLoaded = true;
					if (loadToken) {
						this.loadingController.finish(loadToken);
					} else {
						this.loading = false;
					}
				})
			},
			addShow() {
				this.editFlag = false;
				this.editData = {
					enable: 1,
					method: 1,
					params: {
						sendKey: '',
						notSendNull: false
					}
				}
				this.editShow = true;
			},
			editShowDialog(row) {
				let editData = JSON.parse(JSON.stringify(row));
				editData.params = JSON.parse(editData.params);
				if (!editData.params.hasOwnProperty('notSendNull')) {
					editData.params['notSendNull'] = false;
				}
				this.editData = editData;
				this.editFlag = true;
				this.editShow = true;
			},
			methodChange(val) {
				if (val === 0) {
					this.editData.params = {
						url: '',
						method: 'POST',
						contentType: 'application/json',
						needContent: true,
						titleName: 'title',
						contentName: 'content',
						notSendNull: false
					}
				} else if (val === 1) {
					this.editData.params = {
						sendKey: '',
						notSendNull: false
					}
				} else if (val === 2) {
					this.editData.params = {
						url: '',
						notSendNull: false
					}
				} else if (val === 3) {
					this.editData.params = {
						corpid: '',
						agentid: '',
						corpsecret: '',
						touser: '@all',
						notSendNull: false
					}
				} else if (val === 4) {
					this.editData.params = {
						url: '',
						notSendNull: false
					}
				}
				this.$nextTick(() => {
					this.$refs.addRule.clearValidate();
				})
			},
			closeShow() {
				this.editShow = false;
			},
			handleSizeChange(val) {
				this.params.pageSize = val;
				this.params.pageNum = 1;
				this.getData();
			},
			handleCurrentChange(val) {
				this.params.pageNum = val;
				this.getData();
			},
			checkMobile() {
				this.isMobile = window.innerWidth <= 768;
			},
			enableNotify(notifyId, enable) {
				this.enableLoading = true;
				putEnableNotify(notifyId, enable).then(res => {
					this.enableLoading = false;
					this.$message({
						message: res.msg,
						type: 'success'
					});
					this.getData();
				}).catch(err => {
					this.enableLoading = false;
				})
			},
			submit() {
				this.$refs.addRule.validate((valid) => {
					if (valid) {
						let dt = JSON.parse(JSON.stringify(this.editData));
						dt.params = JSON.stringify(dt.params);
						this.editLoading = true;
						if (this.editFlag) {
							putEditNotify(dt).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getData();
							}).catch(err => {
								this.editLoading = false;
							})
						} else {
							postAddNotify(dt).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getData();
							}).catch(err => {
								this.editLoading = false;
							})
						}
					}
				})
			},
			tstCu(item = null) {
				if (item == null) {
					this.$refs.addRule.validate((valid) => {
						if (valid) {
							this.tstCuTrueDo(this.editData);
						}
					})
				} else {
					this.tstCuTrueDo(item);
				}
			},
			tstCuTrueDo(item) {
				this.tstLoading = true;
				let it = JSON.parse(JSON.stringify(item));
				if (typeof it.params === 'object' && it.params !== null) {
					it.params = JSON.stringify(it.params);
				}
				delete it.enable;
				postAddNotify(it).then(res => {
					this.tstLoading = false;
					this.$message({
						message: '测试消息已发送，请检查是否正确收到通知',
						type: 'success'
					});
				}).catch(err => {
					this.tstLoading = false;
				})
			},
			delCu(id) {
				this.$confirm("操作不可逆，将永久删除该通知配置，仍要删除吗？", '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					this.deleteLoading = true;
					delNotify(id).then(res => {
						this.deleteLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getData();
					}).catch(err => {
						this.deleteLoading = false;
					})
				});
			}
		}
	}
</script>

<style lang="scss">
	.tip-box {
		margin: 0 0 20px 100px;
		padding: 12px 14px;
		border: 1px solid var(--border-color);
		border-radius: 16px;
		background: var(--surface-soft);
		color: var(--text-muted);
		line-height: 1.7;

		a {
			color: var(--link-color);
			font-weight: 900;
			transition: color 0.2s ease;
		}

		a:hover {
			color: var(--link-hover-color);
		}
	}

	.notify {
		width: 100%;
		height: 100%;
		box-sizing: border-box;
		overflow-y: auto;
		padding: clamp(14px, 2.4vw, 28px);
	}

	.notify-shell {
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










	.notify-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: clamp(16px, 2vw, 24px);
	}

	.notify-card {
		min-height: 244px;
		border-radius: 32px;
		position: relative;
		overflow: hidden;
	}

	.notify-card {
		display: flex;
		flex-direction: column;
		gap: 18px;
		padding: 24px;
		border: 1px solid var(--border-color);
		background: linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
	}

	.notify-card:hover {
		transform: translateY(-3px);
		border-color: var(--border-light);
		box-shadow: var(--shadow-soft);
	}

	.notify-card::before {
		content: "";
		position: absolute;
		inset: 0 auto 0 0;
		width: 5px;
		background: linear-gradient(180deg, var(--brand), var(--accent));
	}

	.notify-card-glow {
		position: absolute;
		inset: -38% -28% auto auto;
		width: 190px;
		height: 190px;
		border-radius: 999px;
		background: var(--brand-soft);
		filter: blur(4px);
		pointer-events: none;
	}

	.notify-card-head {
		display: flex;
		align-items: center;
		gap: 16px;
		position: relative;
		z-index: 1;
	}

	.notify-logo-wrap {
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

	.notify-logo {
		width: 42px;
		height: 42px;
	}

	.notify-title-box {
		min-width: 0;
		flex: 1;
	}

	.notify-name-row {
		display: flex;
		align-items: center;
		gap: 10px;
		min-width: 0;
	}

	.notify-name {
		font-size: 23px;
		font-weight: 900;
		line-height: 1.1;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}




	.notify-subtitle {
		margin-top: 8px;
		font-size: 13px;
		font-weight: 800;
		line-height: 1.5;
		color: var(--text-muted);
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
	}

	.notify-meta {
		display: grid;
		grid-template-columns: 88px 1fr;
		gap: 10px;
		position: relative;
		z-index: 1;
	}

	.notify-meta-item {
		padding: 10px 12px;
		border-radius: 16px;
		background: color-mix(in srgb, var(--surface-soft) 76%, transparent);
	}

	.notify-meta-item span {
		display: block;
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .08em;
		color: var(--text-muted);
	}

	.notify-meta-item strong {
		display: block;
		margin-top: 5px;
		font-size: 13px;
		line-height: 1.35;
		color: var(--text-primary);
		word-break: break-all;
	}

	.notify-actions {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 8px;
		margin-top: auto;
		position: relative;
		z-index: 1;
	}

	.notify-actions .el-button {
		width: 100%;
		min-width: 0;
		margin-left: 0 !important;
		padding-left: 8px;
		padding-right: 8px;
		white-space: nowrap;
	}

	.notify-method-0 { --accent: #7fa5a1; }
	.notify-method-1 { --accent: #81a66e; }
	.notify-method-2 { --accent: #d39a46; }
	.notify-method-3 { --accent: #6f9c74; }
	.notify-method-4 { --accent: #6f8db8; }

	@media (max-width: 768px) {
		.notify {
			padding: 12px;
		}

		.page {
			margin-top: 10px;
			padding: 8px 0 2px;
			justify-content: center;
		}





		.notify-grid {
			grid-template-columns: 1fr;
		}

		.notify-card {
			min-height: auto;
			border-radius: 24px;
			padding: 18px;
		}

		.notify-card-head {
			align-items: flex-start;
		}

		.notify-logo-wrap {
			width: 54px;
			height: 54px;
			border-radius: 19px;
		}

		.notify-logo {
			width: 34px;
			height: 34px;
		}

		.notify-name {
			font-size: 20px;
		}

		.notify-meta {
			grid-template-columns: 1fr;
		}

		.notify-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.tip-box {
			margin: 0 0 15px 0;
			font-size: 12px;
		}

		::v-deep .el-dialog {
			width: calc(100vw - 20px) !important;
			margin: 10px auto 0 !important;
			top: 0 !important;
		}
	}

	@media (max-width: 420px) {

		.notify-actions {
			grid-template-columns: 1fr;
		}
	}
	/* notify-compact-row-card: align with job management cards */
	.notify-shell {
		gap: 12px !important;
	}







	.notify-grid {
		grid-template-columns: 1fr !important;
		gap: 10px !important;
	}

	.notify-card {
		display: grid !important;
		grid-template-columns: minmax(260px, .95fr) minmax(260px, 1fr) 340px;
		align-items: center;
		gap: 14px;
		min-height: 0 !important;
		padding: 14px !important;
		border-radius: 22px !important;
	}

	.notify-card::before {
		width: 4px;
	}

	.notify-card-glow {
		display: none;
	}

	.notify-card-head,
	.notify-meta,
	.notify-actions {
		position: relative;
		z-index: 1;
	}

	.notify-card-head {
		gap: 12px;
		min-width: 0;
	}

	.notify-logo-wrap {
		width: 54px;
		height: 54px;
		border-radius: 18px !important;
	}

	.notify-logo {
		width: 34px;
		height: 34px;
	}

	.notify-name {
		font-size: 19px;
	}

	.notify-subtitle {
		margin-top: 4px;
		font-size: 12px;
		-webkit-line-clamp: 1;
	}

	.notify-meta {
		grid-template-columns: 86px minmax(0, 1fr);
		gap: 6px;
	}

	.notify-meta-item {
		padding: 7px 9px;
		border-radius: 12px;
	}

	.notify-meta-item span {
		font-size: 10px;
	}

	.notify-meta-item strong {
		margin-top: 3px;
		font-size: 12px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.notify-actions {
		grid-template-columns: repeat(4, minmax(0, 1fr));
		align-content: center;
		gap: 7px !important;
		margin-top: 0;
	}

	.notify-actions .el-button {
		height: 32px;
		min-height: 32px;
		padding-left: 6px;
		padding-right: 6px;
	}


	@media (max-width: 1180px) {
		.notify-card {
			grid-template-columns: minmax(240px, 1fr) minmax(260px, 1fr);
		}

		.notify-actions {
			grid-column: 1 / -1;
		}
	}

	@media (max-width: 768px) {

		.notify-card {
			grid-template-columns: 1fr;
			gap: 10px;
			padding: 14px !important;
		}

		.notify-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

	}

	@media (max-width: 420px) {

		.notify-actions {
			grid-template-columns: 1fr;
		}
	}

	/* management-page-alignment-v2 */




	.notify-card {
		grid-template-columns: 76px minmax(230px, .9fr) minmax(260px, 1fr) 340px !important;
		align-items: center;
	}

	.notify-card-head {
		display: contents;
	}

	.notify-logo-wrap {
		position: relative;
		z-index: 1;
		grid-column: 1;
		justify-self: center;
	}

	.notify-title-box {
		position: relative;
		z-index: 1;
		grid-column: 2;
		min-width: 0;
	}

	.notify-meta {
		grid-column: 3;
	}

	.notify-actions {
		grid-column: 4;
		align-self: stretch;
		align-content: center;
	}

	.notify-meta-item,
	.notify-actions .el-button {
		border-radius: 14px;
	}

	@media (max-width: 1180px) {

		.notify-card {
			grid-template-columns: 64px minmax(220px, 1fr) minmax(260px, 1fr) !important;
		}

		.notify-logo-wrap { grid-column: 1; }
		.notify-title-box { grid-column: 2; }
		.notify-meta { grid-column: 3; }
		.notify-actions { grid-column: 1 / -1; }
	}

	@media (max-width: 768px) {

		.notify-logo-wrap,
		.notify-title-box,
		.notify-meta,
		.notify-actions {
			grid-column: auto;
		}

		.notify-card-head {
			display: flex;
		}
	}


	/* overview-boundary-fix */








	@media (max-width: 768px) {
	}

	/* notify-list-polish-v3: align list density with job management */
	.notify-grid {
		display: grid !important;
		grid-template-columns: 1fr !important;
		gap: 10px !important;
	}

	.notify-card {
		display: grid !important;
		grid-template-columns: 72px minmax(220px, .85fr) minmax(240px, 1fr) minmax(300px, 332px) !important;
		align-items: stretch;
		gap: 12px;
		min-height: 0 !important;
		padding: 12px !important;
		border-radius: 22px !important;
		overflow: hidden;
	}

	.notify-card::before {
		width: 4px;
	}

	.notify-card-glow {
		display: none;
	}

	.notify-card-head {
		display: contents !important;
	}

	.notify-logo-wrap,
	.notify-title-box,
	.notify-meta,
	.notify-actions {
		position: relative;
		z-index: 1;
		min-width: 0;
	}

	.notify-logo-wrap {
		grid-column: 1;
		justify-self: center;
		align-self: center;
		width: 54px;
		height: 54px;
		border-radius: 18px !important;
	}

	.notify-logo {
		width: 34px;
		height: 34px;
	}

	.notify-title-box {
		grid-column: 2;
		align-self: center;
	}

	.notify-name-row {
		gap: 8px;
	}

	.notify-name {
		font-size: 18px;
		letter-spacing: -.025em;
	}


	.notify-subtitle {
		margin-top: 5px;
		font-size: 12px;
		line-height: 1.45;
		-webkit-line-clamp: 2;
	}

	.notify-meta {
		grid-column: 3;
		display: grid;
		grid-template-columns: 86px minmax(0, 1fr);
		align-self: center;
		gap: 6px;
	}

	.notify-meta-item {
		min-width: 0;
		padding: 7px 9px;
		border-radius: 12px;
	}

	.notify-meta-item span {
		font-size: 10px;
	}

	.notify-meta-item strong {
		margin-top: 3px;
		font-size: 12px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		word-break: normal;
	}

	.notify-actions {
		grid-column: 4;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		align-content: center;
		align-self: stretch;
		gap: 7px !important;
		margin-top: 0;
	}

	.notify-actions .el-button {
		width: 100%;
		min-height: 32px;
		padding-left: 8px;
		padding-right: 8px;
		border-radius: 14px !important;
	}

	.notify-empty-state {
		box-sizing: border-box;
	}

	.notify-loading-state {
		grid-column: 1 / -1;
		position: relative;
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		gap: 14px;
		min-height: 92px;
		padding: 14px;
		border: 1px solid var(--border-color);
		border-radius: 22px;
		background:
			radial-gradient(circle at 12% 18%, var(--brand-soft), transparent 16rem),
			linear-gradient(145deg, var(--surface-raised), var(--bg-secondary));
		box-shadow: var(--shadow-card);
		overflow: hidden;
		box-sizing: border-box;
	}

	.notify-loading-mark {
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

	.notify-loading-copy {
		min-width: 0;
	}

	.notify-loading-title {
		font-size: 18px;
		font-weight: 900;
		color: var(--text-primary);
	}

	.notify-loading-desc {
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
	}

	.notify-loading-state::after {
		content: "";
		position: absolute;
		inset: 0;
		transform: translateX(-110%);
		background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--brand-soft) 62%, transparent), transparent);
		animation: notifyLoadingSweep 1.35s ease-in-out infinite;
		pointer-events: none;
	}

	@keyframes notifyLoadingSweep {
		to {
			transform: translateX(110%);
		}
	}

	@media (max-width: 1180px) {
		.notify-card {
			grid-template-columns: 62px minmax(220px, 1fr) minmax(240px, 1fr) !important;
		}

		.notify-actions {
			grid-column: 1 / -1;
			grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
		}
	}

	@media (max-width: 768px) {
		.notify-card {
			grid-template-columns: 1fr !important;
			padding: 14px !important;
		}

		.notify-card-head {
			display: flex !important;
			align-items: flex-start;
		}

		.notify-logo-wrap,
		.notify-title-box,
		.notify-meta,
		.notify-actions {
			grid-column: auto;
		}

		.notify-logo-wrap {
			justify-self: flex-start;
		}

		.notify-meta {
			grid-template-columns: 1fr;
		}

		.notify-actions {
			grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		}

		.notify-loading-state {
			grid-template-columns: 1fr;
			justify-items: center;
			text-align: center;
		}

	}

	@media (max-width: 420px) {
		.notify-actions {
			grid-template-columns: 1fr !important;
		}
	}

	/* notify-dialog-lock: keep footer stable and stop outside wheel drift */
	body.notify-dialog-open {
		overflow: hidden;
	}

	.notify-form-dialog {
		overflow: hidden;
	}

	.notify-form-dialog .el-dialog__body {
		overflow-x: hidden;
		overflow-y: auto;
	}

	.notify-form-dialog .dialog-footer {
		flex-wrap: wrap;
		padding-top: 2px;
	}

	.notify-form-dialog .dialog-footer .el-button {
		min-width: 0;
	}

	@media (max-width: 768px) {
		.notify-form-dialog .dialog-footer {
			align-items: stretch;
		}
	}

</style>



