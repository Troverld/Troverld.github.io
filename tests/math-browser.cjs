/* Optional browser regression: NODE_PATH=/path/to/node_modules node tests/math-browser.cjs [preview URL] */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {})
  });
  try {
    const page = await browser.newPage();
    // Article rendering must work with all external network access disabled.
    await page.route('https://**', route => route.abort());
    const exceptions = [];
    page.on('pageerror', error => exceptions.push(error.message));
    await page.goto(new URL('posts/moe/', process.argv[2] || 'http://127.0.0.1:1313/').href);
    await page.waitForFunction(() => window.MathJax?.startup?.promise && document.querySelector('mjx-container[jax="SVG"]'));
    await page.evaluate(() => MathJax.startup.promise);
    assert.equal(await page.locator('mjx-merror, [data-mml-node="merror"]').count(), 0, 'MoE math errors');
    assert.equal(await page.locator('mjx-container[jax="SVG"]').count(), 228, 'MoE math count');
    await page.waitForSelector('.mermaid[data-rendered="true"] svg');

    const result = await page.evaluate(async () => {
      const failures = [];
      const macros = MathJax.config.tex.macros;
      for (const [name, definition] of Object.entries(macros)) {
        const expansion = Array.isArray(definition) ? definition[0] : definition;
        const args = name === 'unicodeInt' ? '{x222F}' : '{x}{y}';
        try {
        const actual = await MathJax.tex2mmlPromise(`\\${name}${args}`);
        const expectedSource = Array.isArray(definition)
          ? expansion.replace(/#1/g, name === 'unicodeInt' ? 'x222F' : 'x') + (name === 'unicodeInt' ? '' : '{y}')
          : `${expansion}${args}`;
        const expected = await MathJax.tex2mmlPromise(expectedSource);
        if (actual.includes('<merror') || actual !== expected) failures.push(name);
        } catch (error) { failures.push(`${name}: ${error.message}`); }
      }
      // Independent checks ensure critical aliases produce the intended symbols.
      const examples = { sube: '⊆', supe: '⊇', sub: '⊂', isin: '∈', infin: '∞', lang: '⟨', rang: '⟩' };
      for (const [name, symbol] of Object.entries(examples)) {
        const mml = await MathJax.tex2mmlPromise(`A \\${name} B`);
        if (!new DOMParser().parseFromString(mml, 'application/xml').documentElement.textContent.includes(symbol)) failures.push(`${name}: expected ${symbol}`);
      }
      await MathJax.tex2mmlPromise('\\newcommand{\\R}{\\mathbb R}\\newcommand{\\blogcur}[1]{\\left\\{#1\\right\\}}');
      const custom = await MathJax.tex2mmlPromise('\\blogcur{x} \\sube \\R');
      if (custom.includes('<merror') || !new DOMParser().parseFromString(custom, 'application/xml').documentElement.textContent.includes('⊆') || !custom.includes('R')) failures.push('newcommand');
      const extensions = await MathJax.tex2mmlPromise('\\ce{H2O} + \\cancel{x} + \\text{\\textbf{bold}}');
      if (extensions.includes('<merror')) failures.push('extension autoload/textmacros');
      return { aliases: Object.keys(macros).length, failures, output: MathJax.startup.output.name };
    });
    assert.equal(result.aliases, 101);
    assert.deepEqual(result.failures, []);
    assert.equal(result.output, 'SVG');
    assert.equal(await page.evaluate(() => MathJax.config.svg.fontCache), 'global');
    assert.deepEqual(exceptions, []);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'mobile overflow');
    assert(await page.locator('.prose sup').count() > 0, 'text superscript rendered');
    assert.equal(await page.locator('.mermaid svg').evaluateAll(graphics => graphics.filter(svg =>
      svg.getBoundingClientRect().width + 1 < svg.viewBox.baseVal.width).length), 0, 'diagram labels retain native size');
    const lineBreaks = await page.evaluate(async () => {
      const cases = [
        [String.raw`a=b\\c=d`, 2],
        [String.raw`a=b\newline c=d`, 2],
        [String.raw`\begin{aligned}a&=b\\c&=d\end{aligned}`, 2],
        [String.raw`\begin{bmatrix}a&b\\c&d\end{bmatrix}`, 2],
        [String.raw`\begin{cases}a&x>0\\b&x<0\end{cases}`, 2],
        [String.raw`\displaylines{a=b\\c=d}`, 2],
        [String.raw`\begin{bmatrix}a\\b\end{bmatrix}\\c=d`, 2],
        ["a=b % ignored \\\\\n+c=d", 0]
      ];
      const failures = [];
      for (const [source, rows] of cases) {
        const mml = await MathJax.tex2mmlPromise(source, { display: true });
        const xml = new DOMParser().parseFromString(mml, 'application/xml');
        const actual = xml.querySelector('mtable')?.children.length || 0;
        if (actual !== rows || xml.querySelector('merror')) failures.push({ source, expected: rows, actual });
      }
      // A macro body containing line breaks must retain its scope.
      await MathJax.tex2mmlPromise(String.raw`\newcommand{\blogrows}[1]{\begin{bmatrix}#1\\#1\end{bmatrix}}`);
      const defined = await MathJax.tex2mmlPromise(String.raw`\blogrows{x}`);
      if (new DOMParser().parseFromString(defined, 'application/xml').querySelectorAll('mtr').length !== 2) failures.push('macro body/scope');
      return failures;
    });
    assert.deepEqual(lineBreaks, [], 'display math line breaks');
    await page.evaluate(async () => {
      const fixture = document.createElement('div');
      fixture.id = 'layout-fixture';
      fixture.className = 'prose';
      const ordinary = document.createElement('p');
      ordinary.style.width = '240px';
      ordinary.append('前面的文字占用一部分空间，');
      const formula = document.createElement('span');
      formula.className = 'math-inline';
      formula.textContent = String.raw`\(a+b+c+d+e=f\)`;
      ordinary.append(formula, '，这是后面的文字。');
      const wide = document.createElement('p');
      wide.style.width = '240px';
      const oversized = document.createElement('span');
      oversized.className = 'math-inline';
      oversized.textContent = '\\(' + Array.from({ length: 40 }, (_, i) => `a_{${i}}`).join('+') + '\\)';
      wide.append(oversized);
      fixture.append(ordinary, wide);
      document.querySelector('main').append(fixture);
      await MathJax.typesetPromise([fixture]);
    });
    for (const width of [1280, 390]) {
      await page.setViewportSize({ width, height: 900 });
      const layout = await page.evaluate(() => ({
        scrollingFormulas: [...document.querySelectorAll('.math-inline, .math-inline mjx-container')].filter(element =>
          ['auto', 'scroll'].includes(getComputedStyle(element).overflowX) ||
          ['auto', 'scroll'].includes(getComputedStyle(element).overflowY)).length,
        tooWide: [...document.querySelectorAll('#layout-fixture svg')].filter(svg =>
          svg.getBoundingClientRect().width > 240.5).length,
        pageOverflow: document.documentElement.scrollWidth > innerWidth
      }));
      assert.deepEqual(layout, { scrollingFormulas: 0, tooWide: 0, pageOverflow: false }, `inline layout at ${width}px`);
    }
    console.log(`PASS: MoE's 228 math fragments, Mermaid, ${result.aliases} aliases, newcommand, extension autoload, display line breaks and inline layout.`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
