(() => {
  const layout = document.querySelector('.post-layout.has-toc');
  if (!layout) return;
  const content = layout.querySelector('.post-content');
  const button = layout.querySelector('.post-toc summary');

  function placeTOC() {
    // Leave 12px on each side of the panel, using the actual article position.
    const available = Math.floor(content.getBoundingClientRect().left - 24);
    const fits = available >= Math.ceil(button.getBoundingClientRect().width);
    layout.style.setProperty('--toc-gutter-width', `${Math.min(280, Math.max(0, available))}px`);
    layout.classList.toggle('toc-in-gutter', fits);
  }

  placeTOC();
  const observer = new ResizeObserver(placeTOC);
  observer.observe(document.body);
  observer.observe(button);
  window.addEventListener('resize', placeTOC, { passive: true });
})();
