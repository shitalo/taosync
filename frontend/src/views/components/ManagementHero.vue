<template>
	<section class="management-hero">
		<div class="management-hero-copy">
			<div class="management-hero-kicker">{{ kicker }}</div>
			<h2>{{ title }}</h2>
			<p>{{ description }}</p>
		</div>
		<div class="management-hero-side">
			<div class="management-hero-stat">
				<div class="management-hero-stat-num">{{ statValue }}</div>
				<div class="management-hero-stat-label">{{ statLabel }}</div>
			</div>
			<el-button
				class="management-hero-action"
				:type="actionType"
				:icon="actionIcon"
				@click="$emit('action')"
			>
				{{ actionText }}
			</el-button>
		</div>
	</section>
</template>

<script>
	export default {
		name: 'ManagementHero',
		props: {
			kicker: {
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
			statValue: {
				type: [String, Number],
				required: true
			},
			statLabel: {
				type: String,
				required: true
			},
			actionText: {
				type: String,
				required: true
			},
			actionIcon: {
				type: String,
				default: 'el-icon-plus'
			},
			actionType: {
				type: String,
				default: 'primary'
			}
		}
	}
</script>

<style lang="scss" scoped>
	.management-hero,
	.management-hero-copy,
	.management-hero-side {
		min-width: 0;
	}

	.management-hero {
		flex: 0 0 auto;
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 320px);
		align-items: center;
		gap: 18px;
		min-height: auto;
		padding: 16px 18px;
		border: 1px solid var(--border-color);
		border-radius: 28px;
		background:
			radial-gradient(circle at 88% 16%, color-mix(in srgb, var(--brand-soft) 88%, transparent), transparent 17rem),
			linear-gradient(135deg, color-mix(in srgb, var(--surface-raised) 98%, #fff 2%), color-mix(in srgb, var(--bg-secondary) 92%, transparent));
		box-shadow: var(--shadow-card);
		overflow: hidden;
	}

	.management-hero-kicker {
		font-size: 11px;
		font-weight: 900;
		letter-spacing: .28em;
		color: var(--brand);
	}

	.management-hero h2 {
		margin: 4px 0 6px;
		font-size: clamp(28px, 3.2vw, 44px);
		line-height: 1;
		letter-spacing: -.055em;
		color: var(--text-primary);
	}

	.management-hero p {
		margin: 0;
		max-width: 620px;
		font-size: 13px;
		line-height: 1.55;
		color: var(--text-secondary);
	}

	.management-hero-side,
	.management-hero-stat,
	.management-hero-action {
		box-sizing: border-box;
		max-width: 100%;
	}

	.management-hero-side {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: stretch;
		justify-content: center;
		gap: 10px;
		overflow: hidden;
	}

	.management-hero-stat {
		width: 100%;
		min-height: 64px;
		padding: 10px 12px;
		border: 1px solid var(--border-light);
		border-radius: 18px;
		background: var(--surface-soft);
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		overflow: hidden;
		text-align: left;
	}

	.management-hero-stat-num {
		order: 2;
		flex: 0 1 auto;
		min-width: 0;
		max-width: 58%;
		font-size: 30px;
		font-weight: 900;
		line-height: .9;
		color: var(--brand-strong);
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	.management-hero-stat-label {
		order: 1;
		flex: 1 1 auto;
		min-width: 0;
		font-size: 12px;
		font-weight: 900;
		letter-spacing: .12em;
		color: var(--text-muted);
		text-align: left;
	}

	.management-hero-stat-num,
	.management-hero-stat-label {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.management-hero-action {
		width: 100%;
		min-width: 0;
		min-height: 32px;
		overflow: hidden;
		box-shadow: none !important;
		justify-content: center;
	}

	@media (max-width: 1180px) {
		.management-hero {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.management-hero {
			grid-template-columns: 1fr;
			gap: 12px;
			padding: 16px 18px;
			border-radius: 24px;
		}

		.management-hero-side {
			width: 100%;
		}
	}
</style>
