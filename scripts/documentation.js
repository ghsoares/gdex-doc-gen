// Handle sidebar section
document.querySelectorAll('.sidebar-caption').forEach(el => {
	el.addEventListener('click', () => {
		el.classList.toggle('active');
	});
});

// Prevent links which already points to this page
document.querySelectorAll('a').forEach(el => {
	el.addEventListener('click', ev => {
		if (el.href == window.location.href) {
			ev.preventDefault();
		}
	});

	if (el.href != window.location.href) return;

	// Active menu items
	let parent = el.parentElement;
	while (parent) {
		menu = parent.querySelector(":scope > .sidebar-caption");
		console.log(menu);
		if (menu) {
			menu.classList.add('active');
		}
		parent = parent.parentElement;
	}
});
