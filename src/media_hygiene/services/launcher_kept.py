r"""The `launcher` run that wrote `mh`, kept in it to be run again (0176, 0177).

`mh folders add "D:\X"` and `mh update` write the script anew: `mh` runs `launcher`
through the image with the same options and its photo folders, one more or one less.
So the script keeps, as words already quoted for its shell: the `docker run` options
of that run (its settings, a tool folder mounted by hand, a photo folder mounted with
`-v` elsewhere than the usual place), the global `--locale`, `launcher --shell …` and
its `--quarantine`, then the photo folders, apart, each one given back as `--photos`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.paths.docker_run import PUBLISHED_IMAGE, Shell, running_image
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.launcher_folders import checked_folders, container_point
from media_hygiene.services.launcher_memory import LOCALE_VARIABLE
from media_hygiene.services.next_command import TOOL_KINDS

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.launcher import LauncherScript

# The cache is a named volume (README), the other tool folders are in the home.
CACHE_VOLUME: Final = "media-hygiene-cache"
_LAUNCHER: Final = "launcher"
_ENVIRONMENT: Final = '-e "'
_ESCAPES: Final = {
    Shell.POWERSHELL: {"`": "``", "$": "`$", '"': '`"'},
    Shell.BASH: {"\\": "\\\\", '"': '\\"', "$": "\\$", "`": "\\`"},
}


@dataclass(frozen=True, slots=True)
class KeptRun:
    """The `launcher` run of the script, each word quoted for its shell."""

    docker: tuple[str, ...]  # `docker run --rm` options, before the image
    launcher: tuple[str, ...]  # after the image: `--locale`, `launcher`, its options
    photos: tuple[str, ...]  # the folders given back with `--photos`
    shown: tuple[str, ...]  # every photo folder that is a path, as `mh folders` lists
    quarantine: str  # the host folder of the quarantine, inside double quotes
    image: str
    pullable: bool  # the published image; a local build has nothing to pull

    @property
    def fixed(self) -> int:
        """Count the photo folders mounted with `-v`: kept, never removed by `mh`.

        Returns:
            How many listed folders are not given back with `--photos`.
        """
        return len(self.shown) - len(self.photos)


def kept_run(script: LauncherScript) -> KeptRun:
    """Gather what running `launcher` again needs, to write this very script.

    Args:
        script: The script.

    Returns:
        The kept run.
    """
    shell = script.shell
    docker, locale = _settings(script)
    photos = [
        volume.host
        for volume in script.data
        if _point(script, volume.host) == volume.point
    ]
    for volume in script.data:
        if volume.host not in photos:
            docker.extend(("-v", f"{volume.host}:{volume.point.as_posix()}:ro"))
    launcher = [*locale, _LAUNCHER, "--shell", shell.value]
    for kind, volume in zip(TOOL_KINDS, script.tools, strict=True):
        if volume.host == _default(shell, kind):
            continue
        if kind is MountKind.QUARANTINE and _point(script, volume.host) is not None:
            launcher.extend(("--quarantine", volume.host))
        else:
            docker.extend(("-v", f"{volume.host}:{volume.point.as_posix()}"))
    quarantine = script.tools[TOOL_KINDS.index(MountKind.QUARANTINE)].host
    image = running_image()
    return KeptRun(
        docker=tuple(quoted(word, shell) for word in docker),
        launcher=tuple(quoted(word, shell) for word in launcher),
        photos=tuple(quoted(folder, shell) for folder in photos),
        shown=tuple(quoted(folder, shell) for folder in checked_folders(script)),
        quarantine=(
            f'"{quarantine}"'
            if quarantine == _default(shell, MountKind.QUARANTINE)
            else quoted(quarantine, shell)
        ),
        image=image,
        pullable=image == PUBLISHED_IMAGE,
    )


def quoted(word: str, shell: Shell) -> str:
    """Quote a word so that the shell reads it back unchanged, `$` included.

    Args:
        word: Any word: a folder, an option.
        shell: The shell reading it.

    Returns:
        The word inside double quotes, its special characters escaped.
    """
    escapes = _ESCAPES[shell]
    return '"' + "".join(escapes.get(character, character) for character in word) + '"'


def _settings(script: LauncherScript) -> tuple[list[str], list[str]]:
    """Split the `-e` options of the script: the language becomes `--locale`.

    Args:
        script: The script.

    Returns:
        The `-e NAME=value` words, then `--locale <language>` or nothing.
    """
    docker: list[str] = []
    locale: list[str] = []
    for option in script.environment:
        setting = option.removeprefix(_ENVIRONMENT).removesuffix('"')
        name, _equal, value = setting.partition("=")
        if name == LOCALE_VARIABLE:
            locale = ["--locale", value]
        else:
            docker.extend(("-e", setting))
    return docker, locale


def _point(script: LauncherScript, host: str) -> Path | None:
    """Where `--photos` (or `--quarantine`) would mount a host folder.

    Args:
        script: The script, for its data mount point.
        host: A host folder, or a named volume.

    Returns:
        Its mount point under `/data`; None for what these options refuse (a named
        volume, a network folder): it stays a `-v`.
    """
    try:
        return container_point(script.data_dir, host)
    except MountError:
        return None


def _default(shell: Shell, kind: MountKind) -> str:
    """The host folder `launcher` gives a tool folder no option names.

    Args:
        shell: The shell of the script.
        kind: The tool folder.

    Returns:
        The cache volume, or the folder of the user's home.
    """
    return CACHE_VOLUME if kind is MountKind.CACHE else shell.home_folder(kind.value)
