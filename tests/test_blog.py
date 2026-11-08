"""Contract checks: HUGO_BIN=hugo uv run python -m unittest discover -s tests -v."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("admin", ROOT / "admin.py")
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)
HUGO = os.environ.get("HUGO_BIN") or shutil.which("hugo")


class AdminTests(unittest.TestCase):
    def test_save_validation_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "metadata.json"
            with patch.object(admin, "METADATA", target):
                old = admin.revision()
                value = {"MoE.txt": {"real_title": "真实标题", "date": "2026-11-07",
                                     "created_at": "2026-11-07 09:05", "source_url": "https://example.org/post"}}
                new = admin.save_metadata(value, old)
                self.assertEqual(admin.read_metadata(), value)
                self.assertNotEqual(new, old)
                with self.assertRaises(FileExistsError):
                    admin.save_metadata({}, old)
                with self.assertRaises(ValueError):
                    admin.save_metadata({"MoE.txt": {"date": "2026-02-30"}}, new)
                for invalid in ("2026-02-30 09:05", "2026-11-07 24:00", "2026-11-07",
                                "2026-11-07T09:05", "2026-11-07 09:05:30", "2026-1-7 09:05", 123):
                    with self.subTest(created_at=invalid), self.assertRaises(ValueError):
                        admin.save_metadata({"MoE.txt": {"created_at": invalid}}, new)
                self.assertEqual(admin.read_metadata(), value)
                empty = {"MoE.txt": {"created_at": ""}}
                admin.save_metadata(empty, new)
                self.assertEqual(admin.read_metadata(), empty)

    def test_current_system_time_endpoint(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), admin.Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                url = f"http://127.0.0.1:{server.server_port}/api/time"
                with self.assertRaises(HTTPError) as error:
                    urlopen(url)
                self.assertEqual(error.exception.code, 403)
                with patch.object(admin, "datetime") as clock:
                    clock.now.return_value = datetime(2026, 11, 8, 21, 4, 59)
                    with urlopen(Request(url, headers={"X-Admin-Token": admin.TOKEN})) as response:
                        self.assertEqual(json.load(response), {"created_at": "2026-11-08 21:04"})
            finally:
                server.shutdown()
                worker.join()


@unittest.skipUnless(HUGO, "Install Hugo or set HUGO_BIN")
class HugoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.site = Path(self.temporary.name)
        for directory in ("layouts", "static"):
            shutil.copytree(ROOT / directory, self.site / directory)
        # Tests start with comments disabled, independently of the live site's IDs.
        config = (ROOT / "hugo.toml").read_text()
        config = re.sub(r"(?m)^(repoId|categoryId) = .*?$", r"\1 = ''", config)
        (self.site / "hugo.toml").write_text(config)
        (self.site / "content/posts").mkdir(parents=True)
        (self.site / "data").mkdir()

    def article(self, name, value):
        (self.site / "content/posts" / name).write_text(value, encoding="utf-8")

    def metadata(self, value):
        (self.site / "data/metadata.json").write_text(json.dumps(value), encoding="utf-8")

    def build(self):
        result = subprocess.run([HUGO, "--source", str(self.site), "--cleanDestinationDir"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.site / "public"

    def test_plain_files_math_and_missing_metadata(self):
        self.article("plain.txt", r'''# 正文标题

<div id="raw-html">HTML works</div>

$$
\newcommand{\cur}[1]{\left\{#1\right\}}
$$

$\cur{x_1}$ and \(a_b\).

\[x_i^2\]

```mermaid
graph TD
A --> B
```
''')
        self.article("simple.md", "普通 Markdown，无 frontmatter。")
        output = self.build()
        home = (output / "index.html").read_text()
        page = (output / "posts/plain/index.html").read_text()
        simple = (output / "posts/simple/index.html").read_text()
        self.assertIn("<title>plain</title>", page)
        self.assertIn("正文标题</h1>", page)
        self.assertNotIn("正文标题", home)
        self.assertIn("<p>I'm Troverld.</p>", home)
        self.assertNotIn('class="post-list"', home)
        self.assertIn('<div id="raw-html">HTML works</div>', page)
        self.assertIn(r"\newcommand{\cur}[1]{\left\{#1\right\}}", page)
        self.assertIn(r'\(a_b\)</span>', page)
        self.assertIn(r'\[x_i^2\]</div>', page)
        self.assertIn('class="mermaid"', page)
        self.assertIn('js/math.js', page)
        self.assertIn('js/mermaid.js', page)
        self.assertNotIn('rel="preload"', home)
        self.assertNotIn('rel="modulepreload"', home)
        self.assertIn('vendor/mathjax/3.2.2/tex-svg-full.js', page)
        self.assertIn('vendor/mermaid/11.12.0/mermaid.esm.min.mjs', page)
        self.assertNotIn('<script', home)
        self.assertNotIn('<script', simple)

    def test_math_inside_quotes_preserves_relations(self):
        self.article("quotes.txt", r'''---
title: Quoted math
---

> $$
> outer > 0
> $$
>
> > \[
> > nested > 1
> > \]
>
> $$
> preserve >0
> $$
>
> inline $a +
> b > 0$ end.

- > $$
  > listed > 2
  > $$

$$
plain > 3
$$
''')
        output = self.build()
        page = (output / "posts/quotes/index.html").read_text()
        from html import unescape
        import re
        blocks = [unescape(value) for value in re.findall(r'<div class="math-block">(.*?)</div>', page, re.S)]
        self.assertEqual(len(blocks), 5, page)
        self.assertIn("\\[\nouter > 0\n\\]", blocks)
        self.assertIn("\\[\nnested > 1\n\\]", blocks)
        self.assertIn("\\[\npreserve >0\n\\]", blocks)
        self.assertTrue(any("listed > 2" in value and "\n  >" not in value for value in blocks))
        self.assertIn("\\[\nplain > 3\n\\]", blocks)
        self.assertIn("\\(a +\nb > 0\\)", unescape(page))
        self.assertIn("<blockquote>", page)

    def test_github_alerts_preserve_markdown_and_math(self):
        types = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
        content = "\n\n".join(f"> [!{kind}]\n> {kind} body." for kind in types)
        content += r'''

> [!NOTE]
> **加粗**和[链接](https://example.org/)。
>
> - 列表项目
>
> $$
> x > 0
> $$
>
> ```mermaid
> graph TD
> A --> B
> ```

> 普通引用。

> [!CUSTOM]
> 自定义标记仍作为普通引用显示。

[!TIP] 普通文本。

```text
> [!WARNING]
> 代码原文。
```
'''
        self.article("alerts.txt", content)
        output = self.build()
        page = (output / "posts/alerts/index.html").read_text()
        for kind in types:
            self.assertIn(f'class="markdown-alert markdown-alert-{kind.lower()}"', page)
            self.assertIn(f'aria-label="{kind.title()}"', page)
            self.assertIn(f"{kind} body.", page)
        self.assertEqual(page.count('<aside class="markdown-alert '), 6)
        self.assertIn('<strong>加粗</strong>', page)
        self.assertIn('<a href="https://example.org/">链接</a>', page)
        self.assertIn('<li>列表项目</li>', page)
        self.assertIn("\\[\nx &gt; 0\n\\]", page)
        self.assertIn('class="mermaid"', page)
        self.assertIn('js/math.js', page)
        self.assertIn('js/mermaid.js', page)
        self.assertIn('普通引用。', page)
        self.assertIn('[!CUSTOM]', page)
        self.assertNotIn('markdown-alert-custom', page)
        self.assertIn('[!TIP] 普通文本。', page)
        self.assertIn('[!WARNING]', page)

    def test_text_superscript_preserves_tex_and_code(self):
        self.article("superscript.txt", r'''CV^2^ 与 L^p^。

`code^2^` 和 $x^2_{i}$。

$$
x^2+y^2=z^2
$$
''')
        output = self.build()
        page = (output / "posts/superscript/index.html").read_text()
        self.assertIn("CV<sup>2</sup>", page)
        self.assertIn("L<sup>p</sup>", page)
        self.assertIn("<code>code^2^</code>", page)
        self.assertIn(r"\(x^2_{i}\)", page)
        from html import unescape
        self.assertIn("x^2+y^2=z^2", unescape(page))

    def test_metadata_priority_and_invalid_optional_values(self):
        self.article("test.txt", "# 正文标题\n\n正文。")
        self.metadata({"test.txt": {"public_title": "公开标题", "public_description": "公开简介",
                                    "real_title": "内部标题", "real_description": "内部简介",
                                    "created_at": "2026-11-07 09:05"}})
        output = self.build()
        listing = (output / "posts/index.html").read_text()
        page = (output / "posts/test/index.html").read_text()
        head = page.split('</head>')[0]
        self.assertIn("公开标题", listing)
        self.assertIn("摘要：公开简介</p>", listing)
        self.assertNotIn("内部标题", listing)
        self.assertNotIn("内部简介", listing)
        self.assertIn("<title>内部标题</title>", head)
        self.assertIn('content="公开简介"', head)
        self.assertNotIn("内部简介", head)
        self.assertIn("内部标题</h1>", page)
        self.assertIn("摘要：内部简介</p>", page)
        self.assertIn('datetime="2026-11-07T09:05"', page)
        self.metadata({"test.txt": {"public_title": 3, "public_description": "  ",
                                    "date": "2026-99-99", "real_title": "内部标题",
                                    "real_description": "内部简介"}})
        output = self.build()
        self.assertIn("<title>内部标题</title>", (output / "posts/test/index.html").read_text())
        listing = (output / "posts/index.html").read_text()
        self.assertIn("内部标题", listing)
        self.assertIn("摘要：内部简介</p>", listing)
        self.assertNotIn("<time", listing)
        self.metadata({"test.txt": {"public_title": "公开标题", "public_description": "公开简介"}})
        output = self.build()
        self.assertIn("公开标题", (output / "posts/index.html").read_text())
        self.assertIn("<title>test</title>", (output / "posts/test/index.html").read_text())
        self.metadata({"test.txt": "bad entry"})
        output = self.build()
        listing = (output / "posts/index.html").read_text()
        self.assertIn('href="/posts/test/">test</a>', listing)
        self.assertNotIn("摘要：", listing)
        self.assertIn("<title>test</title>", (output / "posts/test/index.html").read_text())

    def test_creation_time_sorting_and_navigation(self):
        # Frontmatter and legacy dates must not give an undated post a timestamp.
        self.article("missing.txt", '---\ndate: 2020-01-01\n---\n正文。')
        for name in ("invalid", "older", "newer", "tie-a", "tie-b"):
            self.article(f"{name}.txt", "正文。")
        self.metadata({
            "missing.txt": {"date": "2020-01-01"},
            "invalid.txt": {"created_at": "2026-02-30 10:00"},
            "older.txt": {"created_at": "2026-11-07 09:04", "public_title": "较早文章"},
            "newer.txt": {"created_at": "2026-11-07 09:05", "real_title": "较新文章"},
            "tie-a.txt": {"created_at": "2026-11-06 08:00"},
            "tie-b.txt": {"created_at": "2026-11-06 08:00"},
        })
        output = self.build()
        import re
        order = ["missing", "invalid", "newer", "older", "tie-b", "tie-a"]
        text = (output / "posts/index.html").read_text()
        self.assertEqual(re.findall(r'<h2><a href="/posts/([^/]+)/">', text), order)
        self.assertEqual(text.count('class="published-unknown">未知</span>'), 2)
        self.assertIn('<time datetime="2026-11-07T09:05">2026-11-07 09:05</time>', text)
        self.assertIn('class="post-heading"', text)
        for index, name in enumerate(order):
            page = (output / "posts" / name / "index.html").read_text()
            nav = page.split('<nav class="post-navigation"', 1)[1]
            if index + 1 < len(order):
                self.assertIn(f'rel="prev" href="/posts/{order[index + 1]}/"', nav)
            else:
                self.assertIn("前篇：无", nav)
                self.assertNotIn('rel="prev"', nav)
            if index:
                self.assertIn(f'rel="next" href="/posts/{order[index - 1]}/"', nav)
            else:
                self.assertIn("后篇：无", nav)
                self.assertNotIn('rel="next"', nav)
        page = (output / "posts/newer/index.html").read_text()
        self.assertIn('href="/posts/older/">较早文章</a>', page)
        self.metadata({"invalid.txt": {"created_at": 123}})
        self.build()

    def test_giscus_is_opt_in_and_base_path_works(self):
        self.article("test.md", "正文。")
        config = self.site / "hugo.toml"
        config.write_text(config.read_text().replace("repoId = ''", "repoId = 'R_test'")
                          .replace("categoryId = ''", "categoryId = 'DIC_test'")
                          .replace("https://troverld.github.io/", "https://example.org/blog/"))
        output = self.build()
        page = (output / "posts/test/index.html").read_text()
        self.assertIn('id="load-comments"', page)
        self.assertIn('/blog/js/comments.js', page)
        self.assertNotIn('src="https://giscus.app/client.js"', page)
        self.assertFalse((output / "data/metadata.json").exists())


if __name__ == "__main__":
    unittest.main()
