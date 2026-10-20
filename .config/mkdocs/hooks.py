"""MkDocs hooks: GitHub's heading anchors, and links leaving a language kept working.

The pages are written for GitHub first: their anchors keep accents (`#étape-1`), each
page links its twin in the other language (`../../fr/…`), which a language's build does
not hold, and some links point at files outside documentation/ (the READMEs, the CI).
Where a link leads is decided by `src/media_hygiene/docs/links.py`, which the docs
inside the image use too: loaded by its path, the package is not installed here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import re
    from pathlib import PurePosixPath
    from types import ModuleType

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page

_SHARED: Final = (
    Path(__file__).resolve().parents[2] / "src" / "media_hygiene" / "docs" / "links.py"
)


def _load_links() -> ModuleType:
    """Load the module shared with the docs inside the image, by its path.

    Returns:
        `media_hygiene.docs.links`.
    """
    spec = importlib.util.spec_from_file_location("media_hygiene_doc_links", _SHARED)
    if spec is None or spec.loader is None:  # pragma: no cover - the file is tracked
        raise ImportError(_SHARED)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look their module up
    spec.loader.exec_module(module)
    return module


links = _load_links()


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    """Slug the headings like GitHub: lower case, accents kept.

    Args:
        config: The site configuration.

    Returns:
        The configuration, the `toc` extension set up.
    """
    config.mdx_configs.setdefault("toc", {})["slugify"] = links.slugifier()
    return config


def on_page_markdown(
    markdown: str, *, page: Page, config: MkDocsConfig, **_: object
) -> str:
    """Point the links to another language, or outside documentation/, at their page.

    Args:
        markdown: The page source.
        page: The page.
        config: The site configuration.
        **_: The other arguments of the event (the site files).

    Returns:
        The source, those links rewritten.
    """
    docs = Path(config.docs_dir).resolve()
    source = Path(page.file.abs_src_path or docs).resolve()
    locale = source.relative_to(docs).parts[0]
    where = links.LinkSource(docs, source)

    def rewrite(link: re.Match[str]) -> str:
        target = links.resolve(where, link["target"])
        anchor = link["anchor"] or ""
        if target.kind is links.LinkKind.PAGE and target.path.parts[0] != locale:
            return f"{link['head']}{site_page(config, target.path)}{anchor})"
        if target.kind is links.LinkKind.REPOSITORY:
            return f"{link['head']}{links.blob_url(target.path)}{anchor})"
        return link[0]

    return links.MARKDOWN_LINK.sub(rewrite, markdown)


def site_page(config: MkDocsConfig, page_path: PurePosixPath) -> str:
    """The address on the site of a page of documentation/.

    Args:
        config: The site configuration.
        page_path: E.g. `fr/start/01-first-audit.md`.

    Returns:
        E.g. `https://…/fr/start/01-first-audit/`; the default language at the root.
    """
    locale, parts = links.page_parts(page_path)
    prefix = () if locale == links.DEFAULT_LOCALE else (locale,)
    path = "/".join((*prefix, *parts))
    return f"{config.site_url or '/'}{path}/" if path else config.site_url or "/"


def on_page_context(
    context: dict[str, object], *, page: Page, **_: object
) -> dict[str, object]:
    """Title the home page like the others: Material gives it the site name alone.

    Args:
        context: The template context.
        page: The page.
        **_: The other arguments of the event (the configuration, the navigation).

    Returns:
        The context, unchanged.
    """
    if page.is_homepage and page.title and not page.meta.get("title"):
        page.meta["title"] = page.title
    return context
