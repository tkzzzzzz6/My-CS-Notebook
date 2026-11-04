"""Skip removed Markdown references before awesome-nav builds the navigation."""

import logging
import posixpath
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml

log = logging.getLogger("mkdocs.hooks.navigation")


def _missing_page(target, directory, pages):
    url = urlsplit(target)
    if url.scheme or url.netloc or url.path.startswith("/"):
        return False
    path = unquote(url.path)
    if not path.endswith((".md", ".markdown")):
        return False
    if any(char in path for char in "*?["):
        return False
    return posixpath.normpath(posixpath.join(directory, path)) not in pages


def _prune(items, directory, pages):
    result = []
    removed = 0
    for item in items:
        if isinstance(item, str):
            if _missing_page(item, directory, pages):
                removed += 1
                continue
        elif isinstance(item, dict) and "glob" not in item and len(item) == 1:
            title, target = next(iter(item.items()))
            if isinstance(target, list):
                children, count = _prune(target, directory, pages)
                removed += count
                if not children:
                    continue
                item = {title: children}
            elif isinstance(target, str) and _missing_page(target, directory, pages):
                removed += 1
                continue
        result.append(item)
    return result, removed


def on_files(files, *, config):
    """Change the build's in-memory config; never rewrite a user's .nav.yml."""
    pages = {file.src_uri for file in files.documentation_pages()}
    for file in files:
        path = PurePosixPath(file.src_uri)
        if path.name != ".nav.yml":
            continue
        data = yaml.safe_load(file.content_string) or {}
        if not isinstance(data, dict) or not isinstance(data.get("nav"), list):
            continue
        nav, removed = _prune(data["nav"], path.parent.as_posix(), pages)
        if removed:
            data["nav"] = nav
            file.content_string = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
            log.info("Navigation: skipped %s removed page(s) in %s", removed, file.src_uri)
    return files
