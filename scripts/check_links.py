"""Fail if any internal link or #anchor in the rendered site is broken.

Checks every href/src in _site/**/*.html that points inside the site, plus
#fragments against the target page's ids. External links (http, mailto) are
not fetched: they are flaky in CI and are checked by hand before a release.

Usage (after `quarto render`):  python scripts/check_links.py [_site]
Exit codes: 0 = clean, 1 = broken links, 2 = no site to check.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_SCHEMES = ("http:", "https:", "mailto:", "tel:", "data:", "javascript:")


class Page(HTMLParser):
    """Collects link targets and element ids from one HTML file."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                self.ids.add(value)
            elif name in ("href", "src"):
                self.links.append(value)


def parse(path: Path) -> Page:
    page = Page()
    page.feed(path.read_text(encoding="utf-8", errors="replace"))
    return page


def resolve(site: Path, page: Path, target: str) -> Path:
    if target.startswith("/"):
        out = site / target.lstrip("/")
    else:
        out = page.parent / target
    if out.is_dir() or target.endswith("/"):
        out = out / "index.html"
    return out.resolve()


def main(argv: list[str]) -> int:
    site = Path(argv[1] if len(argv) > 1 else "_site").resolve()
    pages = sorted(site.rglob("*.html"))
    if not pages:
        print(f"check_links: no HTML found in {site}. Run `quarto render` first.")
        return 2
    cache: dict[Path, Page] = {}

    def get(path: Path) -> Page:
        if path not in cache:
            cache[path] = parse(path)
        return cache[path]

    broken: list[str] = []
    for page in pages:
        for link in get(page).links:
            if link.startswith(SKIP_SCHEMES) or link.startswith("//") or "${" in link:
                continue
            parts = urlsplit(link)
            path_part, fragment = unquote(parts.path), unquote(parts.fragment)
            target = resolve(site, page, path_part) if path_part else page.resolve()
            rel = page.relative_to(site).as_posix()
            if not target.exists():
                broken.append(f"{rel}: {link} (no such file)")
                continue
            if fragment and target.suffix == ".html" and fragment not in get(target).ids:
                broken.append(f"{rel}: {link} (no #{fragment} on that page)")
    if broken:
        print(f"check_links: {len(broken)} broken link(s):")
        for line in broken:
            print(f"  {line}")
        return 1
    print(f"check_links: clean ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
