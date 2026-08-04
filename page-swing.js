// Swing transition al navegar entre páginas del sitio
(function () {
  const links = document.querySelectorAll('a.nav-tab, a[href$=".html"]');

  links.forEach((link) => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      // ignora links externos, anchors, o si abre en pestaña nueva
      if (!href || href.startsWith('http') || href.startsWith('#') || link.target === '_blank') return;

      e.preventDefault();
      document.getElementById('page-wrapper').classList.add('swing-out');
      setTimeout(() => {
        window.location.href = href;
      }, 320); // debe coincidir con la duración de swing-out
    });
  });
})();