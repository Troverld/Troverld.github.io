/*
 * Typora-compatible math configuration (MathJax 3.2.2, SVG output).
 * The complete texvc macro table below is adapted from MathJax 2.7.9:
 * https://github.com/mathjax/MathJax/blob/2.7.9/unpacked/extensions/TeX/mediawiki-texvc.js
 * Copyright (c) 2015-2020 The MathJax Consortium. Apache-2.0.
 * See LICENSES/MathJax-Apache-2.0.txt and THIRD_PARTY_NOTICES.md.
 * Changes: convert v2 Macro definitions to v3 configmacros entries.
 * All entries verified against Typora 1.10.8's window.html.
 */
const typoraMacros = {
  "AA": "Å",
  "alef": "\\aleph",
  "alefsym": "\\aleph",
  "Alpha": "\\mathrm{A}",
  "and": "\\land",
  "ang": "\\angle",
  "Bbb": "\\mathbb",
  "Beta": "\\mathrm{B}",
  "bold": "\\mathbf",
  "bull": "\\bullet",
  "C": "\\mathbb{C}",
  "Chi": "\\mathrm{X}",
  "clubs": "\\clubsuit",
  "cnums": "\\mathbb{C}",
  "Complex": "\\mathbb{C}",
  "coppa": "ϙ",
  "Coppa": "Ϙ",
  "Dagger": "\\ddagger",
  "Digamma": "Ϝ",
  "darr": "\\downarrow",
  "dArr": "\\Downarrow",
  "Darr": "\\Downarrow",
  "dashint": "\\unicodeInt{x2A0D}",
  "ddashint": "\\unicodeInt{x2A0E}",
  "diamonds": "\\diamondsuit",
  "empty": "\\emptyset",
  "Epsilon": "\\mathrm{E}",
  "Eta": "\\mathrm{H}",
  "euro": "€",
  "exist": "\\exists",
  "geneuro": "€",
  "geneuronarrow": "€",
  "geneurowide": "€",
  "H": "\\mathbb{H}",
  "hAar": "\\Leftrightarrow",
  "harr": "\\leftrightarrow",
  "Harr": "\\Leftrightarrow",
  "hearts": "\\heartsuit",
  "image": "\\Im",
  "infin": "\\infty",
  "Iota": "\\mathrm{I}",
  "isin": "\\in",
  "Kappa": "\\mathrm{K}",
  "koppa": "ϟ",
  "Koppa": "Ϟ",
  "lang": "\\langle",
  "larr": "\\leftarrow",
  "Larr": "\\Leftarrow",
  "lArr": "\\Leftarrow",
  "lrarr": "\\leftrightarrow",
  "Lrarr": "\\Leftrightarrow",
  "lrArr": "\\Leftrightarrow",
  "Mu": "\\mathrm{M}",
  "N": "\\mathbb{N}",
  "natnums": "\\mathbb{N}",
  "Nu": "\\mathrm{N}",
  "O": "\\emptyset",
  "oiint": "\\unicodeInt{x222F}",
  "oiiint": "\\unicodeInt{x2230}",
  "ointctrclockwise": "\\unicodeInt{x2233}",
  "officialeuro": "€",
  "Omicron": "\\mathrm{O}",
  "or": "\\lor",
  "P": "¶",
  "pagecolor": [
    "",
    1
  ],
  "part": "\\partial",
  "plusmn": "\\pm",
  "Q": "\\mathbb{Q}",
  "R": "\\mathbb{R}",
  "rang": "\\rangle",
  "rarr": "\\rightarrow",
  "Rarr": "\\Rightarrow",
  "rArr": "\\Rightarrow",
  "real": "\\Re",
  "reals": "\\mathbb{R}",
  "Reals": "\\mathbb{R}",
  "Rho": "\\mathrm{P}",
  "sdot": "\\cdot",
  "sampi": "ϡ",
  "Sampi": "Ϡ",
  "sect": "\\S",
  "spades": "\\spadesuit",
  "stigma": "ϛ",
  "Stigma": "Ϛ",
  "sub": "\\subset",
  "sube": "\\subseteq",
  "supe": "\\supseteq",
  "Tau": "\\mathrm{T}",
  "textvisiblespace": "␣",
  "thetasym": "\\vartheta",
  "uarr": "\\uparrow",
  "uArr": "\\Uparrow",
  "Uarr": "\\Uparrow",
  "unicodeInt": [
    "\\mathop{\\vcenter{\\mathchoice{\\huge\\unicode{#1}\\,}{\\unicode{#1}}{\\unicode{#1}}{\\unicode{#1}}}\\,}\\nolimits",
    1
  ],
  "varcoppa": "ϙ",
  "varstigma": "ϛ",
  "varointclockwise": "\\unicodeInt{x2232}",
  "vline": "\\smash{\\large\\lvert}",
  "weierp": "\\wp",
  "Z": "\\mathbb{Z}",
  "Zeta": "\\mathrm{Z}"
};

