<template>
	<div class="taskDetailTable">
		<div class="card-list-container" v-loading="loading && hasRows" element-loading-text="正在刷新明细...">
			<div v-if="!hasRows" class="state-panel" :class="{ 'is-loading': stateLoading, 'is-empty': !stateLoading }">
				<div class="state-mark">
					<i :class="stateLoading ? 'el-icon-loading' : 'el-icon-document-remove'"></i>
				</div>
				<div class="state-copy">
					<div class="state-title">{{ stateLoading ? '正在读取任务明细' : '当前没有明细记录' }}</div>
					<div class="state-desc">{{ stateText }}</div>
				</div>
			</div>
			<template v-else>
				<div v-for="(item, index) in taskItemData.dataList" :key="index" class="task-card">
					<div class="card-main" @click="toggleExpand(index)">
						<i :class="getFileIconClass(item)" class="file-icon"></i>
						<div class="file-content">
							<div class="file-name-line">
								<span class="file-name">{{ item.fileName || item.dstPath }}</span>
								<span class="status-badge" v-if="item.status != 1">
									<div :class="`bg-status bg-${item.status}`">
										<span v-if="item.status != 7">
											{{ item.status | taskItemStatusFilter }}
										</span>
										<el-popover v-else placement="top-end" title="错误原因" width="200" trigger="hover"
											:content="item.errMsg" @show.native.stop>
											<span slot="reference" @click.stop>失败，<span class="link-text-inline">原因</span></span>
										</el-popover>
									</div>
								</span>
								<el-progress v-else :stroke-width="16" :text-inside="true"
									color="rgba(64, 158, 255, .8)" text-color="#fff"
									define-back-color="rgba(64, 158, 255, .3)"
									:percentage="Number(Number(item.progress).toFixed(3))"
									class="progress-bar"></el-progress>
							</div>
							<div class="file-meta-line">
								<span class="operation-type">
									<div :class="`bg-status bg-${item.type ? '3' : '8'}`">
										{{ getOperationType(item) }}
									</div>
								</span>
								<span class="file-size">{{ item.fileSize | sizeFilter }}</span>
								<span :class="['expand-icon', { 'expanded': expandedIndex === index }]">
									<i class="el-icon-arrow-down"></i>
								</span>
							</div>
						</div>
					</div>
					<div v-show="expandedIndex === index" class="card-detail" @click.stop>
						<div class="form-box">
							<div class="form-box-item" v-if="item.type != 1">
								<div class="form-box-item-label">
									来源目录
								</div>
								<div class="form-box-item-value">
									{{ item.srcPath }}
								</div>
							</div>
							<div class="form-box-item">
								<div class="form-box-item-label">
									目标目录
								</div>
								<div class="form-box-item-value">
									{{ item.dstPath }}
								</div>
							</div>
							<div class="form-box-item">
								<div class="form-box-item-label">
									创建时间
								</div>
								<div class="form-box-item-value">
									{{ item.createTime | timeStampFilter }}
								</div>
							</div>
						</div>
					</div>
				</div>
			</template>
		</div>
		<div class="page">
			<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
				:current-page="params.pageNum" :page-size="params.pageSize" :total="taskItemData.count"
				:layout="paginationLayout" :page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
	</div>
</template>

