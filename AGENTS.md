# AGENTS.md

## 1. 项目概述与愿景

这是一个基于 **Hugo** 和 **GitHub Pages** 的超轻量个人博客系统。
**核心原则**：
1. **极致精简与性能**：页面 0 动画、无复杂交互配色，极小资源占用，毫秒级本地编译，极速 CI/CD 部署。
2. **纯粹的内容创作**：平时发布仅需向 `content/posts/` 拖入一个 `.txt` 或 `.md`格式的文本，统一视作 markdown 文档，无 YAML Frontmatter 也必须正常工作。
3. **“双层元数据”需求**：
   - **对外元数据**（目录页展示、网页 `<title>`、`<meta description>` SEO）：公开标题、公开简介。
   - **对内元数据**（正文页顶部展示）：真实标题、真实简介。
   - **元数据 UI**：本地提供单文件 Python 脚本，以图形化表格管理元数据，保存为 `data/metadata.json`。若未配置，严格执行自动 Fallback 机制，严禁报错。
4. **渲染支持**：与 typora 完全相同的渲染体验，需要支持 html/mermaid 流程图等渲染，以及 `\newcommand` 等操作。
5. **评论系统**：基于 Giscus（GitHub Discussions），按 URL pathname 映射，纯文本按钮或滚动按需懒加载。

---

## 2. 技术栈标准

- **SSG 引擎**：Hugo（纯静态输出，建议配置 Goldmark 为 Markdown 渲染器）
- **样式方案**：原生纯手写 CSS，禁止引入 CSS 框架（Tailwind/Bootstrap 等），严禁任何 `transition` 和 `animation`。
- **本地管理 UI**：使用 `uv` 管理 python 库和 python 版本。
- **评论系统**：Giscus（配置为无边框浅色主题 `noborder_light`）。
- **部署环境**：GitHub Actions + GitHub Pages。

---

## 3. 目录结构规范

Agent 需按以下结构初始化或维护工程：

```text
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 自动编译部署
├── archetypes/
│   └── default.md
├── content/
│   └── posts/                  # 用户存放纯 .md 文件的目录
├── data/
│   └── metadata.json           # 存储双标题/简介/日期的映射文件
├── layouts/
│   ├── _default/
│   │   ├── baseof.html         # 全局骨架
│   │   ├── list.html           # 首页/目录页（读取对外元数据）
│   │   └── single.html         # 文章正文页（读取真实元数据 + Mermaid + Giscus）
│   └── index.html              # 首页重定向或等同于 list.html
├── static/
│   └── css/
│       └── style.css           # 极简黑白/Typora排版样式
├── admin.py                    # 本地管理 UI 脚本（双击或命令行启动）
├── hugo.toml                   # Hugo 配置文件
└── AGENTS.md