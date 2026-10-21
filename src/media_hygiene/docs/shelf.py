"""Where the rendered docs are: in the image, or rendered from the sources (developers).

The image holds them in `BUILT_DOCS` (the `docs` stage of the Dockerfile). A developer
running the tool from the sources (the `hygiene` helper) sets `MEDIA_HYGIENE_DOCS_DIR`:
the docs are rendered there on first use, and again when a page changed, when the
renderer can be imported (the `docs` dependency group). Without rendered docs, the
links stay on the public site.
"""

from __future__ import annotations

import functools
import logging
import os
from pathlib import Path
from typing import Final

from pydantic import TypeAdapter

from media_hygiene.constants import ENV_PREFIX, Locale
from media_hygiene.docs.pages import INDEX_FILE, DocIndex

DOCS_VARIABLE: Final = f"{ENV_PREFIX}DOCS_DIR"
BUILT_DOCS: Final = Path("/usr/share/media-hygiene/docs")
# The repository, when the tool runs from its sources: documentation/ and mkdocs.yml.
REPOSITORY: Final = Path(__file__).resolve().parents[3]
_LOG: Final = logging.getLogger(__name__)
_INDEX: Final = TypeAdapter(DocIndex)


@functools.cache
def docs_root() -> Path | None:
    """The folder of the rendered docs, read once per run.

    Returns:
        It, holding one folder per language; None when there are none.
    """
    wanted = os.environ.get(DOCS_VARIABLE, "")
    root = Path(wanted) if wanted else BUILT_DOCS
    if wanted:
        _render_from_sources(root, REPOSITORY)
    return root if (root / Locale.EN.value / INDEX_FILE).is_file() else None


@functools.cache
def doc_index(root: Path, locale: Locale) -> DocIndex:
    """The index of a language, read once per run.

    Args:
        root: The folder of the rendered docs.
        locale: The language.

    Returns:
        Its menu and pages.
    """
    return _INDEX.validate_json((root / locale.value / INDEX_FILE).read_bytes())


def _render_from_sources(root: Path, repository: Path) -> None:
    """Render the sources' docs into a folder when they are missing or older.

    Args:
        root: Where to render them.
        repository: The sources: documentation/ and .config/mkdocs/mkdocs.yml.
    """
    documentation = repository / "documentation"
    mkdocs_yml = repository / ".config" / "mkdocs" / "mkdocs.yml"
    if not documentation.is_dir() or not mkdocs_yml.is_file():
        return
    index = root / Locale.EN.value / INDEX_FILE
    newest = max(path.stat().st_mtime for path in documentation.rglob("*"))
    if index.is_file() and index.stat().st_mtime >= max(newest, _mtime(mkdocs_yml)):
        return
    try:
        from media_hygiene.docs.render import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            RenderJob,
            render_all,
        )
    except ImportError:  # the docs group is not installed: the links stay outside
        _LOG.debug("The docs cannot be rendered: the docs group is missing.")
        return
    render_all(RenderJob(documentation, mkdocs_yml, root))


def _mtime(path: Path) -> float:
    """The modification time of a file.

    Args:
        path: The file.

    Returns:
        Its time, in seconds.
    """
    return path.stat().st_mtime
