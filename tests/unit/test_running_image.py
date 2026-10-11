"""Suggested commands name the image that runs, not always the published one."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.docker_run import IMAGE_VARIABLE, PUBLISHED_IMAGE, Shell
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.next_command import CHANGING, NextVerb, next_command
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest

    from media_hygiene.services.runtime import Runtime

ROOT: Final = Path(__file__).resolve().parents[2]
_LOCAL = "media-hygiene"
_COMMANDS = LauncherCommands(names=("audit",), writers=(), pages=(), data=(), port=8088)
_STAGE = re.compile(r"^FROM .* AS (?P<name>\w+)$", re.MULTILINE)


def _runtime() -> Runtime:
    r"""An audit of `C:\Photos`, the only folder mounted.

    Returns:
        The runtime.
    """
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    photos = Path("/data/c/Photos")
    return replace(
        make_runtime(locations), mounts=MountTable(frozenset({photos}), (), ())
    )


def test_a_local_build_names_itself_and_does_not_carry_the_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`MEDIA_HYGIENE_IMAGE=media-hygiene`: `media-hygiene clean`, no `-e` for it."""
    monkeypatch.setenv(IMAGE_VARIABLE, _LOCAL)
    command = next_command(_runtime(), NextVerb("clean", CHANGING)).command
    assert command.splitlines()[-1] == f"  {_LOCAL} clean"
    assert IMAGE_VARIABLE not in command
    assert PUBLISHED_IMAGE not in command


def test_without_the_variable_the_published_image_is_suggested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset or empty: `cavo789/media-hygiene <verb>`."""
    monkeypatch.setenv(IMAGE_VARIABLE, "")
    command = next_command(_runtime(), NextVerb("clean", CHANGING)).command
    assert command.splitlines()[-1] == f"  {PUBLISHED_IMAGE} clean"
    monkeypatch.delenv(IMAGE_VARIABLE)
    command = next_command(_runtime(), NextVerb("audit")).command
    assert command.splitlines()[-1] == f"  {PUBLISHED_IMAGE} audit"


def test_the_launcher_runs_the_image_that_wrote_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`mh` runs the local build, without passing the variable on."""
    monkeypatch.setenv(IMAGE_VARIABLE, _LOCAL)
    text = render_script(launcher_script(_runtime(), Shell.BASH, _COMMANDS))
    assert f'{_LOCAL} "$@"' in text
    assert PUBLISHED_IMAGE not in text
    assert IMAGE_VARIABLE not in text


def test_only_the_local_target_sets_the_variable() -> None:
    """CI publishes the last stage (no `--target`): it never names the local image."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    stages = [match["name"] for match in _STAGE.finditer(dockerfile)]
    assert stages[-1] == "published"
    local = dockerfile.split("AS local", 1)[1].split("AS published", 1)
    assert f"ENV {IMAGE_VARIABLE}={_LOCAL}\n" in local[0]
    assert IMAGE_VARIABLE not in local[1]
