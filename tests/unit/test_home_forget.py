"""The home page's *Forget every face and every name* states what it deletes (0795)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.home_forget import with_forget_names
from media_hygiene.cli.menu_catalog_settings import FORGET_NAMES
from media_hygiene.cli.menu_steps import build_menu
from media_hygiene.services.status import read_status
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.cli.menu_steps import MenuStep

_PEOPLE = """
[[people.person]]
name = "Zoé"
faces = []

[[people.person]]
name = "Albert"
faces = []
"""


def _line(tmp_path: Path, text: str | None) -> MenuStep:
    """The step's line once the file holding `text` is read."""
    runtime = make_runtime(make_locations(tmp_path))
    config = runtime.locations.config_file
    if text is not None:
        config.write_text(text, encoding="utf-8")
    menu = with_forget_names(build_menu(read_status(runtime), 30), config)
    return next(line for line in menu.steps if line.step.name == FORGET_NAMES)


def test_the_confirmation_counts_and_lists_every_name(tmp_path: Path) -> None:
    """Its title states the count, its text every name, sorted."""
    line = _line(tmp_path, _PEOPLE)
    assert line.step.confirm is not None
    title, text = line.step.confirm
    assert "2 names" in title
    assert "Albert, Zoé" in text
    assert not line.reason


def test_without_a_name_it_is_not_offered(tmp_path: Path) -> None:
    """No name, no face ignored: a reason, never an empty confirmation."""
    assert _line(tmp_path, "").reason
    assert _line(tmp_path, None).reason


def test_a_broken_file_offers_nothing(tmp_path: Path) -> None:
    """A file that is not TOML: a reason, no traceback."""
    assert _line(tmp_path, "[[people.person]\n").reason
