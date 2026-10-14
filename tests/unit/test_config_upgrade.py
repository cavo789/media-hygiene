"""`config --upgrade`: the settings of a newer version added, the user's own kept."""

from __future__ import annotations

import re
import tomllib
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.config.loader import default_config
from media_hygiene.config.settings import Settings
from media_hygiene.config.upgrade import plan_upgrade, written_by
from media_hygiene.constants import Locale
from media_hygiene.errors import MountError
from media_hygiene.services import config_upgrade as service
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

VERSION: Final = "9.9.9"
MINE: Final = "propose_aside_below = 0.5  # my own value\n"
RULE: Final = '[[classify.rules]]\nname = "Mine"\nmatch = "folder"\ncategory = "X"\n'


def older(template: str) -> str:
    """An older file: no mark, no [tags], no review.brightness_gap, mine changed.

    Args:
        template: The file of this version.

    Returns:
        The older file.
    """
    text = re.sub(r"# media-hygiene-config: .*\n", "", template)
    text = re.sub(r"\n\[tags\]\n.*?(?=\n\[people\])", "\n", text, flags=re.DOTALL)
    text = re.sub(r"\n(?:# .*\n)*brightness_gap = .*\n", "\n", text, count=1)
    text = re.sub(r"propose_aside_below = .*\n", MINE, text)
    return text.replace("[general]\n", "[general]\n# a comment of mine\n", 1)


def keys(document: dict[str, object], prefix: str = "") -> set[str]:
    """Every dotted key of a parsed file, arrays of tables as one key."""
    found: set[str] = set()
    for name, value in document.items():
        if isinstance(value, dict):
            found |= keys(value, f"{prefix}{name}.")
        else:
            found.add(f"{prefix}{name}")
    return found


def test_missing_keys_and_tables_added_the_rest_kept() -> None:
    """Everything of the template is there; the user's lines are kept byte for byte."""
    template = default_config(Locale.EN)
    text = older(template).replace("[general]\n", "[general]\nunknown_but_kept = 1\n")
    upgrade = plan_upgrade(text, template, VERSION)
    assert "tags" in upgrade.added
    assert "review.brightness_gap" in upgrade.added
    assert upgrade.written_by is None
    assert keys(tomllib.loads(template)) <= keys(tomllib.loads(upgrade.text))
    for line in (MINE, "# a comment of mine\n", "unknown_but_kept = 1\n"):
        assert line in upgrade.text
    assert upgrade.text.startswith(f"# media-hygiene-config: {VERSION}\n")
    assert written_by(upgrade.text) == VERSION


def test_the_rules_of_the_user_are_left_alone() -> None:
    """Arrays of tables are the user's own: never added, never touched."""
    template = default_config(Locale.EN)
    text = re.sub(r"\n\[\[classify\.rules\]\]\n.*", "\n", template, flags=re.DOTALL)
    upgrade = plan_upgrade(text + RULE, template, VERSION)
    rules = tomllib.loads(upgrade.text)["classify"]["rules"]
    assert [rule["name"] for rule in rules] == ["Mine"]


def test_an_up_to_date_file_is_not_changed() -> None:
    """Nothing missing: the same text, the old mark kept."""
    template = default_config(Locale.FR)
    upgrade = plan_upgrade(template, template, VERSION)
    assert not upgrade.added
    assert upgrade.text == template


def test_written_in_the_language_of_the_file_with_the_same_settings(
    locations: Locations,
) -> None:
    """A French file gets French comments; the effective settings do not move."""
    template = default_config(Locale.FR)
    text = older(template)
    config_file = locations.config_file
    config_file.write_text(text, encoding="utf-8")
    runtime = make_runtime(locations)
    upgrade = service.config_upgrade(runtime, dry_run=False)
    written = config_file.read_text(encoding="utf-8")
    assert written == upgrade.text
    assert "[tags]" in written
    assert "Langue" in written or "langue" in written
    before = Settings.model_validate(tomllib.loads(text))
    after = Settings.model_validate(tomllib.loads(written))
    assert before == after
    assert not service.pending_upgrade(written).added
    assert not list(locations.config_dir.glob(".*.tmp"))


def test_dry_run_and_up_to_date_write_nothing(locations: Locations) -> None:
    """`--dry-run` lists; an up-to-date file keeps its modification time."""
    config_file = locations.config_file
    config_file.write_text(older(default_config(Locale.EN)), encoding="utf-8")
    before = config_file.stat().st_mtime_ns
    runtime = make_runtime(locations)
    assert service.config_upgrade(runtime, dry_run=True).added
    assert config_file.stat().st_mtime_ns == before
    service.config_upgrade(runtime, dry_run=False)
    after = config_file.stat().st_mtime_ns
    assert not service.config_upgrade(runtime, dry_run=False).added
    assert config_file.stat().st_mtime_ns == after


def test_refused_when_read_only_or_missing(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read-only /config, or no file yet: a clear refusal, nothing written."""
    runtime = make_runtime(locations)
    with pytest.raises(MountError, match=r"no config\.toml"):
        service.config_upgrade(runtime, dry_run=True)
    locations.config_file.write_text(older(default_config(Locale.EN)), "utf-8")
    monkeypatch.setattr(service, "is_read_only", lambda _path: True)
    with pytest.raises(MountError, match="read-only"):
        service.config_upgrade(runtime, dry_run=False)
    assert service.config_upgrade(runtime, dry_run=True).added
