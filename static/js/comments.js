const button = document.querySelector('#load-comments');
button?.addEventListener('click', () => {
  button.disabled = true;
  const status = document.querySelector('#comments-status');
  status.textContent = '正在加载评论…';
  const script = document.createElement('script');
  script.src = 'https://giscus.app/client.js';
  const settings = {
    repo: button.dataset.repo, 'repo-id': button.dataset.repoId,
    category: button.dataset.category, 'category-id': button.dataset.categoryId,
    mapping: 'pathname', strict: '1', 'reactions-enabled': '0',
    'emit-metadata': '0', 'input-position': 'top', theme: 'noborder_light', lang: 'zh-CN'
  };
  for (const [key, value] of Object.entries(settings)) script.setAttribute(`data-${key}`, value);
  script.crossOrigin = 'anonymous';
  script.async = true;
  script.onload = () => { status.textContent = ''; button.hidden = true; };
  script.onerror = () => { status.textContent = '加载失败，请重试。'; button.disabled = false; script.remove(); };
  document.querySelector('#giscus').append(script);
});
