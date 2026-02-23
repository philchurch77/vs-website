document.addEventListener("DOMContentLoaded", () => {
	initRevealOnLoad();
	initChatHistoryDrawers();
});

function initRevealOnLoad() {
	const revealEls = document.querySelectorAll(".reveal-on-load");
	if (!revealEls.length) return;

	revealEls.forEach((el, index) => {
		const delay = 120 * index; // stagger for a nice cascade
		setTimeout(() => {
			el.classList.add("is-visible");
		}, delay);
	});
}

function initChatHistoryDrawers() {
	const triggers = document.querySelectorAll(".chat-history-hamburger");
	if (!triggers.length) return;

	const overlay = document.querySelector("[data-chat-history-overlay]");
	const mediaQuery = window.matchMedia("(min-width: 901px)");
	let activePanel = null;
	let activeTrigger = null;

	const updateGlobalState = () => {
		const isOpen = Boolean(activePanel);
		document.body.classList.toggle("chat-history-open", isOpen);
		if (overlay) {
			overlay.classList.toggle("is-visible", isOpen);
		}
	};

	const setPanelState = (panel, trigger, shouldOpen) => {
		if (shouldOpen && activePanel && activePanel !== panel) {
			setPanelState(activePanel, activeTrigger, false);
		}

		if (shouldOpen) {
			activePanel = panel;
			activeTrigger = trigger;
		} else if (activePanel === panel) {
			activePanel = null;
			activeTrigger = null;
		}

		panel.classList.toggle("is-open", shouldOpen);
		trigger.setAttribute("aria-expanded", String(shouldOpen));
		updateGlobalState();

		if (shouldOpen && !mediaQuery.matches) {
			panel.focus();
		}
	};

	triggers.forEach((trigger) => {
		const targetId = trigger.getAttribute("aria-controls");
		const panel = targetId ? document.getElementById(targetId) : null;
		if (!panel) {
			return;
		}

		const closeButton = panel.querySelector(".chat-history-close");
		const togglePanel = () => {
			const nextState = !panel.classList.contains("is-open");
			setPanelState(panel, trigger, nextState);
		};

		trigger.addEventListener("click", togglePanel);
		closeButton?.addEventListener("click", () => setPanelState(panel, trigger, false));
	});

	const closeActivePanel = () => {
		if (activePanel && activeTrigger) {
			setPanelState(activePanel, activeTrigger, false);
		}
	};

	overlay?.addEventListener("click", closeActivePanel);
	window.addEventListener("keydown", (event) => {
		if (event.key === "Escape") {
			closeActivePanel();
		}
	});

	const handleBreakpoint = (event) => {
		if (event.matches) {
			closeActivePanel();
		}
	};

	if (mediaQuery.addEventListener) {
		mediaQuery.addEventListener("change", handleBreakpoint);
	} else if (mediaQuery.addListener) {
		mediaQuery.addListener(handleBreakpoint);
	}
}