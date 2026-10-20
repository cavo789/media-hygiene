"""Render documentation/ for the tool to serve: at build time, never at run time.

`python -m media_hygiene.docs.render <documentation> <mkdocs.yml> <out>` writes, per
language, one HTML fragment per page (its body only, `pages/`), the screenshots
(`images/`) and `index.json` (the menu, each page's title, `h2` and `h3`). The Markdown
extensions and the anchors are the public site's (`mkdocs.yml`, `links.slugifier`).
Needs the `docs` dependency group: the shipped image holds the result, not the renderer.
"""

from __future__ import annotations

import dataclasses
import html
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import markdown

from media_hygiene.docs.links import DEFAULT_LOCALE, LinkSource, slugifier
from media_hygiene.docs.nav import markdown_extensions, nav_sections, read_config
from media_hygiene.docs.pages import (
    IMAGES_DIR,
    INDEX_FILE,
    DocIndex,
    DocPage,
    Heading,
    route_of,
)
from media_hygiene.docs.rewrite import rewrite_html

if TYPE_CHECKING:
    from collections.abc import Mapping

LOCALES: Final = (DEFAULT_LOCALE, "fr")
_TOC: Final = "toc"
_HIGHLIGHT: Final = "pymdownx.highlight"
_INDEXED_LEVELS: Final = (2, 3)
_ARGUMENTS: Final = 3


@dataclass(frozen=True, slots=True)
class RenderJob:
    """What to render, and where."""

    documentation: Path  # documentation/, holding one folder per language
    mkdocs_yml: Path  # its menu and Markdown extensions
    out: Path  # one folder per language is written there


def render_all(job: RenderJob) -> tuple[DocIndex, ...]:
    """Render every language.

    Args:
        job: The sources and the output folder.

    Returns:
        The index of each language, as written.
    """
    config = read_config(job.mkdocs_yml)
    return tuple(_render_locale(job, config, locale) for locale in LOCALES)


def _render_locale(
    job: RenderJob, config: Mapping[str, object], locale: str
) -> DocIndex:
    """Render one language: its fragments, its screenshots, its index.

    Args:
        job: The sources and the output folder.
        config: The site's configuration.
        locale: E.g. `fr`.

    Returns:
        Its index.
    """
    names, settings = markdown_extensions(config)
    settings.setdefault(_TOC, {})
    cast("dict[str, object]", settings[_TOC])["slugify"] = slugifier()
    # The colours of the code are the tool's own: plain `<pre><code>`, no Pygments.
    settings[_HIGHLIGHT] = {"use_pygments": False}
    renderer = markdown.Markdown(extensions=names, extension_configs=settings)
    sources = job.documentation / locale
    target = job.out / locale
    sections = nav_sections(config, locale)
    pages = tuple(
        _render_page(renderer, (sources, target), path)
        for section in sections
        for path in section.pages
    )
    shutil.copytree(sources / IMAGES_DIR, target / IMAGES_DIR, dirs_exist_ok=True)
    index = DocIndex(locale, sections, pages)
    body = json.dumps(dataclasses.asdict(index), ensure_ascii=False, indent=1)
    (target / INDEX_FILE).write_text(body, encoding="utf-8")
    return index


def _render_page(
    renderer: markdown.Markdown, folders: tuple[Path, Path], path: str
) -> DocPage:
    """Render one page into its fragment.

    Args:
        renderer: The Markdown renderer, the site's extensions loaded.
        folders: The language's sources, and its output folder.
        path: The page, e.g. `commands/audit.md`.

    Returns:
        The page, as the index lists it.
    """
    sources, target = folders
    page_file = sources / path
    renderer.reset()
    body = renderer.convert(page_file.read_text(encoding="utf-8"))
    where = LinkSource(sources.parent.resolve(), page_file.resolve())
    tokens = cast("list[dict[str, object]]", renderer.toc_tokens)
    title = html.unescape(str(tokens[0]["name"])) if tokens else path
    page = DocPage(path, title, route_of(sources.name, path), _headings(tokens))
    fragment = target / page.fragment
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(rewrite_html(body, where), encoding="utf-8")
    return page


def _headings(tokens: list[dict[str, object]]) -> tuple[Heading, ...]:
    """The `h2` and `h3` of a page, in its order.

    Args:
        tokens: The table of contents of the `toc` extension, nested.

    Returns:
        The headings.
    """
    found: list[Heading] = []
    for token in tokens:
        level = cast("int", token["level"])
        if level in _INDEXED_LEVELS:
            name = html.unescape(str(token["name"]))
            found.append(Heading(level, str(token["id"]), name))
        found.extend(_headings(cast("list[dict[str, object]]", token["children"])))
    return tuple(found)


def main(arguments: list[str]) -> int:
    """Render documentation/ from the command line.

    Args:
        arguments: `<documentation> <mkdocs.yml> <out>`.

    Returns:
        0, or 2 for a wrong call.
    """
    if len(arguments) != _ARGUMENTS:
        sys.stderr.write(__doc__ or "")
        return 2
    documentation, mkdocs_yml, out = (Path(argument) for argument in arguments)
    indexes = render_all(RenderJob(documentation, mkdocs_yml, out))
    count = sum(len(index.pages) for index in indexes)
    sys.stdout.write(f"{count} pages rendered into {out}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - run by the Dockerfile
    sys.exit(main(sys.argv[1:]))