// Typora's "Apply Line Break at \\" mode uses MathJax's displaylines.
// Only wrap breaks outside groups/environments: matrix rows, macro bodies,
// comments and explicit aligned/displaylines already have their own semantics.
function hasDisplayLineBreak(source) {
  let groups = 0;
  let environments = 0;
  const tokens = source.match(/%[^\r\n]*|\\(?:begin|end)\s*\{[^}]+\}|\\[a-zA-Z]+|\\[\s\S]|[{}]/g) || [];
  for (const token of tokens) {
    if (token.startsWith('%')) continue;
    if (/^\\begin\s*\{/.test(token)) { environments++; continue; }
    if (/^\\end\s*\{/.test(token)) { environments--; continue; }
    if (token === '{') groups++;
    else if (token === '}') groups--;
    else if (!groups && !environments && (token === '\\\\' || token === '\\newline')) return true;
  }
  return false;
}

const mathSource = new URL('../vendor/mathjax/3.2.2/', document.currentScript.src);
window.MathJax = {
  loader: { paths: { mathjax: mathSource.href.replace(/\/$/, '') }, load: ['[tex]/textmacros'] },
  startup: {
    ready() {
      // Typora's MathJax 3.2.2 configuration classifies these Unicode
      // ranges as text (including currency signs and visible spaces).
      const ranges = MathJax._.core.MmlTree.OperatorDictionary.RANGES;
      for (const index of [28, 30, 33, 47]) ranges[index][3] = 'mtext';
      // These two Unicode blocks are absent from v3.2.2's range table.
      // Literal euro/visible-space aliases otherwise throw in BaseConfiguration.Other.
      ranges.push([0x20A0, 0x20CF, 0, 'mtext', 'normal'], [0x2400, 0x243F, 0, 'mtext', 'normal']);
      ranges.sort((left, right) => left[0] - right[0]);
      MathJax.startup.defaultReady();
      MathJax.startup.document.inputJax[0].preFilters.add(({ math }) => {
        if (math.display && hasDisplayLineBreak(math.math)) {
          math.math = '\\displaylines{' + math.math + '}';
        }
      });
    }
  },
  tex: {
    inlineMath: [['\\(', '\\)']],
    displayMath: [['\\[', '\\]']],
    processEscapes: true,
    macros: typoraMacros,
    packages: { '[+]': ['newcommand', 'textmacros'] },
    tags: 'none',
    useLabelIds: true,
    maxBuffer: 10 * 1024
  },
  options: { enableMenu: false, skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] },
  svg: { fontCache: 'global' }
};
const mathScript = document.createElement('script');
mathScript.id = 'MathJax-script';
mathScript.src = new URL('tex-svg-full.js', mathSource).href;
mathScript.async = true;
mathScript.onerror = () => { console.error('公式脚本加载失败；页面保留 TeX 原文。'); };
document.head.append(mathScript);
