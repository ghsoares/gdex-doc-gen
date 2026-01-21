// Handle filename and copy
document.querySelectorAll('.codeblocks > .language > .filename').forEach(el => {
	const filename = el.textContent;
	let copyTimeout = null;
	el.addEventListener('click', () => {
		const codeEl = el.parentElement.querySelector(':scope > pre > code');
		const code = codeEl.textContent;
		navigator.clipboard.writeText(code).then(() => {
			if (copyTimeout) {
				clearTimeout(copyTimeout);
			}
			el.textContent = "Copied!";
			copyTimeout = setTimeout(() => {
				el.textContent = filename;
			}, 2000);
		}).catch(err => {
			console.error(err);
		});
	});
});