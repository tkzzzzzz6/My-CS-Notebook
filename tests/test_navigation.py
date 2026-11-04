"""Exercise the real navigation rules with temporary articles, never published files."""

import shutil
import tempfile
import unittest
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation


REPO = Path(__file__).resolve().parents[1]


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        shutil.copyfile(REPO / "docs/.nav.yml", self.docs / ".nav.yml")
        for source in (REPO / "docs").rglob("*.md"):
            self.write(source.relative_to(REPO / "docs").as_posix(), "# Fixture\n")

    def write(self, path, content):
        destination = self.docs / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def navigation(self):
        config = MkDocsConfig(config_file_path=str(self.root / "mkdocs.yml"))
        config.load_dict({
            "site_name": "Navigation test",
            "docs_dir": str(self.docs),
            "site_dir": str(self.root / "site"),
            "plugins": ["awesome-nav"],
            "hooks": [str(REPO / "hooks/navigation.py")],
        })
        errors, _ = config.validate()
        self.assertEqual(errors, [])
        config = config.plugins.on_config(config)
        files = config.plugins.on_files(get_files(config), config=config)
        nav = config.plugins.on_nav(get_navigation(files, config), config=config, files=files)
        for page in nav.pages:
            page.read_source(config)
        return nav

    @staticmethod
    def entries(nav):
        result = []

        def walk(items, parents=()):
            for item in items:
                if item.is_section:
                    walk(item.children, parents + (item.title,))
                elif item.is_page:
                    result.append((item.file.src_uri, parents, item.title))

        walk(nav.items)
        return result

    def test_existing_categories_names_order_and_no_duplicates(self):
        nav = self.navigation()
        self.assertEqual([item.title for item in nav.items[:6]], [
            "🏡 主页", "⚙️ AI Infra", "🤖 Agent", "🧩 多模态 Pipeline",
            "📚 基础与参考", "🧪 实验项目",
        ])
        entries = self.entries(nav)
        paths = [path for path, _, _ in entries]
        expected = {path.relative_to(self.docs).as_posix() for path in self.docs.rglob("*.md")}
        self.assertEqual(set(paths), expected)
        self.assertEqual(len(paths), len(expected))
        ml = [(path, title) for path, parents, title in entries if parents == ("📚 基础与参考", "统计学习与数据处理", "统计机器学习")]
        self.assertEqual([title for _, title in ml[:3]], [
            "01：机器学习中的基本概念", "02：贝叶斯定理", "03：线性模型",
        ])
        greedy = next(entry for entry in entries if entry[0] == "Leetcode/Greedy.md")
        self.assertEqual(greedy[2], "贪心")

    def test_new_articles_go_to_their_existing_categories(self):
        categories = {
            "AIInfra/auto.md": ("⚙️ AI Infra",),
            "Agents/auto.md": ("🤖 Agent",),
            "Multimodal/auto.md": ("🧩 多模态 Pipeline",),
            "Projects/auto.md": ("🧪 实验项目",),
            "OS/auto.md": ("📚 基础与参考", "计算机系统", "🐒 操作系统"),
            "ML/auto.md": ("📚 基础与参考", "统计学习与数据处理", "统计机器学习"),
            "ML/CS246/auto.md": ("📚 基础与参考", "统计学习与数据处理", "CS246-数据挖掘课程笔记"),
            "Papers/auto.md": ("📚 基础与参考", "大模型与多模态论文"),
            "root-article.md": ("🏡 主页",),
            "主页/auto.md": ("🏡 主页",),
        }
        for path in categories:
            self.write(path, "# New article\n")
        entries = {path: parents for path, parents, _ in self.entries(self.navigation())}
        for path, parents in categories.items():
            with self.subTest(path=path):
                self.assertEqual(entries[path], parents)

    def test_new_directories_and_nested_courses_are_discovered(self):
        self.write("PL/Rust/index.md", "# Rust\n")
        self.write("Extra/index.md", "# Extra\n")
        self.write("AIInfra/Serving/index.md", "# Serving\n")
        self.write("Agents/Runtime/recovery.md", "# Recovery\n")
        self.write("Multimodal/Data/schema.md", "# Schema\n")
        self.write("DB/CMU15-445/lab/project10.md", "# Project 10\n")
        entries = {path: parents for path, parents, _ in self.entries(self.navigation())}
        self.assertEqual(entries["PL/Rust/index.md"], ("📚 基础与参考", "编程语言", "Rust"))
        self.assertEqual(entries["Extra/index.md"], ("Extra",))
        self.assertEqual(entries["AIInfra/Serving/index.md"], ("⚙️ AI Infra", "Serving"))
        self.assertEqual(entries["Agents/Runtime/recovery.md"], ("🤖 Agent", "Runtime"))
        self.assertEqual(entries["Multimodal/Data/schema.md"], ("🧩 多模态 Pipeline", "Data"))
        self.assertEqual(entries["DB/CMU15-445/lab/project10.md"][:4], (
            "📚 基础与参考", "计算机系统", "🐶 数据库系统", "CMU15-445 Database Systems",
        ))

    def test_titles_and_natural_filename_order(self):
        self.write("AIInfra/auto10.md", "# 第十篇\n")
        self.write("AIInfra/auto2.md", "---\ntitle: 自定义导航标题\n---\n# 第二篇\n")
        entries = self.entries(self.navigation())
        automatic = [(path, title) for path, _, title in entries if path.startswith("AIInfra/auto")]
        self.assertEqual(automatic, [
            ("AIInfra/auto2.md", "自定义导航标题"), ("AIInfra/auto10.md", "第十篇"),
        ])

    def test_removed_and_renamed_pages_leave_no_broken_menu_links(self):
        old_path = "OS/操作系统1-导论.md"
        (self.docs / old_path).unlink()
        (self.docs / "about.md").unlink()
        (self.docs / "System/index.md").unlink()
        self.write("OS/renamed-intro.md", "# Renamed introduction\n")
        config_path = self.docs / ".nav.yml"
        before = config_path.read_bytes()
        nav = self.navigation()
        entries = {path: parents for path, parents, _ in self.entries(nav)}
        self.assertNotIn(old_path, entries)
        self.assertNotIn("about.md", entries)
        self.assertNotIn("System/index.md", entries)
        self.assertEqual(entries["OS/renamed-intro.md"], ("📚 基础与参考", "计算机系统", "🐒 操作系统"))
        self.assertEqual(config_path.read_bytes(), before)

        def check_links(items):
            for item in items:
                if item.is_section:
                    check_links(item.children)
                elif item.is_link:
                    self.assertNotIn(item.url, {old_path, "about.md", "System/index.md"})

        check_links(nav.items)


if __name__ == "__main__":
    unittest.main()
