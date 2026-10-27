"""A section renamed since a default `config.toml` wrote it still loads (0375)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.loader import load_settings, renamed_sections

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_a_backup_section_is_read_as_push(locations: Locations) -> None:
    """`[backup]`, written before `mh backup` became `mh push`, sets `[push]`."""
    locations.config_file.write_text("[backup]\nkeep_removed_days = 7\n", "utf-8")
    assert load_settings(locations).settings.push.keep_removed_days == 7


def test_push_wins_when_both_are_written() -> None:
    """Both sections: `[push]` is kept, `[backup]` left for the error to name."""
    layer = renamed_sections({"backup": {"a": 1}, "push": {"a": 2}})
    assert layer == {"backup": {"a": 1}, "push": {"a": 2}}
