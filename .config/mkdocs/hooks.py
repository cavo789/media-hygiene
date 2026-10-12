"""MkDocs hooks: GitHub's heading anchors, and links leaving a language kept working.

The pages are written for GitHub first: their anchors keep accents (`#étape-1`), each
page links its twin in the other language (`../../fr/…`), which a language's build does
not hold, and some links point at files outside documentation/ (the READMEs, the CI).
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

from pymdownx.slugs import slugify

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page

BLOB: Final = "https://github.com/cavo789/media-hygiene/blob/main"
_LINK: Final = re.compile(r"(?P<head>\]\()(?P<target>[^)\s#]+)(?P<anchor>#[^)\s]*)?\)")
_EXTERNAL: Final = ("http://", "https://", "mailto:")
DEFAULT_LOCALE: Final = (
    "en"  # built at the root of the site, the others under /<locale>/
)
INDEX: Final = "README.md"


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    """Slug the headings like GitHub: lower case, accents kept.

    Args:
        config: The site configuration.

    Returns:
        The configuration, the `toc` extension set up.
    """
    config.mdx_configs.setdefault("toc", {})["slugify"] = slugify(case="lower")
    return config


def on_page_markdown(
    markdown: str, *, page: Page, config: MkDocsConfig, **_: object
) -> str:
    """Point the links to repository files outside documentation/ at GitHub.

    Args:
        markdown: The page source.
        page: The page.
        config: The site configuration.
        **_: The other arguments of the event (the site files).

    Returns:
        The source, those links rewritten.
    """
    docs = Path(config.docs_dir).resolve()
    repository = docs.parent
    source = Path(page.file.abs_src_path or docs).resolve()
    locale = source.relative_to(docs).parts[0]

    def rewrite(link: re.Match[str]) -> str:
        target = link["target"]
        if target.startswith(_EXTERNAL):
            return link[0]
        resolved = (source.parent / target).resolve()
        anchor = link["anchor"] or ""
        if resolved.is_relative_to(docs):
            page_path = resolved.relative_to(docs)
            if page_path.parts[0] == locale or resolved.suffix != ".md":
                return link[0]
            return f"{link['head']}{site_page(config, page_path)}{anchor})"
        if not resolved.is_relative_to(repository):
            return link[0]
        path = PurePosixPath(*resolved.relative_to(repository).parts)
        return f"{link['head']}{BLOB}/{path}{anchor})"

    return _LINK.sub(rewrite, markdown)


def site_page(config: MkDocsConfig, page_path: Path) -> str:
    """The address on the site of a page of documentation/.

    Args:
        config: The site configuration.
        page_path: E.g. `fr/start/01-first-audit.md`.

    Returns:
        E.g. `https://…/fr/start/01-first-audit/`; the default language at the root.
    """
    locale, *parts = page_path.parts
    prefix = () if locale == DEFAULT_LOCALE else (locale,)
    *folders, name = parts
    tail = () if name == INDEX else (name.removesuffix(".md"),)
    path = "/".join((*prefix, *folders, *tail))
    return f"{config.site_url or '/'}{path}/" if path else config.site_url or "/"
