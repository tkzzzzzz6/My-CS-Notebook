# My-CS-Notebook

网站：<https://notes.tanke.asia/>

## 日常发文

把 Markdown 文章放进 `docs/` 对应目录，提交并推送后，GitHub Actions 会自动生成导航、构建并发布网站。

例如新增 `docs/OS/08-Linux进程调度.md`：

```markdown
---
title: Linux 进程调度
---

# Linux 进程调度

文章正文……
```

```bash
git add "docs/OS/08-Linux进程调度.md"
# 有新图片时，也添加对应图片文件。
git commit -m "docs: 新增 Linux 进程调度笔记"
git push origin master
```

常规新增文章无需修改 `mkdocs.yml` 或导航规则。修改正文、删除或改名文章后，同样提交并推送即可。删除和改名时可用 `git add -A -- "对应文件或目录"` 暂存文件变动。

## 导航如何自动生成

- `mkdocs.yml`：站点地址、主题、插件等全局配置。
- `docs/.nav.yml`：保留原来的分类、显示名称和顺序，并用 `glob` 规则补充各目录中新出现的文章。
- `hooks/navigation.py`：构建时忽略已删除文章的固定导航条目，避免留下失效菜单；处理在内存中完成。
- `awesome-nav`：在本地预览和线上构建时读取这些规则，生成网站导航。

现有文章保留固定顺序，新发现的文章追加到对应栏目，并按文件名自然排序，例如 `09-...md`、`10-...md`。

自动发现的文章优先使用文章元数据中的 `title`，其次使用一级标题，最后使用文件名。原有固定导航条目的自定义显示名称优先。

常用目录与栏目对应关系：

| 文章位置 | 自动加入的栏目 |
| --- | --- |
| `docs/OS/` | 计算机系统 → 操作系统 |
| `docs/Papers/` | 机器学习/深度学习 → 论文阅读 |
| `docs/ML/*.md` | 机器学习与数据挖掘 → 统计机器学习 |
| `docs/ML/CS246/` | 机器学习与数据挖掘 → CS246 |
| `docs/PL/Go/` | 编程语言 → Go |
| `docs/PL/Rust/` 等新语言目录 | 编程语言下的新栏目 |
| `docs/` 下全新的一级目录 | 新的一级栏目 |

只有需要调整逻辑分类、指定特殊名称或固定顺序时，才编辑 `docs/.nav.yml`。新子目录也可以添加自己的 `.nav.yml` 来控制该目录的导航。

## 本地预览与验证

使用 Python 3.11，项目已提供 `.python-version`。使用 uv 创建环境：

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
mkdocs serve
```

本地预览：<http://127.0.0.1:8000/>。

```bash
python -m unittest discover -s tests -v
mkdocs build
```

导航测试会在临时目录验证新增文章、自然排序、子目录、标题、改名和删除，不会在网站中加入测试文章。

## 域名与发布

`docs/CNAME` 保存自定义域名，每次构建都会随网页一起发布。更换域名时同步修改它和 `mkdocs.yml` 的 `site_url`。

源文件提交到 `master`，生成的网页自动发布到 `gh-pages`；部署结果可在仓库的 Actions 页面查看。
