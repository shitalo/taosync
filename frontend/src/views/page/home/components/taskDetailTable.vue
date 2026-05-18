<template>
	<div class="taskDetailTable">
		<div class="card-list-container" v-loading="loading" element-loading-text="加载中...">
			<div v-if="!loading && (!taskItemData.dataList || taskItemData.dataList.length === 0)" class="empty-text">
				无数据
			</div>
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
			paginationLayout() {
				return this.isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper';
			}
		},
		created() {},
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
				// 如果是目录
				if (item.isPath) {
					return 'el-icon-folder';
				}
				
				// 获取文件名
				const fileName = item.fileName || item.dstPath || '';
				
				// 获取文件扩展名（处理没有扩展名或扩展名为空的情况）
				const lastDotIndex = fileName.lastIndexOf('.');
				if (lastDotIndex === -1 || lastDotIndex === fileName.length - 1) {
					// 没有扩展名或扩展名为空，返回默认文档图标
					return 'el-icon-document';
				}
				
				const ext = fileName.substring(lastDotIndex + 1).toLowerCase();
				
				// 根据文件扩展名返回对应的图标类
				const iconMap = {
					// 图片
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
					// 视频
					'mp4': 'el-icon-video-camera',
					'avi': 'el-icon-video-camera',
					'mkv': 'el-icon-video-camera',
					'mov': 'el-icon-video-camera',
					'wmv': 'el-icon-video-camera',
					'flv': 'el-icon-video-camera',
					'webm': 'el-icon-video-camera',
					'm4v': 'el-icon-video-camera',
					// 音频
					'mp3': 'el-icon-headset',
					'wav': 'el-icon-headset',
					'flac': 'el-icon-headset',
					'aac': 'el-icon-headset',
					'ogg': 'el-icon-headset',
					'm4a': 'el-icon-headset',
					'wma': 'el-icon-headset',
					// 文档
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
					// 压缩包
					'zip': 'el-icon-box',
					'rar': 'el-icon-box',
					'7z': 'el-icon-box',
					'tar': 'el-icon-box',
					'gz': 'el-icon-box',
					'bz2': 'el-icon-box',
					// 代码文件
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
				
				// 如果有匹配的图标，返回对应的类名
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
			
			.empty-text {
				text-align: center;
				padding: 40px 0;
				color: var(--text-muted);
				font-size: 14px;
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
									background-color: rgba(128, 128, 128, 0.1);
									color: var(--text-primary);
									opacity: 1;
								}

								i {
									transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
								}

								&.expanded {
									opacity: 1;
									
									i {
										transform: rotate(180deg);
									}
								}
							}
						}
					}
				}

				.card-detail {
					border-top: 1px solid var(--border-color);
					background-color: var(--bg-tertiary);
					padding: 12px 14px;
					animation: slideDown 0.35s cubic-bezier(0.4, 0, 0.2, 1);
				}
			}
		}

		.page {
			flex: 0 0 auto;
			margin-top: 0;
			padding: 10px 0 2px;
			border-top: 1px solid var(--border-color);
			background: color-mix(in srgb, var(--bg-primary) 82%, transparent);
			display: flex;
			justify-content: flex-end;
			align-items: center;
			min-height: 46px;
			box-sizing: border-box;
			overflow: hidden;
		}

		.page ::v-deep .el-pagination {
			white-space: normal;
		}
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			max-height: 0;
			transform: translateY(-8px);
		}
		to {
			opacity: 1;
			max-height: 500px;
			transform: translateY(0);
		}
	}

	.form-box {
		display: flex;
		flex-direction: column;
		gap: 8px;

		.form-box-item {
			display: flex;
			align-items: flex-start;
			padding: 2px 0;

			.form-box-item-label {
				font-size: 12px;
				width: 75px;
				text-align: right;
				margin-right: 14px;
				color: var(--text-muted);
				flex-shrink: 0;
				padding-top: 2px;
				font-weight: 400;
				letter-spacing: 0.01em;
			}

			.form-box-item-value {
				flex: 1;
				font-size: 12px;
				color: var(--text-primary);
				word-break: break-all;
				line-height: 1.4;
				letter-spacing: -0.01em;
				overflow-wrap: break-word;
				min-width: 0;
			}
		}

		.link-text-inline {
			color: var(--link-color);
		}
	}

	// 移动端适配
	@media (max-width: 768px) {
		.taskDetailTable {
			overflow-x: hidden;

			.card-list-container {
				padding-right: 0;
				scrollbar-width: none;
				-ms-overflow-style: none;
			}

			.page {
				justify-content: center;
				padding-bottom: 0;
				scrollbar-width: none;
				-ms-overflow-style: none;
			}

			.page ::v-deep .el-pagination {
				display: flex;
				flex-wrap: wrap;
				align-items: center;
				justify-content: center;
				row-gap: 8px;
				width: 100%;
				max-width: 100%;
				min-width: 0;
			}

			.page ::v-deep .el-pagination > * {
				min-width: 0;
			}

			.card-list-container::-webkit-scrollbar,
			.page::-webkit-scrollbar {
				width: 0;
				height: 0;
				display: none;
			}

			.card-item {
				padding: 8px 10px;

				.file-content {
					.file-icon {
						font-size: 18px;
					}

					.file-name {
						font-size: 13px;
					}

					.file-status,
					.file-size,
					.file-type {
						font-size: 11px;
					}
				}

				.card-detail {
					padding: 10px 12px;

					.form-box-item {
						flex-direction: column;
						align-items: flex-start;
						gap: 4px;

						.form-box-item-label {
							width: auto;
							margin-right: 0;
							text-align: left;
						}
					}
				}
			}
		}
	}
</style>
