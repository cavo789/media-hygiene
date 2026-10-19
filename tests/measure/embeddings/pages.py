"""The pages to judge: per search, each model's best pictures side by side; the pairs.

Three self-contained HTML files and a folder of thumbnails. Each picture has a box
"relevant" (a pair: "same photo"); the page keeps the boxes in the browser while it is
open and downloads them as one JSON file, to send back (TODO 0221).
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Final

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import UnidentifiedImageError

from .embedders import STUB
from .models import SPECS
from .ranking import SEARCH
from .runs import open_upright

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .ranking import Pair, Ranked

TEMPLATES: Final = Path(__file__).parent / "templates"
THUMBS: Final = "thumbs"
INDEX_PAGE: Final = "index.html"
QUERIES_PAGE: Final = "queries.html"
PAIRS_PAGE: Final = "pairs.html"
_THUMB_SIDE: Final = 320
_THUMB_QUALITY: Final = 80
_TITLES: Final = {
    **{name: spec.title for name, spec in SPECS.items()},
    STUB: "Stub (random vectors, tests only)",
    SEARCH: "Today's search (words of the index)",
}


def thumb_name(photo: int) -> str:
    """The thumbnail of a photo, relative to the pages.

    Args:
        photo: Its number in the sample.

    Returns:
        The relative path.
    """
    return f"{THUMBS}/{photo:06d}.jpg"


def _write_thumbs(ranked: Ranked, out: Path) -> None:
    """Write a thumbnail of every photo a page shows.

    Args:
        ranked: What the pages show.
        out: The pages' folder.
    """
    (out / THUMBS).mkdir(parents=True, exist_ok=True)
    for photo in sorted(_shown(ranked)):
        target = out / thumb_name(photo)
        try:
            picture = open_upright(ranked.bench.photos[photo]).convert("RGB")
        except OSError, UnidentifiedImageError, ValueError:
            continue
        picture.thumbnail((_THUMB_SIDE, _THUMB_SIDE))
        picture.save(target, quality=_THUMB_QUALITY)


def _shown(ranked: Ranked) -> set[int]:
    """Every photo number a page shows.

    Args:
        ranked: What the pages show.

    Returns:
        The numbers.
    """
    shown = {
        photo for columns in ranked.answers for row in columns.values() for photo in row
    }
    for pairs in ranked.pairs.values():
        shown.update(photo for pair in pairs for photo in (pair.first, pair.second))
    return shown


def _picture(ranked: Ranked, photo: int) -> dict[str, object]:
    """What a page needs of a photo.

    Args:
        ranked: What the pages show.
        photo: Its number.

    Returns:
        Its number, thumbnail and path.
    """
    return {
        "n": photo,
        "thumb": thumb_name(photo),
        "path": str(ranked.bench.photos[photo]),
    }


def _queries(ranked: Ranked) -> list[dict[str, object]]:
    """The searches and, per column, the pictures in order.

    Args:
        ranked: What the pages show.

    Returns:
        One entry per search.
    """
    return [
        {
            "query": query,
            "columns": [
                {
                    "name": name,
                    "title": _TITLES.get(name, name),
                    "pictures": [_picture(ranked, photo) for photo in row],
                }
                for name, row in columns.items()
            ],
        }
        for query, columns in zip(ranked.bench.queries, ranked.answers, strict=True)
    ]


def _pairs(ranked: Ranked) -> list[dict[str, object]]:
    """Each model's closest pairs.

    Args:
        ranked: What the pages show.

    Returns:
        One entry per model.
    """

    def entries(pairs: Iterable[Pair]) -> list[dict[str, object]]:
        return [
            {
                "first": _picture(ranked, pair.first),
                "second": _picture(ranked, pair.second),
                "similarity": round(pair.similarity, 4),
            }
            for pair in pairs
        ]

    return [
        {"name": name, "title": _TITLES.get(name, name), "pairs": entries(pairs)}
        for name, pairs in ranked.pairs.items()
    ]


def _models(ranked: Ranked) -> list[dict[str, object]]:
    """Each model's costs and licence, for the summary.

    Args:
        ranked: What the pages show.

    Returns:
        One entry per model.
    """
    return [
        {
            "name": run.model,
            "title": _TITLES.get(run.model, run.model),
            "licence": SPECS[run.model].licence if run.model in SPECS else "",
            "reads_text": run.texts is not None,
            **asdict(run.timing),
        }
        for run in ranked.bench.runs
    ]


def write_pages(ranked: Ranked, out: Path) -> Path:
    """Write the three pages and their thumbnails.

    Args:
        ranked: What the pages show.
        out: The folder (created when missing).

    Returns:
        The summary page.
    """
    out.mkdir(parents=True, exist_ok=True)
    _write_thumbs(ranked, out)
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(),
        keep_trailing_newline=True,
    )
    models = _models(ranked)
    bench = ranked.bench
    facts = {
        "photos": len(bench.photos),
        "queries": len(bench.queries),
        "searched": bench.search is not None,
    }
    pages = {
        INDEX_PAGE: {"models": models, "facts": facts},
        QUERIES_PAGE: {"queries": _queries(ranked), "facts": facts},
        PAIRS_PAGE: {"models": _pairs(ranked), "facts": facts},
    }
    for name, values in pages.items():
        page = environment.get_template(name).render(**values)
        (out / name).write_text(page, encoding="utf-8")
    return out / INDEX_PAGE
