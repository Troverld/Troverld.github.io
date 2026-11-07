# Third-party notices

## MathJax texvc compatibility macros

`static/js/math.js` includes the complete macro definitions from:

- MathJax 2.7.9, `unpacked/extensions/TeX/mediawiki-texvc.js`
- Source: https://github.com/mathjax/MathJax/blob/2.7.9/unpacked/extensions/TeX/mediawiki-texvc.js
- Copyright (c) 2015-2020 The MathJax Consortium
- License: Apache License 2.0; see [LICENSES/MathJax-Apache-2.0.txt](LICENSES/MathJax-Apache-2.0.txt)

The v2 `Macro` definitions were converted to MathJax v3 `tex.macros` syntax. The configuration also applies Typora's Unicode text-range classification, plus two missing Unicode ranges (currency symbols and control pictures) to prevent MathJax 3.2.2 parser exceptions for the euro and visible-space aliases. All 101 entries were independently compared with the table shipped in the official Typora 1.10.8 Linux amd64 package (`resources/window.html`); their names and expansions match. The table was adapted from the open-source MathJax source, rather than copying Typora application code.

The official package used for comparison was https://typora.io/linux/typora_1.10.8_amd64.deb (SHA256 `edabb14ed75569fbccd9f229415bc47b2d50e9e2d51b798b7637595dca9213f4`). Its bundled MathJax reports version 3.2.2 and uses SVG output. This comparison establishes that version's built-in alias table, not parity with every Typora version, optional extension, or user setting.

## Vendored browser runtimes

The official npm distributions of MathJax 3.2.2 (`tex-svg-full.js` and TeX extensions) and Mermaid 11.12.0 (minified ES modules and diagram chunks) are served from `static/vendor/` on the site's own origin. Their runtime source is unmodified; source maps are omitted. Bundled dependency copyright and license comments remain intact.

- MathJax: Apache License 2.0; `static/vendor/mathjax/3.2.2/LICENSE.txt`.
- Mermaid: MIT License; `static/vendor/mermaid/11.12.0/LICENSE.txt`.

`scripts/vendor-libraries.mjs` reproduces these copies from the pinned npm packages. MathJax's SVG font cache is shared across the document, and the article head preloads runtime entry points. No third-party rendering CDN is needed at runtime.

Display-math top-level line breaks use MathJax `\displaylines`, following the behavior described in Typora’s official math documentation (https://support.typora.io/Math/#line-breaking). A TeX prefilter leaves breaks inside groups, macro definitions, and explicit environments to MathJax itself. Inline layout uses native MathJax baselines with responsive SVG sizing.
