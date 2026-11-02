// FLI shared registration modal — injects the same modal used on the
// course pages and wires the header "Register Now" button (#open-register-modal).
(function () {
	if (document.getElementById('register-modal')) return;

	var style = document.createElement('style');
	style.textContent = [
		'.register-modal{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;z-index:3000;pointer-events:none;opacity:0;transition:opacity .2s ease;}',
		'.register-modal.is-open{pointer-events:auto;opacity:1;}',
		'.register-modal__backdrop{position:absolute;inset:0;background:rgba(0,0,0,0.45);backdrop-filter:blur(4px);}',
		'.register-modal__dialog{position:relative;background:#fff;border-radius:16px;padding:24px 24px 16px;max-width:820px;width:90%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,0.15);direction:rtl;font-family:inherit;}',
		'.register-modal__close{position:absolute;top:10px;left:12px;border:none;background:transparent;font-size:24px;cursor:pointer;color:#6b7280;}',
		'.register-modal__dialog h3{margin:0;font-size:20px;color:#111827;}',
		'.register-modal__subtitle{margin:6px 0 18px;color:#6b7280;font-size:14px;}',
		'.register-form{margin-top:6px;}',
		'.register-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;}',
		'.register-field{display:flex;flex-direction:column;gap:6px;font-size:14px;color:#1f2937;}',
		'.register-field input,.register-field select{padding:12px 10px;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;outline:none;transition:border-color .2s,box-shadow .2s;background:#fff;}',
		'.register-field input:focus,.register-field select:focus{border-color:var(--accent,#0b5fff);box-shadow:0 0 0 3px rgba(11,95,255,0.15);}',
		'.register-modal .btn{border:none;cursor:pointer;font-size:15px;}',
		'.register-modal .hero-cta,.register-modal #register-submit{width:100%;min-width:180px;padding:12px 24px;border-radius:10px;background:#0a4b78;color:#ffffff;font-weight:600;opacity:1;transition:background .2s ease;}',
		'.register-modal .hero-cta:hover{background:#083c60;}',
		'.register-modal .hero-cta:disabled,.register-modal #register-submit:disabled{background:#0a4b78;color:#ffffff;opacity:.75;cursor:not-allowed;}',
		'.country-code-dropdown{position:relative;width:100%;}',
		'.country-code-trigger{width:100%;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 10px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;cursor:pointer;font-size:14px;}',
		'.country-code-menu{position:absolute;top:110%;left:0;right:0;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 12px 30px rgba(0,0,0,0.08);padding:10px;display:none;z-index:10;max-height:260px;overflow:hidden;}',
		'.country-code-dropdown.open .country-code-menu{display:block;}',
		'.country-code-options{max-height:200px;overflow:auto;display:flex;flex-direction:column;gap:6px;}',
		'.country-code-option{display:flex;align-items:center;gap:10px;width:100%;border:1px solid #f1f5f9;border-radius:10px;padding:8px 10px;background:#fff;cursor:pointer;text-align:right;}',
		'.country-code-option:hover{border-color:var(--accent,#0b5fff);background:rgba(11,95,255,0.06);}',
		'.country-code-search{width:100%;margin-bottom:8px;border-radius:8px;border:1px solid #e5e7eb;padding:8px 10px;font-size:13px;box-sizing:border-box;}',
		'.country-code-copy{display:flex;flex-direction:column;gap:2px;}',
		'.country-dial{direction:ltr;unicode-bidi:isolate;text-align:right;}',
		'.country-name{font-size:12px;color:#6b7280;}',
		'.flag-emoji{font-size:17px;line-height:15px;display:inline-block;width:20px;text-align:center;}',
		'.flag-thumb img{width:20px;height:15px;border-radius:2px;object-fit:cover;}',
		'.country-code-text{flex:1;text-align:right;}',
		'.chevron{font-size:12px;color:#6b7280;}',
		'@media (max-width:767px){.fli-register-btn{height:32px !important;padding:5px 8px !important;font-size:11px !important;gap:3px !important;flex-shrink:0;}.fli-register-btn svg{width:11px !important;height:11px !important;}}',
		'@media (max-width:480px){.fli-register-btn svg{display:none !important;}}'
	].join('\n');
	document.head.appendChild(style);

	var modal = document.createElement('div');
	modal.id = 'register-modal';
	modal.className = 'register-modal';
	modal.setAttribute('aria-hidden', 'true');
	modal.innerHTML = [
		'<div class="register-modal__backdrop" id="register-modal-backdrop"></div>',
		'<div class="register-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="register-modal-title">',
		'  <button type="button" class="register-modal__close" id="register-modal-close" aria-label="إغلاق">×</button>',
		'  <h3 id="register-modal-title">نموذج التسجيل</h3>',
		'  <p class="register-modal__subtitle">املأ البيانات التالية لبدء التسجيل.</p>',
		'  <form class="register-form">',
		'    <div class="register-grid">',
		'      <label class="register-field"><span>الاسم الكامل *</span><input id="register-name" type="text" placeholder="اكتب اسمك" required></label>',
		'      <label class="register-field"><span>تاريخ الميلاد *</span><input id="register-dob" type="date" required></label>',
		'      <label class="register-field"><span>البريد الإلكتروني *</span><input id="register-email" type="email" placeholder="اكتب بريدك الإلكتروني" required></label>',
		'      <label class="register-field"><span>رمز الدولة *</span>',
		'        <div id="register-code-dropdown" class="country-code-dropdown">',
		'          <button type="button" class="country-code-trigger" aria-haspopup="listbox" aria-expanded="false">',
		'            <span class="flag-thumb"><img src="/assets/lms/flags/ye.svg" data-iso="ye" alt="Yemen flag" loading="lazy"></span>',
		'            <span class="country-code-text">+967 — اليمن</span>',
		'            <span class="chevron">▾</span>',
		'          </button>',
		'          <div class="country-code-menu" aria-hidden="true">',
		'            <input type="search" class="form-control country-code-search" placeholder="ابحث عن الدولة أو الرمز" aria-label="Search country code">',
		'            <div class="country-code-options" role="listbox"></div>',
		'          </div>',
		'          <input id="register-code" type="hidden" value="+967">',
		'        </div>',
		'      </label>',
		'      <label class="register-field"><span>رقم الهاتف (اتصال وواتساب) *</span><input id="register-phone" type="tel" inputmode="tel" placeholder="أدخل رقم الهاتف" required></label>',
		'    </div>',
		'    <div style="text-align:center;margin-top:16px;">',
		'      <button type="submit" id="register-submit" class="btn hero-cta" style="padding:12px 26px;">تسجيل</button>',
		'    </div>',
		'  </form>',
		'</div>'
	].join('\n');
	document.body.appendChild(modal);

	var openBtn = document.getElementById('open-register-modal');
	var closeBtn = document.getElementById('register-modal-close');
	var backdrop = document.getElementById('register-modal-backdrop');
	var form = modal.querySelector('.register-form');
	var nameInput = document.getElementById('register-name');
	var dobInput = document.getElementById('register-dob');
	var emailInput = document.getElementById('register-email');
	var codeInput = document.getElementById('register-code');
	var phoneInput = document.getElementById('register-phone');
	var codeDropdown = document.getElementById('register-code-dropdown');
	var codeTrigger = codeDropdown && codeDropdown.querySelector('.country-code-trigger');
	var codeMenu = codeDropdown && codeDropdown.querySelector('.country-code-menu');
	var codeOptionsBox = codeDropdown && codeDropdown.querySelector('.country-code-options');
	var codeSearch = codeDropdown && codeDropdown.querySelector('.country-code-search');

	var openModal = function (e) {
		e.preventDefault();
		modal.setAttribute('aria-hidden', 'false');
		modal.classList.add('is-open');
	};
	var closeModal = function () {
		modal.setAttribute('aria-hidden', 'true');
		modal.classList.remove('is-open');
	};

	// Convert Eastern Arabic-Indic digits (٠-٩ / ۰-۹) to ASCII digits
	var toAsciiDigits = function (s) {
		return (s || '').replace(/[٠-٩۰-۹]/g, function (d) {
			var c = d.charCodeAt(0);
			if (c >= 0x0660 && c <= 0x0669) return String(c - 0x0660);
			return String(c - 0x06F0);
		});
	};
	if (phoneInput) phoneInput.addEventListener('input', function () {
		var ascii = toAsciiDigits(phoneInput.value);
		if (ascii !== phoneInput.value) phoneInput.value = ascii;
	});

	modal.querySelectorAll('img[data-iso]').forEach(function (img) {
		img.addEventListener('error', function () { handleFlagError(img); });
	});

	if (openBtn) openBtn.addEventListener('click', openModal);
	if (closeBtn) closeBtn.addEventListener('click', closeModal);
	if (backdrop) backdrop.addEventListener('click', closeModal);

	// Country code dropdown (all countries via frappe geo service)
	var countryCodes = [];
	var fallbackCodes = [
		{ dial: '+967', name: 'Yemen', flag: 'ye' },
		{ dial: '+966', name: 'Saudi Arabia', flag: 'sa' },
		{ dial: '+971', name: 'United Arab Emirates', flag: 'ae' },
		{ dial: '+974', name: 'Qatar', flag: 'qa' }
	];

	var flagEmoji = function (iso) {
		return String.fromCodePoint.apply(null, (iso || '').toUpperCase().split('').map(function (c) {
			return 0x1F1E6 + c.charCodeAt(0) - 65;
		}));
	};

	// Replace a broken flag <img> with the country's flag emoji
	var handleFlagError = function (img) {
		var iso = img.getAttribute('data-iso');
		if (!iso) return;
		var span = document.createElement('span');
		span.className = 'flag-emoji';
		span.textContent = flagEmoji(iso);
		img.parentNode.replaceChild(span, img);
	};

	var mapInfoToCodes = function (info) {
		return Object.keys(info)
			.map(function (country) {
				var entry = info[country] || {};
				if (!entry.isd) return null;
				var iso = (entry.code || '').toLowerCase();
				var dial = '+' + String(entry.isd).replace(/^\+/, '');
				return { dial: dial, name: country, flag: iso };
			})
			.filter(Boolean)
			.sort(function (a, b) { return a.name.localeCompare(b.name); });
	};

	var loadCountryCodes = function () {
		return new Promise(function (resolve) {
			if (countryCodes.length) return resolve(countryCodes);
			var applyResult = function (codes) {
				countryCodes = codes && codes.length ? codes : fallbackCodes;
				resolve(countryCodes);
			};
			fetch('/api/method/frappe.geo.country_info.get_country_timezone_info')
				.then(function (res) { return res.json(); })
				.then(function (data) {
					applyResult(mapInfoToCodes((data.message || {}).country_info || {}));
				})
				.catch(function () { applyResult(fallbackCodes); });
		});
	};

	var renderCodes = function (items) {
		if (!codeOptionsBox) return;
		codeOptionsBox.innerHTML = items.map(function (item) {
			return '<button type="button" class="country-code-option" data-value="' + item.dial + '" data-name="' + item.name + '" aria-label="' + item.name + '">' +
				'<span class="flag-thumb"><img src="/assets/lms/flags/' + item.flag + '.svg" data-iso="' + item.flag + '" alt="' + item.name + '" loading="lazy"></span>' +
				'<div class="country-code-copy"><span class="country-dial" dir="ltr">' + item.dial + '</span><span class="country-name">' + item.name + '</span></div>' +
				'</button>';
		}).join('');
		codeOptionsBox.querySelectorAll('img[data-iso]').forEach(function (img) {
			img.addEventListener('error', function () { handleFlagError(img); });
		});
		codeOptionsBox.querySelectorAll('.country-code-option').forEach(function (btn) {
			btn.addEventListener('click', function () {
				var dial = btn.getAttribute('data-value');
				var name = btn.getAttribute('data-name');
				if (codeInput) codeInput.value = dial;
				var flagImg = btn.querySelector('img') && btn.querySelector('img').src;
				var triggerFlag = codeTrigger && codeTrigger.querySelector('.flag-thumb img');
				if (triggerFlag && flagImg) triggerFlag.src = flagImg;
				var triggerText = codeTrigger && codeTrigger.querySelector('.country-code-text');
				if (triggerText) triggerText.textContent = dial + ' — ' + name;
				codeDropdown && codeDropdown.classList.remove('open');
				codeTrigger && codeTrigger.setAttribute('aria-expanded', 'false');
				codeMenu && codeMenu.setAttribute('aria-hidden', 'true');
			});
		});
	};

	if (codeTrigger && codeMenu) {
		loadCountryCodes().then(function (list) {
			renderCodes(list && list.length ? list : fallbackCodes);
		});

		codeTrigger.addEventListener('click', function (e) {
			e.preventDefault();
			var open = codeDropdown.classList.toggle('open');
			codeTrigger.setAttribute('aria-expanded', open ? 'true' : 'false');
			codeMenu.setAttribute('aria-hidden', open ? 'false' : 'true');
			if (open && codeSearch) codeSearch.focus();
		});

		if (codeSearch) codeSearch.addEventListener('input', function (e) {
			var term = (e.target.value || '').toLowerCase();
			var source = countryCodes.length ? countryCodes : fallbackCodes;
			renderCodes(source.filter(function (c) {
				return (c.dial + ' ' + c.name).toLowerCase().indexOf(term) !== -1;
			}));
		});

		document.addEventListener('click', function (evt) {
			if (!codeDropdown.contains(evt.target) && codeDropdown.classList.contains('open')) {
				codeDropdown.classList.remove('open');
				codeTrigger.setAttribute('aria-expanded', 'false');
				codeMenu.setAttribute('aria-hidden', 'true');
			}
		});
	}

	if (form) form.addEventListener('submit', function (e) {
		e.preventDefault();
		var msg = [
			'تسجيل جديد',
			'الاسم: ' + (nameInput ? nameInput.value : ''),
			'تاريخ الميلاد: ' + (dobInput ? dobInput.value : ''),
			'البريد الإلكتروني: ' + (emailInput ? emailInput.value : ''),
			'رمز الدولة: ' + (codeInput ? codeInput.value : ''),
			'رقم الهاتف: ' + (phoneInput ? toAsciiDigits(phoneInput.value) : '')
		].join('\n');
		window.location.href = 'https://wa.me/967781405000?text=' + encodeURIComponent(msg);
	});
})();
