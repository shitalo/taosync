export function createDelayedLoadingController({
	show,
	hide,
	delay = 180,
	minDuration = 220
}) {
	let activeToken = 0;
	let delayTimer = null;
	let hideTimer = null;
	let visible = false;
	let visibleAt = 0;
	let activeMinDuration = minDuration;

	const clearDelay = () => {
		if (delayTimer) {
			clearTimeout(delayTimer);
			delayTimer = null;
		}
	};

	const clearHide = () => {
		if (hideTimer) {
			clearTimeout(hideTimer);
			hideTimer = null;
		}
	};

	const close = () => {
		if (activeToken === 0 && visible) {
			visible = false;
			hide();
		}
	};

	return {
		start(options = {}) {
			activeToken += 1;
			const token = activeToken;
			const nextDelay = options.delay == null ? delay : options.delay;
			activeMinDuration = options.minDuration == null ? minDuration : options.minDuration;
			clearDelay();
			clearHide();
			const reveal = () => {
				if (activeToken !== token) {
					return;
				}
				visible = true;
				visibleAt = Date.now();
				show();
			};
			if (nextDelay <= 0) {
				reveal();
			} else {
				delayTimer = setTimeout(reveal, nextDelay);
			}
			return token;
		},
		finish(token) {
			if (activeToken !== token) {
				return;
			}
			activeToken = 0;
			clearDelay();
			if (!visible) {
				hide();
				return;
			}
			const wait = Math.max(0, activeMinDuration - (Date.now() - visibleAt));
			hideTimer = setTimeout(close, wait);
		},
		dispose() {
			activeToken = 0;
			clearDelay();
			clearHide();
			if (visible) {
				visible = false;
				hide();
			}
		}
	};
}