<script>
export default {
	name: 'TaskDetailTable',
	props: {
		taskItemData: {
			type: Object,
			default: {
				dataList: [],
				conut: 0
			}
		},
		loading: {
			type: Boolean,
			default: false
		},
		hasLoaded: {
			type: Boolean,
			default: false
		}
	},
	data() {
		return {
			params: {
				pageSize: 10,
				pageNum: 1
			},
			expandedIndex: null,
			isMobile: false
		};
	},
	computed: {
		hasRows() {
			return !!(this.taskItemData && this.taskItemData.dataList && this.taskItemData.dataList.length > 0);
		},
		stateLoading() {
			return !this.hasLoaded || this.loading;
		},
		stateText() {
			return this.stateLoading ? '正在同步最新数据，请稍等片刻。' : '当前筛选条件下没有匹配记录，换个条件再看。';
		},
		paginationLayout() {
			return this.isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper';
		}
	},
	mounted() {
		this.checkMobile();
		window.addEventListener('resize', this.checkMobile);
	},
	beforeDestroy() {
		window.removeEventListener('resize', this.checkMobile);
	},
	methods: {
		checkMobile() {
			this.isMobile = window.innerWidth <= 768;
		},
		handleSizeChange(val) {
			this.params.pageSize = val;
			this.$emit("pageChange", this.params);
		},
		handleCurrentChange(val) {
			this.params.pageNum = val;
			this.$emit("pageChange", this.params);
		},
		toggleExpand(index) {
			this.expandedIndex = this.expandedIndex === index ? null : index;
		},
		getFileIconClass(item) {
			if (item.isPath) {
				return 'el-icon-folder';
			}

			const fileName = item.fileName || item.dstPath || '';
			const lastDotIndex = fileName.lastIndexOf('.');
			if (lastDotIndex === -1 || lastDotIndex === fileName.length - 1) {
				return 'el-icon-document';
			}

			const ext = fileName.substring(lastDotIndex + 1).toLowerCase();
			const iconMap = {
				'jpg': 'el-icon-picture',
				'jpeg': 'el-icon-picture',
				'png': 'el-icon-picture',
				'gif': 'el-icon-picture',
				'bmp': 'el-icon-picture',
				'webp': 'el-icon-picture',
				'svg': 'el-icon-picture',
				'ico': 'el-icon-picture',
				'heic': 'el-icon-picture',
				'heif': 'el-icon-picture',
				'mp4': 'el-icon-video-camera',
				'avi': 'el-icon-video-camera',
				'mkv': 'el-icon-video-camera',
				'mov': 'el-icon-video-camera',
				'wmv': 'el-icon-video-camera',
				'flv': 'el-icon-video-camera',
				'webm': 'el-icon-video-camera',
				'm4v': 'el-icon-video-camera',
				'mp3': 'el-icon-headset',
				'wav': 'el-icon-headset',
				'flac': 'el-icon-headset',
				'aac': 'el-icon-headset',
				'ogg': 'el-icon-headset',
				'm4a': 'el-icon-headset',
				'wma': 'el-icon-headset',
				'pdf': 'el-icon-document',
				'doc': 'el-icon-document',
				'docx': 'el-icon-document',
				'xls': 'el-icon-document',
				'xlsx': 'el-icon-document',
				'ppt': 'el-icon-document',
				'pptx': 'el-icon-document',
				'txt': 'el-icon-document',
				'rtf': 'el-icon-document',
				'md': 'el-icon-document',
				'zip': 'el-icon-box',
				'rar': 'el-icon-box',
				'7z': 'el-icon-box',
				'tar': 'el-icon-box',
				'gz': 'el-icon-box',
				'bz2': 'el-icon-box',
				'js': 'el-icon-document',
				'ts': 'el-icon-document',
				'html': 'el-icon-document',
				'css': 'el-icon-document',
				'vue': 'el-icon-document',
				'py': 'el-icon-document',
				'java': 'el-icon-document',
				'cpp': 'el-icon-document',
				'c': 'el-icon-document',
				'go': 'el-icon-document',
				'php': 'el-icon-document',
				'xml': 'el-icon-document',
				'json': 'el-icon-document',
			};

			return iconMap[ext] || 'el-icon-document';
		},
		getOperationType(item) {
			if (item.type == 0) {
				return item.isPath ? '创建' : '复制';
			} else if (item.type == 1) {
				return '删除';
			} else {
				return '移动';
			}
		}
	}
}
</script>

