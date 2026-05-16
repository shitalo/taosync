<template>
	<el-dialog :close-on-click-modal="false" :visible="visible" :append-to-body="true"
		:title="`${editData && editData.id != null ? '编辑' : '新增'}作业`" :width="dialogWidth" :before-close="handleClose"
		:top="isMobile ? '0' : '0'" :custom-class="'job-editor-dialog'">
		<div class="elform-box">
			<div class="job-editor-hero">
				<div>
					<div class="job-editor-kicker">JOB WORKBENCH</div>
					<div class="job-editor-title">{{editData && editData.id != null ? '调整同步作业' : '创建同步作业'}}</div>
					<div class="job-editor-desc">先选择引擎与目录，再配置同步策略；滚轮只滚动表单区域，底部操作始终可见。</div>
				</div>
				<div class="job-editor-mode">
					<span>{{editData && editData.id != null ? '编辑模式' : '新建模式'}}</span>
				</div>
			</div>
			<el-form :model="editData" :rules="rules" ref="jobRule" v-if="visible && editData" :label-width="isMobile ? 'auto' : '150px'">
				<div class="form-items-wrapper">
					<el-form-item prop="enable" label="是否启用">
						<div class="enable-switch-wrapper">
							<el-switch
								v-model="editData.enable"
								:active-value="1"
								:inactive-value="0"
								:disabled="editData.isCron == 2"
								active-text="启用"
								inactive-text="禁用"
								class="light-switch">
							</el-switch>
							<span v-if="editData.isCron == 2" class="enable-disabled-tip"><i class="el-icon-info"></i><span>手动调用不会自动运行，作业保持可执行状态</span></span>
						</div>
					</el-form-item>
					<el-form-item prop="openlistId" label="引擎">
						<el-select v-model="editData.openlistId" placeholder="请选择引擎"
							no-data-text="暂无引擎,请前往引擎管理创建" style="width: 100%;">
							<el-option v-for="item in openlistList" :key="item.id" :label="item.url" :value="item.id">
								<span style="float: left;margin-right: 16px;">{{item.url}}{{item.remark != null ? `[${item.remark}]` : ''}}</span>
								<span class="option-desc">{{item.userName}}</span>
							</el-option>
						</el-select>
					</el-form-item>
					<el-form-item prop="srcPath" label="源目录">
						<div v-if="editData.openlistId == null" style="color: var(--text-primary, #303133);">请先选择引擎</div>
						<div v-else class="label_width">
							<div class="path-list-wrapper">
								<div v-if="editData.srcPath" class="path-item">
									<div class="path-item-content path-item-src" :title="editData.srcPath">
										<i class="el-icon-folder path-icon"></i>
										<span class="path-text">{{editData.srcPath}}</span>
									</div>
								</div>
								<el-button type="primary" size="small" class="path-select-btn" @click="$emit('select-path', true)">
									<i class="el-icon-folder-opened"></i>
									{{editData.srcPath ? '更换目录' : '选择目录'}}
								</el-button>
							</div>
						</div>
					</el-form-item>
					<el-form-item prop="dstPath" label="目标目录">
						<div v-if="editData.openlistId == null" class="label_width" style="color: var(--text-primary, #303133);">请先选择引擎</div>
						<div v-else class="label_width">
							<div class="path-list-wrapper">
								<div v-for="(item, index) in editData.dstPath" :key="index" class="path-item">
									<div class="path-item-content path-item-dst" :title="item">
										<i class="el-icon-folder path-icon"></i>
										<span class="path-text">{{item}}</span>
										<el-button type="text" icon="el-icon-close" size="mini" class="path-remove-btn" @click="$emit('delete-dst-path', index)" title="删除"></el-button>
									</div>
								</div>
								<el-button type="primary" size="small" class="path-select-btn" @click="$emit('select-path', false)">
									<i class="el-icon-folder-opened"></i>
									{{editData.dstPath.length == 0 ? '选择目录' : '添加目录'}}
								</el-button>
							</div>
						</div>
					</el-form-item>
					<el-form-item prop="remark" label="作业名称">
						<div class="label_width" style="width: 100%;">
							<el-input v-model="editData.remark" placeholder="用来标识你的作业，选填" style="width: 100%;"></el-input>
						</div>
					</el-form-item>
					<el-form-item prop="method" label="同步方法">
						<el-select v-model="editData.method" class="label_width" style="width: 100%;">
							<el-option label="仅新增" :value="0">
								<span style="float: left;margin-right: 16px;">仅新增</span>
								<span class="option-desc">仅新增目标目录没有的文件</span>
							</el-option>
							<el-option label="全同步" :value="1">
								<span style="float: left;margin-right: 16px;">全同步</span>
								<span class="option-desc">目标目录比源目录多的文件将被删除</span>
							</el-option>
							<el-option label="移动模式" :value="2">
								<span style="float: left;margin-right: 16px;">移动模式</span>
								<span class="option-desc">同步完成后删除源目录所有文件</span>
							</el-option>
						</el-select>
					</el-form-item>
					<el-form-item prop="useCacheT" label="目标目录扫描缓存">
						<el-select v-model="editData.useCacheT" class="label_width" style="width: 100%;">
							<el-option label="不使用" :value="0">
								<span style="float: left;margin-right: 16px;">不使用</span>
								<span class="option-desc">如果会对目标目录手动操作，选这个，但更容易被网盘限制</span>
							</el-option>
							<el-option label="使用" :value="1">
								<span style="float: left;margin-right: 16px;">使用</span>
								<span class="option-desc">推荐，降低网盘风控可能</span>
							</el-option>
						</el-select>
					</el-form-item>
					<el-form-item prop="scanIntervalT" label="目标目录操作间隔">
						<el-input v-model.number="editData.scanIntervalT" placeholder="目标目录操作间隔" class="label_width" style="width: 100%;">
							<template slot="append">秒</template>
						</el-input>
					</el-form-item>
					<el-form-item prop="useCacheS" label="源目录扫描缓存">
						<el-select v-model="editData.useCacheS" class="label_width" style="width: 100%;">
							<el-option label="不使用" :value="0">
								<span style="float: left;margin-right: 16px;">不使用</span>
								<span class="option-desc">用这个</span>
							</el-option>
							<el-option label="使用" :value="1">
								<span style="float: left;margin-right: 16px;">使用</span>
								<span class="option-desc">不要用，除非你知道自己在做什么</span>
							</el-option>
						</el-select>
					</el-form-item>
					<el-form-item prop="scanIntervalS" label="源目录操作间隔">
						<el-input v-model.number="editData.scanIntervalS" placeholder="源目录操作间隔" class="label_width" style="width: 100%;">
							<template slot="append">秒</template>
						</el-input>
					</el-form-item>
					<el-form-item prop="exclude" label="排除项语法" class="form-item-full-width">
						<div class="label_width" style="color: var(--text-primary, #303133);">类gitignore<br />
							<span @click="$emit('open-ignore-help')" class="to-link">点击查看排除项简易教程</span>
						</div>
					</el-form-item>
					<el-form-item prop="exclude" label="排除项规则" class="form-item-full-width">
						<div class="label_width" style="width: 100%;">
							<div class="label-list-box">
								<el-input v-model="excludeTmp" placeholder="输入后点添加才生效" style="width: 100%;">
									<el-button slot="append" @click="handleAddExclude">添加</el-button>
								</el-input>
								<div v-for="(item, index) in editData.exclude" :key="`${item}-${index}`" class="label-list-item">
									<div class="bg-3 label-list-item-left">{{item}}</div>
									<el-button type="danger" size="mini" @click="$emit('delete-exclude', index)">删除</el-button>
								</div>
							</div>
						</div>
					</el-form-item>
					<div v-if="editData.method == 2" class="method-warning-wrapper form-item-full-width">
						<span class="method-warning">移动模式存在风险，可能导致文件丢失（因为会删除源目录文件），该方法应仅用于不重要的文件或有多重备份的文件！希望你知道自己在做什么！</span>
					</div>
					<el-form-item prop="isCron" label="调用方式">
						<el-select v-model="editData.isCron" class="label_width" style="width: 100%;">
							<el-option label="间隔" :value="0">
								<span style="float: left;margin-right: 16px;">间隔</span>
								<span class="option-desc">每n分钟同步一次</span>
							</el-option>
							<el-option label="cron" :value="1">
								<span style="float: left;margin-right: 16px;">cron</span>
								<span class="option-desc">推荐使用，有教程</span>
							</el-option>
							<el-option label="仅手动" :value="2">
								<span style="float: left;margin-right: 16px;">仅手动</span>
								<span class="option-desc">不自动调用</span>
							</el-option>
							<el-option label="时间段" :value="3">
								<span style="float: left;margin-right: 16px;">时间段</span>
								<span class="option-desc">在指定时间段内自动运行，到点自动停止</span>
							</el-option>
						</el-select>
					</el-form-item>
					<template v-if="editData.isCron == 0">
						<el-form-item prop="interval" label="同步间隔">
							<el-input v-model.number="editData.interval" placeholder="请输入同步间隔" class="label_width" style="width: 100%;">
								<template slot="append">分钟</template>
							</el-input>
						</el-form-item>
						<div class="interval-tip-wrapper form-item-full-width">
							<span class="interval-tip">间隔方式不会立即调用，如有需要，可在创建后立即手动调用</span>
						</div>
					</template>
					<template v-else-if="editData.isCron == 1">
						<el-form-item label="常用模板" class="form-item-full-width">
							<div class="cron-shortcuts">
								<el-button-group class="cron-shortcut-group">
									<el-button :type="cronPreset == 'daily-2am' ? 'primary' : 'default'" size="small" @click="$emit('apply-cron-preset', 'daily-2am')">每天 02:00</el-button>
									<el-button :type="cronPreset == 'daily-3am' ? 'primary' : 'default'" size="small" @click="$emit('apply-cron-preset', 'daily-3am')">每天 03:00</el-button>
									<el-button :type="cronPreset == 'weekend-2am' ? 'primary' : 'default'" size="small" @click="$emit('apply-cron-preset', 'weekend-2am')">周末 02:00</el-button>
									<el-button :type="cronPreset == 'custom' ? 'primary' : 'default'" size="small" @click="$emit('apply-cron-preset', 'custom')">自定义</el-button>
								</el-button-group>
								<div class="cron-shortcut-hint">
									先选一个常见模板，再用生成器微调时间。若需要复杂表达式，可展开高级字段。
								</div>
							</div>
						</el-form-item>
						<el-form-item label="cron 生成器" class="form-item-full-width">
							<div class="cron-builder">
								<div class="cron-builder-head">
									<div>
										<div class="cron-builder-title">未来执行更直观</div>
										<div class="cron-builder-desc">{{cronSummary}}</div>
									</div>
									<el-button size="mini" plain class="cron-advanced-toggle" @click="toggleCronAdvanced">
										{{cronEditor.advancedOpen ? '收起高级字段' : '展开高级字段'}}
									</el-button>
								</div>
								<el-radio-group v-model="cronEditor.mode" size="small" class="cron-mode-group" @change="emitCronEditorChange">
									<el-radio-button label="daily">每天固定时间</el-radio-button>
									<el-radio-button label="weekly">每周固定时间</el-radio-button>
									<el-radio-button label="monthly">每月固定日期</el-radio-button>
									<el-radio-button label="interval">每隔 N 分钟</el-radio-button>
									<el-radio-button label="custom">自定义</el-radio-button>
								</el-radio-group>
								<div v-if="cronEditor.mode !== 'custom'" class="cron-builder-body">
									<div class="cron-builder-row" :class="{'is-single': cronEditor.mode == 'interval'}">
										<div v-if="cronEditor.mode != 'interval'" class="cron-builder-field">
											<span class="cron-field-label">时间</span>
											<el-time-picker
												v-model="cronEditor.time"
												format="HH:mm:ss"
												value-format="HH:mm:ss"
												:clearable="false"
												placeholder="选择时间"
												class="cron-time-picker"
												popper-class="tao-time-picker-panel"
												@change="emitCronEditorChange">
											</el-time-picker>
										</div>
										<div v-if="cronEditor.mode == 'interval'" class="cron-builder-field">
											<span class="cron-field-label">间隔</span>
											<el-input-number v-model="cronEditor.intervalMinutes" :min="1" :max="1440" :step="1" class="cron-interval-input" @change="emitCronEditorChange"></el-input-number>
											<span class="cron-field-suffix">分钟</span>
										</div>
									</div>
									<div v-if="cronEditor.mode == 'weekly'" class="cron-builder-field is-full">
										<span class="cron-field-label">星期</span>
										<el-select v-model="cronEditor.weekdays" multiple collapse-tags placeholder="选择星期" class="cron-multi-select" @change="emitCronEditorChange">
											<el-option v-for="item in weekOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
										</el-select>
									</div>
									<div v-if="cronEditor.mode == 'monthly'" class="cron-builder-field is-full">
										<span class="cron-field-label">日期</span>
										<el-select v-model="cronEditor.monthDays" multiple collapse-tags placeholder="选择日期" class="cron-multi-select" @change="emitCronEditorChange">
											<el-option v-for="day in monthDayOptions" :key="day" :label="`${day} 日`" :value="day"></el-option>
										</el-select>
									</div>
									<div class="cron-builder-note">
										生成器会自动回填到高级字段，预览区会实时展示未来执行时间。
									</div>
								</div>
								<div v-else class="cron-builder-custom-tip">
									选择“自定义”后，可以直接展开高级字段手动微调；预览仍会基于当前字段更新。
								</div>
								<div class="cron-preview-box">
									<div class="cron-preview-head">
										<strong>未来执行预览</strong>
										<span>{{cronPreview.summary}}</span>
									</div>
									<div v-if="cronPreview.hint" class="cron-preview-hint">{{cronPreview.hint}}</div>
									<div v-if="cronPreview.items && cronPreview.items.length" class="cron-preview-list">
										<div v-for="(item, index) in cronPreview.items" :key="`${item}-${index}`" class="cron-preview-item">
											<span class="cron-preview-index">#{{index + 1}}</span>
											<span class="cron-preview-time">{{item}}</span>
										</div>
									</div>
									<div v-else class="cron-preview-empty">
										暂无可预览时间，请检查当前表达式或结束时间限制。
									</div>
								</div>
							</div>
						</el-form-item>
						<div v-show="cronEditor.advancedOpen" class="cron-advanced-panel">
							<el-form-item prop="isCron" label="高级字段">
								<div class="label_width cron-advanced-title">
									<span>生成器会自动回填这些字段，也可以直接微调。</span>
									<span @click="$emit('open-cron-help')" class="to-link">查看 cron 简易教程</span>
								</div>
							</el-form-item>
							<el-form-item v-for="item in cronList" :key="item.label" :prop="item.label" :label="item.label">
								<el-input v-model="editData[item.label]" :placeholder="item.palce" class="label_width" style="width: 100%;"></el-input>
							</el-form-item>
						</div>
					</template>
					<template v-else-if="editData.isCron == 3">
						<TimeWindowConfig
							:editData="editData"
							:timeWindowPreset="timeWindowPreset"
							:weekOptions="weekOptions"
							:monthDayOptions="monthDayOptions"
							@apply-preset="$emit('apply-time-window-preset', $event)"
							@mode-change="$emit('time-window-mode-change')"
							@format-point="emitFormatPoint"
							@remove-range="$emit('remove-time-window-range', $event)"
							@apply-ranges="$emit('apply-time-window-ranges', $event)"
							@add-range="$emit('add-time-window-range')"
						/>
					</template>
				</div>
			</el-form>
		</div>
		<span slot="footer" class="dialog-footer">
			<el-button @click="handleClose">取 消</el-button>
			<el-button type="primary" @click="$emit('submit')" :loading="loading">确 定</el-button>
		</span>
	</el-dialog>
