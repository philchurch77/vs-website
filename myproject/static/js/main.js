// Simple reveal-on-load animation for hero elements
document.addEventListener("DOMContentLoaded", () => {
	const revealEls = document.querySelectorAll(".reveal-on-load");
	if (!revealEls.length) return;

	revealEls.forEach((el, index) => {
		const delay = 120 * index; // stagger for a nice cascade
		setTimeout(() => {
			el.classList.add("is-visible");
		}, delay);
	});
});