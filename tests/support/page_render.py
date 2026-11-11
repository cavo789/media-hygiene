"""Render a page served by the tool, every value its template names a placeholder.

Shared by the tests of what every page holds: its bar (`test_page_headers.py`) and its
frame (`test_page_frame.py`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from jinja2 import meta

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.page_header import page_header
from media_hygiene.services.settings_index import Listed, ShownValue
from media_hygiene.services.settings_rows import SettingRow

if TYPE_CHECKING:
    from jinja2 import Environment

# How a page built on the frame (`review/templates/page_frame.html.j2`, 0333) starts.
FRAME_EXTENDS: Final = '{% extends "page_frame.html.j2" %}'
# The package whose templates hold a page; the others are `media_hygiene.review`'s.
_PACKAGES: Final = {
    "search.html.j2": "media_hygiene.search",
    "places.html.j2": "media_hygiene.places",
    "people.html.j2": "media_hygiene.people",
    "person.html.j2": "media_hygiene.person",
    "slideshow.html.j2": "media_hygiene.slideshow",
    "album.html.j2": "media_hygiene.share",
    "album_edit.html.j2": "media_hygiene.share",
}


class _AnyPath(dict[str, str]):
    """A page's `paths`: any route it names."""

    def __missing__(self, key: str) -> str:
        return f"/{key}"


def _names(environment: Environment, template: str, seen: set[str]) -> set[str]:
    """Every value a template and the fragments it includes or extends name."""
    if template in seen:
        return set()
    seen.add(template)
    source = environment.loader.get_source(environment, template)[0]  # type: ignore[union-attr]
    tree = environment.parse(source)
    found = set(meta.find_undeclared_variables(tree))
    for included in meta.find_referenced_templates(tree):
        if included is not None:
            found |= _names(environment, included, seen)
    return found


def render_page(template: str, filler: str = "/x") -> str:
    """A page, every route it names given a placeholder.

    Args:
        template: Its template, a key of `PAGE_STEPS`.
        filler: The value of every name (a hostile one in `test_hostile_names.py`).

    Returns:
        The page, as served.
    """
    package = _PACKAGES.get(template, "media_hygiene.review")
    environment = translated_environment(package, escaped=("html", "j2"))
    values: dict[str, object] = dict.fromkeys(
        _names(environment, template, set()), filler
    )
    values.update(_samples(template, filler))
    values["paths"] = _AnyPath()
    values["header"] = page_header(template)
    return environment.get_template(template).render(**values)


def _samples(template: str, filler: str) -> dict[str, object]:
    """The lists a page loops over, each value the filler (the settings index, 0670)."""
    if template != "settings_index.html.j2":
        return {}
    row = SettingRow(filler, filler, filler, (filler,))
    return {
        "rows": (Listed(row, (ShownValue(filler, filler, default=True),)),),
        "only": (filler,),
    }
