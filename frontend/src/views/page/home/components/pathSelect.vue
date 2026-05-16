<template>
	<div class="pathSelect">
		<el-dialog top="8vh" :close-on-click-modal="false" :visible.sync="dialogShow" title="选择目录" width="520px"
			custom-class="tao-dialog tao-picker-dialog path-picker-dialog" :before-close="closeShow" :append-to-body="true">
			<el-tree :props="props" :load="loadNode" lazy :highlight-current="true" :check-on-click-node="true"
				@node-click="nodeClick" v-if="dialogShow">
			</el-tree>
			<span slot="footer" class="dialog-footer">
				<el-button @click="closeShow">取 消</el-button>
				<el-button type="primary" @click="submit" :loading="submitLoading"
					:disabled="cuPath == null">{{cuPath == null ? '请先选择路径' : '确定'}}</el-button>
			</span>
		</el-dialog>
	</div>
</template>

<script>
	import {
		openlistGetPath
	} from "@/api/job";
	export default {
		name: 'PathSelect',
		components: {},
		props: {
			openlistId: {
				type: Number,
				default: null
			}
		},
		data() {
			return {
				dialogShow: false,
				pathLoading: false,
				submitLoading: false,
				cuPath: null,
				props: {
					label: 'path',
					children: 'child',
					isLeaf: 'leaf'
				}
			};
		},
		created() {},
		beforeDestroy() {},
		methods: {
			show() {
				this.dialogShow = true;
			},
			async getPath(path) {
				this.pathLoading = true;
				try {
					let res = await openlistGetPath(this.openlistId, path);
					this.pathLoading = false;
					return res.data;
				} catch (err) {
					return [];
					this.pathLoading = false;
				}
			},
			async loadNode(node, resolve) {
				let path = '/';
				let cup = node;
				for (let i = 0; i < node.level; i++) {
					path = '/' + cup.data.path + path;
					cup = cup.parent;
				}
				return resolve(await this.getPath(path));
			},
			closeShow() {
				this.dialogShow = false;
				this.cuPath = null;
			},
			nodeClick(dt, node, se) {
				let path = '/';
				let cup = node;
				for (let i = 0; i < node.level; i++) {
					path = '/' + cup.data.path + path;
					cup = cup.parent;
				}
				this.cuPath = path;
			},
			submit() {
				this.$emit('submit', this.cuPath);
				this.closeShow();
			}
		}
	}
</script>

<style lang="scss" scoped>
	.pathSelect {}

	// 移动端适配
	@media (max-width: 768px) {
		::v-deep .el-dialog {
			width: 90% !important;
			margin: 5vh auto 0 !important;

			.el-dialog__body {
				padding: 15px;
				max-height: 60vh;
				overflow-y: auto;
			}
		}
	}
</style>
