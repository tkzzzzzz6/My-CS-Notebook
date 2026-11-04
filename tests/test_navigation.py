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
        self.assertEqual([item.title for item in nav.items], [
            "🏡 主页", "🦔 概率图/因果推断", "🕊️ 机器学习/深度学习",
            "🦃️ 数据结构/算法", "🐊 编程语言", "🦖 计算机系统",
            "🐳 杂谈与总结", "🌾 实习与找工",
        ])
        entries = self.entries(nav)
        paths = [path for path, _, _ in entries]
        expected = {path.relative_to(self.docs).as_posix() for path in self.docs.rglob("*.md")}
        self.assertEqual(set(paths), expected)
        self.assertEqual(len(paths), len(expected))
        pgm = [(path, title) for path, parents, title in entries if parents == ("🦔 概率图/因果推断", "概率图模型")]
        self.assertEqual([title for _, title in pgm[1:]], [
            "01. Introduction", "02. Directed Graph Model", "03. Exact Inference",
        ])
        greedy = next(entry for entry in entries if entry[0] == "Leetcode/Greedy.md")
        self.assertEqual(greedy[2], "贪心")

    def test_new_articles_go_to_their_existing_categories(self):
        categories = {
            "PGM/auto.md": ("🦔 概率图/因果推断", "概率图模型"),
            "ML/auto.md": ("🕊️ 机器学习/深度学习", "🐯 机器学习与数据挖掘", "统计机器学习"),
            "ML/CS246/auto.md": ("🕊️ 机器学习/深度学习", "🐯 机器学习与数据挖掘", "CS246-数据挖掘课程笔记"),
            "Papers/auto.md": ("🕊️ 机器学习/深度学习", "🐍 论文阅读"),
            "Jobs/2021spring/intern5.md": ("🌾 实习与找工", "2021春招", "面试准备"),
            "Jobs/2024spring/auto.md": ("🌾 实习与找工",),
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
        self.write("DB/CMU15-445/lab/project10.md", "# Project 10\n")
        entries = {path: parents for path, parents, _ in self.entries(self.navigation())}
        self.assertEqual(entries["PL/Rust/index.md"], ("🐊 编程语言", "Rust"))
        self.assertEqual(entries["Extra/index.md"], ("Extra",))
        self.assertEqual(entries["DB/CMU15-445/lab/project10.md"][:3], (
            "🦖 计算机系统", "🐶 数据库系统", "CMU15-445 Database Systems",
        ))

    def test_titles_and_natural_filename_order(self):
        self.write("PGM/auto10.md", "# 第十篇\n")
        self.write("PGM/auto2.md", "---\ntitle: 自定义导航标题\n---\n# 第二篇\n")
        entries = self.entries(self.navigation())
        automatic = [(path, title) for path, _, title in entries if path.startswith("PGM/auto")]
        self.assertEqual(automatic, [
            ("PGM/auto2.md", "自定义导航标题"), ("PGM/auto10.md", "第十篇"),
        ])

    def test_removed_and_renamed_pages_leave_no_broken_menu_links(self):
        old_path = "PGM/CMU10-708PGM01：Introduction.md"
        (self.docs / old_path).unlink()
        (self.docs / "about.md").unlink()
        (self.docs / "OS/index.md").unlink()
        self.write("PGM/renamed-intro.md", "# Renamed introduction\n")
        config_path = self.docs / ".nav.yml"
        before = config_path.read_bytes()
        nav = self.navigation()
        entries = {path: parents for path, parents, _ in self.entries(nav)}
        self.assertNotIn(old_path, entries)
        self.assertNotIn("about.md", entries)
        self.assertNotIn("OS/index.md", entries)
        self.assertEqual(entries["PGM/renamed-intro.md"], ("🦔 概率图/因果推断", "概率图模型"))
        self.assertEqual(config_path.read_bytes(), before)

        def check_links(items):
            for item in items:
                if item.is_section:
                    check_links(item.children)
                elif item.is_link:
                    self.assertNotIn(item.url, {old_path, "about.md", "OS/index.md"})

        check_links(nav.items)


if __name__ == "__main__":
    unittest.main()