</template>

<script>
	import TimeWindowConfig from './TimeWindowConfig.vue';

	export default {
		name: 'JobEditorDialog',
		components: {
			TimeWindowConfig
		},
		props: {
			visible: {
				type: Boolean,
				default: false
			},
			editData: {
				type: Object,
				default: null
			},
			rules: {
				type: Object,
				required: true
			},
			isMobile: {
				type: Boolean,
				default: false
			},
			dialogWidth: {
				type: String,
				required: true
			},
			openlistList: {
				type: Array,
				default: () => []
			},
			cronPreset: {
				type: String,
				default: 'custom'
			},
			cronList: {
				type: Array,
				default: () => []
			},
			timeWindowPreset: {
				type: String,
				default: 'night'
			},
			weekOptions: {
				type: Array,
				default: () => []
			},
			monthDayOptions: {
				type: Array,
				default: () => []
			},
			loading: {
				type: Boolean,
				default: false
			}
		},
		data() {
			return {
				excludeTmp: '',
				cronEditor: {
					mode: 'daily',
					time: '02:00:00',
					weekdays: [0, 1, 2, 3, 4],
					monthDays: [1],
					intervalMinutes: 30,
					advancedOpen: false
				}
			};
		},
		computed: {
			cronSummary() {
				if (!this.editData || this.editData.isCron != 1) {
					return '选择 cron 后可生成执行计划';
				}
				if (this.cronEditor.mode == 'daily') {
					return `每天 ${this.displayTime(this.cronEditor.time)} 执行一次`;
				}
				if (this.cronEditor.mode == 'weekly') {
					const days = this.weekOptions
						.filter(item => this.cronEditor.weekdays.indexOf(item.value) > -1)
						.map(item => item.label)
						.join('、');
					return `${days || '未选择星期'} ${this.displayTime(this.cronEditor.time)} 执行一次`;
				}
				if (this.cronEditor.mode == 'monthly') {
					const days = (this.cronEditor.monthDays || []).slice().sort((a, b) => a - b).map(item => `${item}日`).join('、');
					return `每月 ${days || '未选择日期'} ${this.displayTime(this.cronEditor.time)} 执行一次`;
				}
				if (this.cronEditor.mode == 'interval') {
					return `每隔 ${this.cronEditor.intervalMinutes || 1} 分钟执行一次`;
				}
				return '自定义 cron 字段，适合熟悉 APScheduler cron 语法的场景';
			},
			cronPreview() {
				const empty = {
					summary: '基于当前浏览器时间推算',
					hint: '',
					items: []
				};
				if (!this.editData || this.editData.isCron != 1) {
					return empty;
				}
				try {
					const items = this.buildCronPreview(5);
					return {
						summary: items.length ? `已生成 ${items.length} 条` : '没有匹配时间',
						hint: this.cronPreviewHint(),
						items
					};
				} catch (e) {
					return {
						summary: '暂不可预览',
						hint: '当前字段包含复杂语法或格式异常，可保存后由后端调度器校验。',
						items: []
					};
				}
			}
		},
		watch: {
			visible(value) {
				if (value) {
					this.syncCronEditorFromFields();
				}
			},
			'editData.isCron'(value) {
				if (value == 1) {
					this.syncCronEditorFromFields();
				}
			},
			'editData.hour': 'syncCronEditorFromFields',
			'editData.minute': 'syncCronEditorFromFields',
			'editData.second': 'syncCronEditorFromFields',
			'editData.day': 'syncCronEditorFromFields',
			'editData.day_of_week': 'syncCronEditorFromFields'
		},
		methods: {
			validate(callback) {
				if (!this.$refs.jobRule) {
					callback(false);
					return;
				}
				this.$refs.jobRule.validate(callback);
			},
			handleClose() {
				this.excludeTmp = '';
				this.$emit('close');
			},
			handleAddExclude() {
				if (this.excludeTmp != '') {
					this.$emit('add-exclude', this.excludeTmp);
				}
				this.excludeTmp = '';
			},
			emitFormatPoint(range, key) {
				this.$emit('format-time-window-point', range, key);
			},
			toggleCronAdvanced() {
				this.cronEditor.advancedOpen = !this.cronEditor.advancedOpen;
			},
			emitCronEditorChange() {
				this.applyCronEditorToFields();
			},
			displayTime(value) {
				const parts = `${value || '00:00:00'}`.split(':');
				return `${parts[0] || '00'}:${parts[1] || '00'}`;
			},
			parseTime(value) {
				const parts = `${value || '00:00:00'}`.split(':').map(item => Number(item));
				return {
					hour: Number.isNaN(parts[0]) ? 0 : parts[0],
					minute: Number.isNaN(parts[1]) ? 0 : parts[1],
					second: Number.isNaN(parts[2]) ? 0 : parts[2]
				};
			},
			normalizeList(value) {
				if (value == null || value === '') {
					return [];
				}
				return `${value}`.split(',').map(item => item.trim()).filter(Boolean);
			},
			parseSimpleNumberList(value, min, max) {
				const result = [];
				this.normalizeList(value).forEach(item => {
					if (/^\d+$/.test(item)) {
						const num = Number(item);
						if (num >= min && num <= max) {
							result.push(num);
						}
					}
				});
				return Array.from(new Set(result));
			},
			normalizeWeekdayValues(value) {
				const weekMap = {
					mon: 0,
					tue: 1,
					wed: 2,
					thu: 3,
					fri: 4,
					sat: 5,
					sun: 6
				};
				const result = [];
				this.normalizeList(value).forEach(item => {
					const lower = item.toLowerCase();
					if (weekMap[lower] != null) {
						result.push(weekMap[lower]);
					} else if (/^\d+$/.test(item)) {
						const num = Number(item);
						if (num >= 0 && num <= 6) {
							result.push(num);
						}
					}
				});
				return Array.from(new Set(result));
			},
			syncCronEditorFromFields() {
				if (!this.editData || this.editData.isCron != 1) {
					return;
				}
				if (this.cronEditor.mode == 'custom') {
					return;
				}
				const hour = this.parseSimpleNumberList(this.editData.hour, 0, 23);
				const minute = this.parseSimpleNumberList(this.editData.minute, 0, 59);
				const second = this.parseSimpleNumberList(this.editData.second, 0, 59);
				const day = this.parseSimpleNumberList(this.editData.day, 1, 31);
				const weekdays = this.normalizeWeekdayValues(this.editData.day_of_week);
				const hasInterval = `${this.editData.minute || ''}`.indexOf('*/') === 0 && !this.editData.hour && !this.editData.day && !this.editData.day_of_week;
				if (hasInterval) {
					this.cronEditor.mode = 'interval';
					this.cronEditor.intervalMinutes = Number(`${this.editData.minute}`.replace('*/', '')) || 30;
				} else if (day.length) {
					this.cronEditor.mode = 'monthly';
					this.cronEditor.monthDays = day;
				} else if (weekdays.length) {
					this.cronEditor.mode = 'weekly';
					this.cronEditor.weekdays = weekdays;
				} else if (this.editData.hour || this.editData.minute || this.editData.second) {
					this.cronEditor.mode = 'daily';
				}
				const timeHour = hour.length ? hour[0] : 2;
				const timeMinute = minute.length ? minute[0] : 0;
				const timeSecond = second.length ? second[0] : 0;
				this.cronEditor.time = `${String(timeHour).padStart(2, '0')}:${String(timeMinute).padStart(2, '0')}:${String(timeSecond).padStart(2, '0')}`;
			},
			applyCronEditorToFields() {
				if (!this.editData) {
					return;
				}
				if (this.cronEditor.mode == 'custom') {
					this.$emit('apply-cron-preset', 'custom');
					return;
				}
				this.$emit('apply-cron-preset', 'custom');
				const time = this.parseTime(this.cronEditor.time);
				this.cronList.forEach(item => {
					this.editData[item.label] = null;
				});
				if (this.cronEditor.mode == 'interval') {
					this.editData.minute = `*/${this.cronEditor.intervalMinutes || 1}`;
					this.editData.second = '0';
					return;
				}
				this.editData.hour = `${time.hour}`;
				this.editData.minute = `${time.minute}`;
				this.editData.second = `${time.second}`;
				if (this.cronEditor.mode == 'weekly') {
					const weekdays = this.cronEditor.weekdays && this.cronEditor.weekdays.length ? this.cronEditor.weekdays : [0, 1, 2, 3, 4];
					this.cronEditor.weekdays = weekdays;
					this.editData.day_of_week = weekdays.slice().sort((a, b) => a - b).join(',');
				}
				if (this.cronEditor.mode == 'monthly') {
					const monthDays = this.cronEditor.monthDays && this.cronEditor.monthDays.length ? this.cronEditor.monthDays : [1];
					this.cronEditor.monthDays = monthDays;
					this.editData.day = monthDays.slice().sort((a, b) => a - b).join(',');
				}
			},
			cronPreviewHint() {
				const start = this.editData.start_date ? `开始：${this.editData.start_date}` : '';
				const end = this.editData.end_date ? `结束：${this.editData.end_date}` : '';
				return [start, end].filter(Boolean).join('；');
			},
			formatDateTime(date) {
				const pad = value => String(value).padStart(2, '0');
				return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
			},
			parseDateLimit(value, isEnd = false) {
				if (!value) {
					return null;
				}
				const date = new Date(value);
				if (Number.isNaN(date.getTime())) {
					return null;
				}
				if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(`${value}`) && isEnd) {
					date.setHours(23, 59, 59, 999);
				}
				return date;
			},
			buildCronPreview(limit) {
				if (this.cronEditor.mode == 'custom') {
					return this.buildPreviewFromFields(limit);
				}
				const startLimit = this.parseDateLimit(this.editData.start_date);
				const endLimit = this.parseDateLimit(this.editData.end_date, true);
				const now = new Date();
				const startFrom = startLimit && startLimit > now ? startLimit : now;
				let items = [];
				if (this.cronEditor.mode == 'interval') {
					items = this.previewInterval(startFrom, endLimit, limit);
				} else if (this.cronEditor.mode == 'daily') {
					items = this.previewDaily(startFrom, endLimit, limit);
				} else if (this.cronEditor.mode == 'weekly') {
					items = this.previewWeekly(startFrom, endLimit, limit);
				} else if (this.cronEditor.mode == 'monthly') {
					items = this.previewMonthly(startFrom, endLimit, limit);
				}
				return items.map(this.formatDateTime);
			},
			candidateAfter(candidate, startFrom) {
				return candidate.getTime() > startFrom.getTime();
			},
			applyEditorTime(date) {
				const time = this.parseTime(this.cronEditor.time);
				date.setHours(time.hour, time.minute, time.second, 0);
				return date;
			},
			withinEndLimit(date, endLimit) {
				return !endLimit || date.getTime() <= endLimit.getTime();
			},
			previewInterval(startFrom, endLimit, limit) {
				const step = Math.max(1, Number(this.cronEditor.intervalMinutes) || 1);
				const result = [];
				const candidate = new Date(startFrom);
				candidate.setSeconds(0, 0);
				candidate.setMinutes(candidate.getMinutes() + 1);
				for (let i = 0; i < 1440 * 14 && result.length < limit; i++) {
					const next = new Date(candidate.getTime() + i * 60000);
					if (!this.withinEndLimit(next, endLimit)) {
						break;
					}
					if (next.getMinutes() % step == 0) {
						result.push(next);
					}
				}
				return result;
			},
			previewDaily(startFrom, endLimit, limit) {
				const result = [];
				for (let i = 0; i < 370 && result.length < limit; i++) {
					const candidate = this.applyEditorTime(new Date(startFrom.getFullYear(), startFrom.getMonth(), startFrom.getDate() + i));
					if (!this.candidateAfter(candidate, startFrom)) {
						continue;
					}
					if (!this.withinEndLimit(candidate, endLimit)) {
						break;
					}
					result.push(candidate);
				}
				return result;
			},
			previewWeekly(startFrom, endLimit, limit) {
				const selected = this.cronEditor.weekdays && this.cronEditor.weekdays.length ? this.cronEditor.weekdays : [];
				const result = [];
				for (let i = 0; i < 370 && result.length < limit; i++) {
					const candidate = this.applyEditorTime(new Date(startFrom.getFullYear(), startFrom.getMonth(), startFrom.getDate() + i));
					if (selected.indexOf((candidate.getDay() + 6) % 7) == -1 || !this.candidateAfter(candidate, startFrom)) {
						continue;
					}
					if (!this.withinEndLimit(candidate, endLimit)) {
						break;
					}
					result.push(candidate);
				}
				return result;
			},
			previewMonthly(startFrom, endLimit, limit) {
				const selected = this.cronEditor.monthDays && this.cronEditor.monthDays.length ? this.cronEditor.monthDays.slice().sort((a, b) => a - b) : [];
				const result = [];
				for (let monthOffset = 0; monthOffset < 36 && result.length < limit; monthOffset++) {
					const base = new Date(startFrom.getFullYear(), startFrom.getMonth() + monthOffset, 1);
					const daysInMonth = new Date(base.getFullYear(), base.getMonth() + 1, 0).getDate();
					selected.forEach(day => {
						if (result.length >= limit || day > daysInMonth) {
							return;
						}
						const candidate = this.applyEditorTime(new Date(base.getFullYear(), base.getMonth(), day));
						if (!this.candidateAfter(candidate, startFrom)) {
							return;
						}
						if (!this.withinEndLimit(candidate, endLimit)) {
							return;
						}
						result.push(candidate);
					});
				}
				return result.sort((a, b) => a.getTime() - b.getTime()).slice(0, limit);
			},
			buildPreviewFromFields(limit) {
				const hourList = this.parseSimpleNumberList(this.editData.hour, 0, 23);
				const minuteList = this.parseSimpleNumberList(this.editData.minute, 0, 59);
				const secondList = this.parseSimpleNumberList(this.editData.second, 0, 59);
				const dayList = this.parseSimpleNumberList(this.editData.day, 1, 31);
				const weekdayList = this.normalizeWeekdayValues(this.editData.day_of_week);
				if (!hourList.length || !minuteList.length || !secondList.length) {
					return [];
				}
				const startLimit = this.parseDateLimit(this.editData.start_date);
				const endLimit = this.parseDateLimit(this.editData.end_date, true);
				const now = new Date();
				const startFrom = startLimit && startLimit > now ? startLimit : now;
				const result = [];
				for (let i = 0; i < 370 && result.length < limit; i++) {
					const day = new Date(startFrom.getFullYear(), startFrom.getMonth(), startFrom.getDate() + i);
					if (dayList.length && dayList.indexOf(day.getDate()) == -1) {
						continue;
					}
					if (weekdayList.length && weekdayList.indexOf((day.getDay() + 6) % 7) == -1) {
						continue;
					}
					hourList.forEach(hour => {
						minuteList.forEach(minute => {
							secondList.forEach(second => {
								if (result.length >= limit) {
									return;
								}
								const candidate = new Date(day.getFullYear(), day.getMonth(), day.getDate(), hour, minute, second, 0);
								if (this.candidateAfter(candidate, startFrom) && this.withinEndLimit(candidate, endLimit)) {
									result.push(candidate);
								}
							});
						});
					});
				}
				return result.sort((a, b) => a.getTime() - b.getTime()).slice(0, limit).map(this.formatDateTime);
			}
		}
	}
</script>
