"""`classify` names the rules of several folder levels in one warning line."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.convention_notes import note_convention
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path


def _rule(index: int) -> str:
    return (
        f'[[classify.rules]]\nname = "Trip {index}"\nmatch = "path"\n'
        f"pattern = 'trip{index}'\ncategory = \"Holidays/Trip {index}\"\n\n"
    )


def test_many_deep_rules_make_one_warning(tmp_path: Path) -> None:
    """Five such rules: one line, three names, the count."""
    locations = make_locations(tmp_path)
    locations.config_file.write_text(
        "".join(_rule(index) for index in range(5)), encoding="utf-8"
    )
    runtime = make_runtime(locations)

    note_convention(runtime)

    shown = " ".join(output_of(runtime).split())
    assert shown.count("several folder levels") == 1
    assert "5 rules" in shown
    assert "'Trip 0', 'Trip 1', 'Trip 2'…" in shown
    assert "Trip 3" not in shown
