<template>
	<div class="time-window-config form-item-full-width">
		<el-form-item label="快捷方案" class="form-item-full-width">
			<div class="time-window-presets">
				<el-button-group class="time-window-preset-group">
					<el-button :type="timeWindowPreset == 'night' ? 'primary' : 'default'" size="small" @click="$emit('apply-preset', 'night')">每天夜间</el-button>
					<el-button :type="timeWindowPreset == 'daylight' ? 'primary' : 'default'" size="small" @click="$emit('apply-preset', 'daylight')">每天白天</el-button>
					<el-button :type="timeWindowPreset == 'weekday-night' ? 'primary' : 'default'" size="small" @click="$emit('apply-preset', 'weekday-night')">工作日晚间</el-button>
					<el-button :type="timeWindowPreset == 'custom' ? 'primary' : 'default'" size="small" @click="$emit('apply-preset', 'custom')">自定义</el-button>
				</el-button-group>
				<div class="time-window-preset-hint">先选一个常用方案，再按需微调。</div>
			</div>
		</el-form-item>
		<el-form-item label="日期范围" class="form-item-full-width">
			<div class="time-window-box">
				<el-radio-group v-model="editData.timeWindow.mode" size="small" class="time-window-mode" @change="$emit('mode-change')">
					<el-radio-button label="daily">每天</el-radio-button>
					<el-radio-button label="week">按星期</el-radio-button>
					<el-radio-button label="day">按日期</el-radio-button>
				</el-radio-group>
				<el-checkbox-group v-if="editData.timeWindow.mode == 'week'" v-model="editData.timeWindow.days" class="time-window-checks">
					<el-checkbox-button v-for="item in weekOptions" :key="item.value" :label="item.value">{{item.label}}</el-checkbox-button>
				</el-checkbox-group>
				<el-checkbox-group v-if="editData.timeWindow.mode == 'day'" v-model="editData.timeWindow.daysOfMonth" class="time-window-checks is-days">
					<el-checkbox-button v-for="day in monthDayOptions" :key="day" :label="day">{{day}}</el-checkbox-button>
				</el-checkbox-group>
			</div>
		</el-form-item>
		<el-form-item label="同步时间段" class="form-item-full-width">
			<div class="time-window-range-list">
				<div class="time-window-range" v-for="(range, index) in editData.timeWindow.ranges" :key="index">
					<div class="time-window-input">
						<span class="time-window-input-label">开始</span>
						<el-input v-model.trim="range.start" placeholder="如 18:30" maxlength="5" inputmode="numeric" @blur="$emit('format-point', range, 'start')"></el-input>
					</div>
					<span class="time-window-separator">至</span>
					<div class="time-window-input">
						<span class="time-window-input-label">结束</span>
						<el-input v-model.trim="range.end" placeholder="如 18:35" maxlength="5" inputmode="numeric" @blur="$emit('format-point', range, 'end')"></el-input>
					</div>
					<el-button class="time-window-delete" type="default" plain icon="el-icon-delete" size="small" @click="$emit('remove-range', index)" :disabled="editData.timeWindow.ranges.length == 1">删除</el-button>
				</div>
				<div class="time-window-format-tip">
					按 HH:mm 填写，支持任意分钟，例如 23:03；结束时间可填 24:00。
				</div>
				<div class="time-window-mini-presets">
					<span class="time-window-mini-label">常用时间段</span>
					<div class="time-window-mini-group">
						<el-button size="mini" plain @click="$emit('apply-ranges', [{ start: '18:30', end: '18:35' }])">18:30 - 18:35</el-button>
						<el-button size="mini" plain @click="$emit('apply-ranges', [{ start: '22:00', end: '24:00' }, { start: '00:00', end: '07:00' }])">夜间跨天</el-button>
						<el-button size="mini" plain @click="$emit('apply-ranges', [{ start: '07:00', end: '09:00' }])">清晨</el-button>
						<el-button size="mini" plain @click="$emit('apply-ranges', [{ start: '09:00', end: '18:00' }])">工作时段</el-button>
					</div>
				</div>
				<el-button class="time-window-add" type="default" plain icon="el-icon-plus" size="small" @click="$emit('add-range')">添加时间段</el-button>
			</div>
		</el-form-item>
		<div class="interval-tip-wrapper form-item-full-width">
			<span class="interval-tip">到达时间段会自动开始同步，离开时间段会自动中止。跨 0 点的连续时间段会保持连续运行，不会在 24 点附近反复停止和启动。</span>
		</div>
	</div>
</template>

<script>
	export default {
		name: 'TimeWindowConfig',
		props: {
			editData: {
				type: Object,
				required: true
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
			}
		}
	}
</script>
