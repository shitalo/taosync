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
		start() {
			activeToken += 1;
			const token = activeToken;
			clearDelay();
			clearHide();
			delayTimer = setTimeout(() => {
				if (activeToken !== token) {
					return;
				}
				visible = true;
				visibleAt = Date.now();
				show();
			}, delay);
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
			const wait = Math.max(0, minDuration - (Date.now() - visibleAt));
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
