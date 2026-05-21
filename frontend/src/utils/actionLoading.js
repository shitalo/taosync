import { createDelayedLoadingController } from './loadingFeedback';

export function createActionLoadingMap(config = {}) {
	const controllers = {};

	const ensureController = (vm, key) => {
		if (!controllers[key]) {
			controllers[key] = createDelayedLoadingController({
				show: () => { vm[key] = true; },
				hide: () => { vm[key] = false; },
				delay: config.delay == null ? 120 : config.delay,
				minDuration: config.minDuration == null ? 180 : config.minDuration
			});
		}
		return controllers[key];
	};

	return {
		start(vm, key) {
			return ensureController(vm, key).start();
		},
		finish(vm, key, token) {
			ensureController(vm, key).finish(token);
		},
		dispose() {
			Object.keys(controllers).forEach(key => {
				controllers[key].dispose();
			});
		}
	};
}
