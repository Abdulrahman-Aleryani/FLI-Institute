// Small helpers for the static FLI website.
document.querySelectorAll('[aria-label="Switch language"]').forEach(function (b) {
  b.addEventListener('click', function () { location.href = window.FLI_OTHER_LANG; });
});
// Programs search: hides cards whose text does not contain the typed words.
var search = document.querySelector('input[type="search"], input[placeholder]');
if (search && document.querySelector('[data-program-card], article')) {
  search.addEventListener('input', function () {
    var q = search.value.toLowerCase();
    document.querySelectorAll('article').forEach(function (c) {
      c.style.display = c.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
    });
  });
}
// Mobile menu: show the desktop links as a simple dropdown.
document.querySelectorAll('[aria-label="Open menu"]').forEach(function (b) {
  b.addEventListener('click', function () {
    var nav = document.querySelector('header nav');
    if (!nav) return;
    var open = nav.classList.toggle('fli-open');
    nav.style.cssText = open ? 'display:flex;flex-direction:column;position:absolute;top:100%;left:0;right:0;padding:1rem;gap:.75rem;background:var(--background);z-index:50' : '';
  });
});
// Programs category buttons: show only cards of the chosen category.
document.querySelectorAll('button').forEach(function (b) {
  if (!document.querySelector('.program-card') || b.closest('article') || b.closest('header')) return;
  b.addEventListener('click', function () {
    var cat = b.textContent.trim();
    var all = /^(All|الكل)/.test(cat);
    document.querySelectorAll('article.program-card').forEach(function (c) {
      var tag = c.querySelector('.program-category');
      c.style.display = all || (tag && tag.textContent.trim() === cat) ? '' : 'none';
    });
  });
});
