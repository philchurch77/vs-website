document.addEventListener("DOMContentLoaded", () => {
	initScrollReveal();
	initChatHistoryDrawers();
});

function initScrollReveal() {
	const revealEls = document.querySelectorAll(".reveal-on-load");
	if (!revealEls.length) return;

	if (!("IntersectionObserver" in window)) {
		revealEls.forEach((el) => el.classList.add("is-visible"));
		return;
	}

	const observer = new IntersectionObserver(
		(entries) => {
			entries
				.filter((entry) => entry.isIntersecting)
				.forEach((entry, index) => {
					// stagger elements that enter the viewport together
					setTimeout(() => entry.target.classList.add("is-visible"), 90 * index);
					observer.unobserve(entry.target);
				});
		},
		{ threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
	);

	revealEls.forEach((el) => observer.observe(el));
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