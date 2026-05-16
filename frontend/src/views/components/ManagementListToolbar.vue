<template>
	<div class="management-list-toolbar" v-if="show">
		<div>
			<strong>{{ title }}</strong>
			<span>{{ summary }}</span>
		</div>
		<div class="management-list-hint" :class="{ 'has-accent': hintAccent }">
			<span v-if="hintIcon"><i :class="hintIcon"></i>{{ hint }}</span>
			<span v-else>{{ hint }}</span>
		</div>
	</div>
</template>

<script>
	export default {
		name: 'ManagementListToolbar',
		props: {
			show: {
				type: Boolean,
				default: true
			},
			title: {
				type: String,
				required: true
			},
			summary: {
				type: String,
				required: true
			},
			hint: {
				type: String,
				required: true
			},
			hintIcon: {
				type: String,
				default: ''
			},
			hintAccent: {
				type: Boolean,
				default: false
			}
		}
	}
</script>

<style lang="scss" scoped>
	.management-list-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		margin-bottom: 10px;
		padding: 0 2px;
		color: var(--text-muted);
		font-size: 12px;
	}

	.management-list-toolbar strong {
		display: block;
		margin-bottom: 2px;
		color: var(--text-primary);
		font-size: 15px;
		font-weight: 900;
		letter-spacing: -.01em;
	}

	.management-list-toolbar span {
		line-height: 1.6;
	}

	.management-list-hint {
		display: inline-flex;
		align-items: center;
		justify-content: flex-end;
		min-width: 0;
		text-align: right;
	}

	.management-list-hint span {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
	}

	.management-list-hint i {
		flex: 0 0 auto;
	}

	.management-list-hint.has-accent {
		color: var(--brand-strong);
		font-weight: 800;
	}

	@media (max-width: 768px) {
		.management-list-toolbar {
			align-items: stretch;
			flex-direction: column;
		}

		.management-list-hint {
			justify-content: flex-start;
			text-align: left;
		}
	}
</style>
