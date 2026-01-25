// Handle sidebar section
document.querySelectorAll('.sidebar-caption').forEach(el => {
	el.addEventListener('click', () => {
		if (el.classList.contains('leaf')) {
			document.querySelectorAll('.sidebar-caption.leaf').forEach(el => {
				el.classList.remove('active');
			});
			el.classList.add('active');
		} else {
			el.classList.toggle('active');
		}
	});
});

// Handle links
document.querySelectorAll('a').forEach(el => {
	// Prevent from redirecting to same page again
	el.addEventListener('click', ev => {
		if (el.href.search('#') == -1 && el.href == window.location.href.split("#")[0]) {
			ev.preventDefault();
		}
	});

	// Active menu items which are active to current window href
	console.log(el.href, "\n", window.location.href);
	if (window.location.href != el.href) return;

	let parent = el.parentElement;
	while (parent) {
		menu = parent.querySelector(":scope > .sidebar-caption");
		if (menu) {
			menu.classList.add('active');
		}
		parent = parent.parentElement;
	}
});

// Add reference link tags for headers
document.querySelectorAll('[link-section]').forEach(el => {
	const link = document.createElement('a');
	const section = el.parentElement;
	const sectionId = section.id;

	link.classList.add('headerlink');
	link.classList.add('material-symbols-outlined');
	link.href = `#${sectionId}`;
	link.textContent = 'link_2';

	el.appendChild(link);
});


