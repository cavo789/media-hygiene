"""Czkawka's side: the command media-hygiene suggests, and the JSON results it writes.

`czkawka_cli dup -C <file>` (version 12) writes `{"<size>": [[{"path": ...}, ...]]}`:
groups of identical files, by size. In the image, `crosscheck` runs it in place
(`czkawka_run`), on the very paths media-hygiene reads; the command printed for those
who run it themselves reuses media-hygiene's mount points, so its paths are the same.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from media_hygiene.constants import CZKAWKA_FILE_NAME, CZKAWKA_IMAGE, CZKAWKA_OUTPUT_DIR
from media_hygiene.errors import CrossCheckError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence

type Group = frozenset[Path]

# Czkawka's command-line tool: shipped in the image, run by the printed command too.
CZKAWKA_BINARY: Final = "czkawka_cli"

# Options whose value is a path or a wildcard: quoted in the printed command.
_QUOTED: Final = frozenset({"-e", "-E"})


class _Entry(BaseModel):
    """One file of a Czkawka group; the other fields (size, hash, date) are ignored."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    path: str


_RESULTS = TypeAdapter(dict[str, list[list[_Entry]]])


def read_czkawka_groups(results: Path) -> tuple[Group, ...]:
    """Read the duplicate groups Czkawka found.

    Args:
        results: The JSON file written by `czkawka_cli dup -C`.

    Returns:
        One set of container paths per group.

    Raises:
        CrossCheckError: The file cannot be read or is not Czkawka's JSON.
    """
    try:
        by_size = _RESULTS.validate_json(results.read_bytes())
    except (OSError, ValidationError) as exc:
        raise CrossCheckError(
            _("{path} is not a Czkawka result file.").format(path=results),
            _("Run the Czkawka command again; it writes this file with -C."),
        ) from exc
    return tuple(
        frozenset(Path(entry.path) for entry in group)
        for groups in by_size.values()
        for group in groups
    )


@dataclass(frozen=True, slots=True)
class CzkawkaCommand:
    """Everything Czkawka needs to see the same files as media-hygiene."""

    mounts: tuple[tuple[str, Path], ...]
    output_dir: str
    scope: CzkawkaScope

    def render(self) -> str:
        """Build the `docker run` line, ready to paste in PowerShell or bash.

        Returns:
            The command, on one line.
        """
        volumes = [f'-v "{host}:{point}:ro"' for host, point in self.mounts]
        volumes.append(f'-v "{self.output_dir}:{CZKAWKA_OUTPUT_DIR}"')
        results = f"{CZKAWKA_OUTPUT_DIR}/{CZKAWKA_FILE_NAME}"
        options = (
            f'{flag} "{value}"' if flag in _QUOTED else f"{flag} {value}".strip()
            for flag, value in self.scope.options(results)
        )
        return " ".join(
            (
                "docker run --rm -it",  # a terminal: Czkawka shows its progress
                *volumes,
                CZKAWKA_IMAGE,
                CZKAWKA_BINARY,
                *options,
            )
        )


@dataclass(frozen=True, slots=True)
class CzkawkaScope:
    """What media-hygiene analyses: the data folder, the extensions, the exclusions.

    Folder names become Czkawka wildcards (`-E "*/Thumbnails/*"`, one option each: it
    ignores a comma-separated list). Czkawka matches them case-sensitively: a folder
    in another case is still hashed there, then set aside by the comparison.
    """

    data_dir: Path
    extensions: Sequence[str]
    excluded: tuple[Path, ...] = ()
    excluded_names: tuple[str, ...] = ()

    def options(self, results: str) -> tuple[tuple[str, str], ...]:
        """The `dup` options, the same for the printed command and a run in place.

        Every file size (`-m 1`), no error code when duplicates are found (`-W`),
        no list on the terminal (`-N`), the results as compact JSON (`-C`).

        Args:
            results: Where Czkawka writes its JSON results.

        Returns:
            Each option and its value (empty for a flag), `dup` first.
        """
        return (
            ("dup", ""),
            ("-d", str(self.data_dir)),
            ("-m", "1"),
            ("-W", ""),
            ("-N", ""),
            ("-x", ",".join(self.extensions)),
            *(("-e", str(folder)) for folder in self.excluded),
            *(("-E", f"*/{name}/*") for name in self.excluded_names),
            ("-C", results),
        )

    def arguments(self, results: str) -> tuple[str, ...]:
        """The `dup` options as the arguments of a process (no shell, no quoting).

        Args:
            results: Where Czkawka writes its JSON results.

        Returns:
            The arguments, after the executable.
        """
        return tuple(
            part
            for flag, value in self.options(results)
            for part in ((flag, value) if value else (flag,))
        )
