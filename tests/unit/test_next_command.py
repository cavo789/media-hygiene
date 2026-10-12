"""The full `docker run` of the next command, rebuilt from the mount table."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.cli.next_steps import carried
from media_hygiene.constants import Locale
from media_hygiene.paths.docker_run import PUBLISHED_IMAGE
from media_hygiene.paths.host_folders import HostFolder
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.next_command import CHANGING, NextVerb, next_command
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    import typer

    from media_hygiene.services.runtime import Runtime

_PHOTOS = Path("/data/c/Photos")
_HOME_PHOTOS = Path("/data/home/me/Photos")
_VOLUME = HostFolder(
    "dev:8:1", ("/", "var", "lib", "docker", "volumes", "media-hygiene-cache", "_data")
)


def _runtime(table: MountTable) -> Runtime:
    """A runtime with the container's usual mount points and `table`.

    Args:
        table: The mount table of the run.

    Returns:
        The runtime.
    """
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    return replace(make_runtime(locations), mounts=table)


def _windows_run() -> Runtime:
    r"""An audit of `C:\Photos`, with reports and the cache volume.

    Returns:
        The runtime.
    """
    return _runtime(
        MountTable(
            frozenset({_PHOTOS, Path("/reports"), Path("/cache")}),
            ((_PHOTOS, "C:\\Photos"), (Path("/reports"), "C:\\Users\\me\\reports")),
            ((Path("/cache"), _VOLUME),),
        )
    )


def test_clean_after_an_audit_drops_ro_and_adds_the_tool_folders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PowerShell, read-write photos, same reports and cache, journal and quarantine."""
    monkeypatch.setenv("TZ", "Europe/Brussels")
    monkeypatch.setenv("MEDIA_HYGIENE_GENERAL__LOCALE", "fr")
    monkeypatch.setenv("MEDIA_HYGIENE_REPORTS_DIR", "/elsewhere")
    built = next_command(_windows_run(), NextVerb("clean", CHANGING))
    lines = built.command.splitlines()
    assert lines[0] == (
        'mkdir -Force "$HOME\\media-hygiene\\journal", '
        '"$HOME\\media-hygiene\\quarantine"'
    )
    assert lines[1] == "docker run --rm -it `"
    assert '  -v "C:\\Photos:/data/c/Photos" `' in lines
    assert '  -v "C:\\Users\\me\\reports:/reports" `' in lines
    assert '  -v "media-hygiene-cache:/cache" `' in lines
    assert '  -v "$HOME\\media-hygiene\\journal:/journal" `' in lines
    assert '  -e "TZ=Europe/Brussels" `' in lines
    assert '  -e "MEDIA_HYGIENE_GENERAL__LOCALE=fr" `' in lines
    assert "REPORTS_DIR" not in built.command
    assert lines[-1] == f"  {PUBLISHED_IMAGE} clean"
    assert built.added == (MountKind.JOURNAL, MountKind.QUARANTINE)
    assert "/journal, /quarantine" in built.note()


def test_a_page_keeps_the_photos_read_only_and_publishes_its_port() -> None:
    """Bash for Linux folders: backslashes, --user, :ro kept, -p, nothing added."""
    runtime = _runtime(
        MountTable(
            frozenset({_HOME_PHOTOS}),
            (),
            ((_HOME_PHOTOS, HostFolder("dev:8:1", ("/", "home", "me", "Photos"))),),
        )
    )
    built = next_command(runtime, NextVerb("review", port=8088))
    lines = built.command.splitlines()
    assert lines[0] == "docker run --rm -it \\"
    assert '  --user "$(id -u):$(id -g)" \\' in lines
    assert '  -v "/home/me/Photos:/data/home/me/Photos:ro" \\' in lines
    assert "  -p 127.0.0.1:8088:8088 \\" in lines
    assert not built.added
    assert not built.note()


def test_unknown_host_folders_follow_the_naming_convention() -> None:
    r"""A data root the mount table says nothing about: `/data/c/x` is `C:\x`."""
    runtime = _runtime(MountTable(frozenset({_PHOTOS}), (), ()))
    built = next_command(runtime, NextVerb("undo 1", CHANGING))
    assert '-v "C:\\Photos:/data/c/Photos"' in built.command
    assert "$HOME\\media-hygiene\\quarantine" in built.command


def test_the_next_command_keeps_the_global_and_folder_options() -> None:
    """--locale and --prefer come along; a command without folders: --locale only."""
    runtime = replace(_windows_run(), cli_layer={"general": {"locale": Locale.FR}})
    ctx = cast("typer.Context", SimpleNamespace(params={"prefer": ["C:\\Best"]}))
    assert carried(runtime, "clean", ctx) == '--locale fr clean --prefer "C:\\Best"'
    assert carried(runtime, "undo 1") == "--locale fr undo 1"


def test_under_the_launcher_the_next_command_is_mh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `mh` function mounts everything: the step is `mh <verb>`, nothing added."""
    monkeypatch.setenv("MEDIA_HYGIENE_LAUNCHER", "1")
    built = next_command(_windows_run(), NextVerb("clean", CHANGING))
    assert built.command == "mh clean"
    assert not built.note()
