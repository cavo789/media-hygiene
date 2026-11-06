"""The words dropped and merged (0546, 0622), and the line said after a change."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _, ngettext
from media_hygiene.tags.stop_edit import dropped_words
from media_hygiene.tags.synonym_edit import saved_synonyms

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.tag_drop import Dropped


def sidecar_lines(done: Dropped) -> list[str]:
    """What happened to the sidecars.

    Args:
        done: What dropping or merging did.

    Returns:
        The lines, maybe none.
    """
    lines: list[str] = []
    if done.sidecars:
        lines.append(
            ngettext(
                "Taken out of {n} sidecar: 'mh undo {run}' puts it back.",
                "Taken out of {n} sidecars: 'mh undo {run}' puts them back.",
                done.sidecars,
            ).format(n=done.sidecars, run=done.run_id)
        )
    if done.failed:
        lines.append(
            ngettext(
                "{n} sidecar left as it was.",
                "{n} sidecars left as they were.",
                done.failed,
            ).format(n=done.failed)
        )
    if done.waiting:
        lines.append(
            _("Sidecars not written from here: the next 'xmp --apply' takes it out.")
        )
    return lines


def dropped_line(words: tuple[str, ...], left: int) -> str:
    """The first line of a drop, read back.

    Args:
        words: The words dropped.
        left: The photos still carrying one of them.

    Returns:
        The line.
    """
    return _(
        "“{word}” dropped, read back from the disk: "
        "in the stop words, still on {left} photos."
    ).format(word="”, “".join(words), left=left)


def merged_line(word: str, target: str, left: int) -> str:
    """The first line of a merge, read back.

    Args:
        word: The synonym.
        target: The tag it means.
        left: The photos still carrying the synonym.

    Returns:
        The line.
    """
    return _(
        "“{word}” merged into “{target}”, read back from the disk: "
        "in the synonyms, still on {left} photos."
    ).format(word=word, target=target, left=left)


def listed(config: Path) -> dict[str, object]:
    """The words dropped and merged, read from the disk.

    Args:
        config: `config.toml`.

    Returns:
        `dropped`, and `merged` as pairs.
    """
    merged = sorted(saved_synonyms(config).items(), key=lambda pair: pair[0].casefold())
    return {"dropped": list(dropped_words(config)), "merged": [list(p) for p in merged]}