<style lang="scss" scoped>
	.taskDetailTable {
		height: 100%;
		display: flex;
		flex-direction: column;
		min-height: 0;
		overflow: hidden;

		.card-list-container {
			flex: 1;
			min-height: 0;
			overflow-y: auto;
			padding: 10px 2px 12px 0;

			.state-panel {
				position: relative;
				display: grid;
				grid-template-columns: auto minmax(0, 1fr);
				align-items: center;
				gap: 14px;
				min-height: 120px;
				margin-bottom: 8px;
				padding: 16px;
				border: 1px solid var(--border-color);
				border-radius: 18px;
				box-sizing: border-box;
				overflow: hidden;
				background:
					radial-gradient(circle at 14% 18%, color-mix(in srgb, var(--link-color) 7%, transparent), transparent 18rem),
					var(--bg-secondary);
			}

			.state-panel.is-loading {
				border-color: color-mix(in srgb, var(--link-color) 18%, var(--border-color));
			}

			.state-panel.is-loading::after {
				content: "";
				position: absolute;
				inset: 0;
				transform: translateX(-110%);
				background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--link-color) 16%, transparent), transparent);
				animation: taskDetailSweep 1.3s ease-in-out infinite;
				pointer-events: none;
			}

			.state-mark {
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

			.state-panel.is-loading .state-mark {
				background: color-mix(in srgb, var(--link-color) 10%, var(--bg-tertiary));
				color: var(--link-color);
			}

			.state-panel.is-empty {
				border-color: var(--border-color);
			}

			.state-copy {
				min-width: 0;
			}

			.state-title {
				font-size: 16px;
				font-weight: 800;
				color: var(--text-primary);
			}

			.state-desc {
				margin-top: 4px;
				font-size: 13px;
				line-height: 1.65;
				color: var(--text-muted);
			}

			.task-card {
				background-color: var(--bg-secondary);
				border: 1px solid var(--border-color);
				border-radius: 8px;
				margin-bottom: 8px;
				overflow: hidden;
				transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
				backdrop-filter: blur(10px);

				&:hover {
					border-color: var(--border-light);
					box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
					transform: translateY(-1px);
				}

				.card-main {
					display: flex;
					align-items: flex-start;
					gap: 12px;
					padding: 10px 14px;
					cursor: pointer;
					user-select: none;
					transition: background-color 0.2s ease;

					&:hover {
						background-color: var(--bg-tertiary);
					}

					.file-icon {
						font-size: 20px;
						flex-shrink: 0;
						margin-top: 2px;
						color: var(--text-secondary);
						transition: color 0.2s ease, transform 0.2s ease;
						display: inline-flex;
						align-items: center;
						justify-content: center;
					}

					&:hover .file-icon {
						color: var(--text-primary);
						transform: scale(1.05);
					}

					.file-content {
						flex: 1;
						min-width: 0;
						display: flex;
						flex-direction: column;
						gap: 6px;

						.file-name-line {
							display: flex;
							align-items: center;
							gap: 10px;
							min-width: 0;

							.file-name {
								font-size: 14px;
								color: var(--text-primary);
								font-weight: 500;
								overflow: hidden;
								text-overflow: ellipsis;
								white-space: nowrap;
								flex: 1;
								min-width: 0;
								letter-spacing: -0.01em;
								line-height: 1.4;
								max-width: 100%;
							}

							.status-badge {
								flex-shrink: 0;
								margin-left: auto;

								.bg-status {
									padding: 3px 10px;
									font-size: 12px;
									white-space: nowrap;
									font-weight: 500;
									letter-spacing: 0.02em;
									border-radius: 4px;
								}
							}

							.progress-bar {
								width: 130px;
								flex-shrink: 0;
								margin-left: auto;

								::v-deep .el-progress-bar__outer {
									border-radius: 6px;
									overflow: hidden;
								}

								::v-deep .el-progress-bar__inner {
									border-radius: 6px;
								}
							}
						}

						.file-meta-line {
							display: flex;
							align-items: center;
							gap: 10px;
							min-width: 0;

							.file-size {
								font-size: 12px;
								color: var(--text-secondary);
								flex-shrink: 0;
								font-weight: 400;
								letter-spacing: 0.01em;
							}

							.operation-type {
								flex-shrink: 0;

								.bg-status {
									padding: 3px 10px;
									font-size: 12px;
									white-space: nowrap;
									font-weight: 500;
									letter-spacing: 0.02em;
									border-radius: 4px;
								}
							}

							.expand-icon {
								display: inline-flex;
								align-items: center;
								justify-content: center;
								width: 24px;
								height: 24px;
								font-size: 12px;
								color: var(--text-muted);
								transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
								cursor: pointer;
								margin-left: auto;
								flex-shrink: 0;
								border-radius: 50%;
								background-color: transparent;
								opacity: 0.7;

								&:hover {
									opacity: 1;
									background-color: var(--bg-tertiary);
									color: var(--text-primary);
								}

								&.expanded {
									transform: rotate(180deg);
									opacity: 1;
								}
							}
						}
					}
				}

				.card-detail {
					border-top: 1px solid var(--border-color);
					background-color: color-mix(in srgb, var(--bg-secondary) 94%, var(--bg-tertiary));
					overflow: hidden;
					animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
				}
			}

			.form-box {
				padding: 14px 18px;
				display: grid;
				gap: 10px;

				.form-box-item {
					display: grid;
					grid-template-columns: 88px minmax(0, 1fr);
					align-items: start;
					gap: 10px;

					.form-box-item-label {
						font-size: 12px;
						color: var(--text-muted);
						line-height: 1.6;
					}

					.form-box-item-value {
						font-size: 13px;
						color: var(--text-primary);
						line-height: 1.6;
						word-break: break-all;
					}
				}
			}
		}

		.page {
			flex: 0 0 auto;
			display: flex;
			justify-content: flex-end;
			padding-top: 10px;
		}

		.link-text-inline {
			color: var(--link-color);
		}
	}

	@keyframes taskDetailSweep {
		to {
			transform: translateX(110%);
		}
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}

		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 768px) {
		.taskDetailTable {
			.card-list-container {
				padding: 10px 0 12px;
				-ms-overflow-style: none;
			}

			.card-list-container::-webkit-scrollbar {
				width: 0;
				height: 0;
				display: none;
			}

			.state-panel {
				grid-template-columns: 1fr;
				justify-items: center;
				text-align: center;
				padding: 14px 12px;
			}

			.state-mark {
				width: 48px;
				height: 48px;
				font-size: 20px;
			}

			.form-box {
				padding: 12px 14px;

				.form-box-item {
					grid-template-columns: 1fr;
					gap: 4px;
				}
			}

			.page {
				justify-content: center;
				padding-bottom: 0;
			}
		}
	}
</style>
