"""The intruders page's live sentence in Chromium, for the four cases, EN + FR (0741).

The sentence is computed by the page's script from `state.files` (0510): only a browser
runs it. Heavy (Playwright image): CI only, where `MEDIA_HYGIENE_E2E_BROWSER` is set.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.review_file import review_page
from tests.support.pages_browser import (
    BROWSER_ONLY,
    BrowserRun,
    build_browser,
    run_browser,
)

pytestmark = list(BROWSER_ONLY)
_WALK: Final = Path(__file__).parents[1] / "support" / "intruders_walk.py"
_Y2010: Final = "C:\\Photos\\2010"
_Y2011: Final = "C:\\Photos\\2011"
_KB: Final = 1024


def _file(extension: str, folder: str) -> dict[str, object]:
    """One intruder file of 1 KB."""
    return {"extension": extension, "folder": folder, "bytes": _KB}


def _row(key: str, count: int) -> dict[str, object]:
    """A tally row (its figures are redrawn by the page)."""
    return {"key": key, "count": count, "size": f"{count} KB", "hint": ""}


_STATE: Final = {
    "decisions_place": "decisions.json",
    "total": 4,
    "size": "4 KB",
    "extensions": [_row(".ithmb", 3), _row(".zip", 1)],
    "folders": [_row(_Y2010, 3), _row(_Y2011, 1)],
    "files": [
        _file(".ithmb", _Y2010),
        _file(".ithmb", _Y2010),
        _file(".ithmb", _Y2011),
        _file(".zip", _Y2010),
    ],
    "set_aside": [],
}
# (extensions, folders) ticked → (sentence, button), per language; plural and singular.
_CASES: Final = {
    Locale.EN: (
        ((), (), "Tick an extension or a folder.", "Set the files ticked aside"),
        (
            (".ithmb",),
            (),
            "3 .ithmb files (3.0 KB), in every folder.",
            "Set these 3 files aside",
        ),
        (
            (".zip",),
            (),
            "1 .zip file (1.0 KB), in every folder.",
            "Set this 1 file aside",
        ),
        (
            (),
            (_Y2010,),
            f"Every intruder file of {_Y2010} (3 files, 3.0 KB).",
            "Set these 3 files aside",
        ),
        (
            (".ithmb",),
            (_Y2010,),
            f"The .ithmb files of {_Y2010} only (2 files, 2.0 KB).",
            "Set these 2 files aside",
        ),
    ),
    Locale.FR: (
        (
            (),
            (),
            "Cochez une extension ou un dossier.",
            "Mettre de côté les fichiers cochés",
        ),
        (
            (".ithmb",),
            (),
            "3 fichiers .ithmb (3,0 Ko), dans tous les dossiers.",
            "Mettre ces 3 fichiers de côté",
        ),
        (
            (".zip",),
            (),
            "1 fichier .zip (1,0 Ko), dans tous les dossiers.",
            "Mettre ce 1 fichier de côté",
        ),
        (
            (),
            (_Y2010,),
            f"Tous les fichiers intrus de {_Y2010} (3 fichiers, 3,0 Ko).",
            "Mettre ces 3 fichiers de côté",
        ),
        (
            (".ithmb",),
            (_Y2010,),
            f"Les fichiers .ithmb de {_Y2010} seulement (2 fichiers, 2,0 Ko).",
            "Mettre ces 2 fichiers de côté",
        ),
    ),
}


@pytest.mark.parametrize("locale", list(_CASES))
def test_the_sentence_says_what_the_ticks_take(tmp_path: Path, locale: Locale) -> None:
    """Nothing, extensions only, folders only, both: the sentence and the button."""
    install(locale)
    try:
        place = DecisionsPlace(argument="decisions.json", host="decisions.json")
        html = review_page(
            "intruders_review.html.j2", place, ("api/intruders", "api/file")
        )
    finally:
        install(Locale.EN)
    page = tmp_path / "intruders.html"
    page.write_bytes(html)
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "state": _STATE,
                "cases": [
                    {"extensions": e, "folders": f, "sentence": s, "button": b}
                    for e, f, s, b in _CASES[locale]
                ],
            }
        ),
        "utf-8",
    )
    shots = tmp_path / "shots"
    shots.mkdir()
    build_browser()
    run = BrowserRun(
        name=f"media-hygiene-intruders-walk-{locale.value}",
        scripts=(_WALK, page, cases),
        args=("/tmp/intruders.html", "/tmp/cases.json"),  # noqa: S108  # in the container
        network="bridge",  # the script installs playwright first
    )
    assert run_browser(run, shots) == ""
