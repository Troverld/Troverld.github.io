const diagrams = [...document.querySelectorAll('pre.mermaid')];
try {
  const { default: mermaid } = await import('../vendor/mermaid/11.12.0/mermaid.esm.min.mjs');
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral', suppressErrorRendering: true });
  // Render separately so a malformed diagram cannot break the rest of the article.
  for (const [index, element] of diagrams.entries()) {
    try {
      const { svg } = await mermaid.render(`diagram-${index}`, element.textContent);
      element.innerHTML = svg;
      // Preserve the diagram's readable native size. The surrounding pre
      // scrolls wide diagrams instead of shrinking their labels to a few pixels.
      const graphic = element.querySelector('svg');
      if (graphic?.viewBox.baseVal.width) {
        graphic.setAttribute('width', graphic.viewBox.baseVal.width);
        graphic.setAttribute('height', graphic.viewBox.baseVal.height);
      }
      element.tabIndex = 0;
      element.dataset.rendered = 'true';
    } catch (error) {
      element.dataset.error = 'true';
      console.error('流程图渲染失败，保留源码。', error);
    }
  }
} catch (error) {
  console.error('流程图脚本加载失败，保留源码。', error);
}
