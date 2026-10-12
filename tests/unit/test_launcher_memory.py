"""What `mh` remembers beside the folders: the language of the run, its time zone."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_memory import locale_option, remembered
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_COMMANDS = LauncherCommands(names=("audit",), writers=(), pages=(), data=(), port=8088)
_FRENCH = '-e "MEDIA_HYGIENE_GENERAL__LOCALE=fr"'


def test_a_locale_given_to_launcher_is_written_into_the_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--locale fr launcher`: every `mh` run speaks French."""
    monkeypatch.delenv("MEDIA_HYGIENE_GENERAL__LOCALE", raising=False)
    runtime = make_runtime(make_locations(tmp_path), {"general": {"locale": "fr"}})
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    assert f"        {_FRENCH} `" in text


def test_the_default_locale_adds_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No `--locale`: the script holds no language at all."""
    monkeypatch.delenv("MEDIA_HYGIENE_GENERAL__LOCALE", raising=False)
    runtime = make_runtime(make_locations(tmp_path))
    text = render_script(launcher_script(runtime, Shell.BASH, _COMMANDS))
    assert "LOCALE" not in text


def test_a_locale_of_config_toml_is_left_to_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config.toml is read by every `mh` run: a later edit of it still wins."""
    monkeypatch.delenv("MEDIA_HYGIENE_GENERAL__LOCALE", raising=False)
    locations = make_locations(tmp_path)
    locations.config_file.write_text('[general]\nlocale = "fr"\n', encoding="utf-8")
    assert not locale_option(make_runtime(locations))


def test_a_locale_of_the_environment_is_carried_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`-e MEDIA_HYGIENE_GENERAL__LOCALE=fr launcher`: kept, not repeated."""
    monkeypatch.setenv("MEDIA_HYGIENE_GENERAL__LOCALE", "fr")
    runtime = make_runtime(make_locations(tmp_path))
    text = render_script(launcher_script(runtime, Shell.BASH, _COMMANDS))
    assert text.count("MEDIA_HYGIENE_GENERAL__LOCALE=fr") == 1


def test_remembered_names_the_folders_the_language_and_the_zone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One line: how many folders, which language, which time zone."""
    monkeypatch.setenv("TZ", "Europe/Brussels")
    runtime = make_runtime(make_locations(tmp_path), {"general": {"locale": "fr"}})
    script = launcher_script(runtime, Shell.BASH, _COMMANDS)
    line = remembered(runtime, script)
    assert "language fr" in line
    assert "time zone Europe/Brussels" in line
    assert "0 folders" in line
