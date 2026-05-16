<template>
	<div :class="['tao-empty-state', customClass]">
		<div class="tao-empty-mark">
			<i :class="icon"></i>
		</div>
		<div class="tao-empty-copy">
			<div class="tao-empty-title">{{ title }}</div>
			<div class="tao-empty-desc">{{ description }}</div>
		</div>
	</div>
</template>

<script>
	export default {
		name: 'EmptyStateCard',
		props: {
			icon: {
				type: String,
				required: true
			},
			title: {
				type: String,
				required: true
			},
			description: {
				type: String,
				required: true
			},
			customClass: {
				type: String,
				default: ''
			}
		}
	}
</script>

<style lang="scss" scoped>
	.tao-empty-state {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: center;
		gap: 14px;
		min-height: 92px;
		padding: 14px;
		border: 1px dashed var(--border-light);
		border-radius: 22px;
		background:
			radial-gradient(circle at 12% 18%, var(--brand-soft), transparent 16rem),
			var(--surface-soft);
		box-sizing: border-box;
	}

	.tao-empty-mark {
		width: 54px;
		height: 54px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 18px;
		background: linear-gradient(135deg, var(--brand), var(--accent));
		color: #fffaf1;
		font-size: 22px;
		box-shadow: 0 14px 28px rgba(169, 79, 34, .18);
	}

	.tao-empty-copy {
		min-width: 0;
	}

	.tao-empty-title {
		font-size: 18px;
		font-weight: 900;
		letter-spacing: -.03em;
		color: var(--text-primary);
	}

	.tao-empty-desc {
		max-width: none;
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.7;
		color: var(--text-muted);
	}

	@media (max-width: 768px) {
		.tao-empty-state {
			grid-template-columns: 1fr;
			justify-items: center;
			text-align: center;
		}
	}
</style>
