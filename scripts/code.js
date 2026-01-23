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

// Handle codeblocks
document.querySelectorAll('.codeblocks').forEach(el => {
	const languageElements = el.querySelectorAll(':scope > .language');

	const languageTabs = document.createElement("div");
	const languageTabButtons = [];
	languageTabs.classList.add("codeblocks-tabs");
	languageElements.forEach(langEl => {
		const languageTabButton = document.createElement("button");
		languageTabButton.textContent = langEl.getAttribute("language-name");

		languageTabButton.addEventListener('click', () => {
			languageElements.forEach(otherTab => otherTab.classList.remove('active'));
			languageTabButtons.forEach(otherButton => otherButton.classList.remove('active'));
			langEl.classList.add('active');
			languageTabButton.classList.add('active');
		});

		languageTabs.appendChild(languageTabButton);
		languageTabButtons.push(languageTabButton);
	});

	languageElements[0].classList.add('active');
	languageTabButtons[0].classList.add('active');

	el.prepend(languageTabs);
});