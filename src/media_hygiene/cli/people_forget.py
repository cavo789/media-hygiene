"""`people --forget`: delete every face, then, when asked, the names of `config.toml`.

Each deletion is read back and shown: the faces from the index, the names from the
file. The names are only deleted after an explicit yes in a terminal, or with
`--names` (the home page's confirmation states their count first, 0795); without
either they stay, and the console says how to delete them. The previous file is kept
in `/config/.history/`. The home page sends what its confirmation showed
(`--expect <names>/<ignored>`): a name added since, in another tab, makes the whole
run refuse before anything is deleted (review of 2026-11-13).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number
from media_hygiene.errors import MediaHygieneError
from media_hygiene.file_history import HISTORY_DIR, history_root
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.people.config_file import read_people, save_people

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import FaceStore
    from media_hygiene.services.runtime import Runtime

_NOTHING: Final = "0/0"  # `names_shown` of a missing config.toml


@dataclass(frozen=True, slots=True)
class NamesAsked:
    """`--names` and `--expect`: the names go too, as many as the page showed."""

    delete: bool = False  # `--names`: without a question (0795)
    expect: str = ""  # `--expect`: `names_shown` of what the confirmation listed


def names_shown(written: PeopleSettings) -> str:
    """What a confirmation of the names shows, in a word the command can compare.

    Args:
        written: `[people]` as the file holds it.

    Returns:
        E.g. `3/12`: three names, twelve faces ignored.
    """
    return f"{len(written.person)}/{len(written.ignored)}"


def forget_people(
    runtime: Runtime, store: FaceStore, names: NamesAsked | None = None
) -> None:
    """Delete every face, show what the index holds now, then offer the names.

    Args:
        runtime: Output and mount points.
        store: The faces of the open index.
        names: `--names` and `--expect`; None: ask in the terminal.

    Raises:
        MediaHygieneError: `--expect` no longer matches `config.toml`; nothing deleted.
    """
    asked = names or NamesAsked()
    _check_expected(runtime, asked)
    output = runtime.output
    forgotten, left = store.forget()
    output.success(
        ngettext(
            "{count} face forgotten.",
            "{count} faces forgotten.",
            forgotten,
        ).format(count=human_number(forgotten))
    )
    output.info(
        _("Read back from the index: {faces} faces left.").format(
            faces=human_number(left)
        )
    )
    _forget_names(runtime, names=asked.delete)


def _check_expected(runtime: Runtime, asked: NamesAsked) -> None:
    """Refuse when the names changed since the page listed them.

    Args:
        runtime: Mount points.
        asked: `--names` and `--expect`.

    Raises:
        MediaHygieneError: They changed; nothing is deleted.
    """
    if not asked.delete or not asked.expect:
        return
    config = runtime.locations.config_file
    now = names_shown(read_people(config)) if config.is_file() else _NOTHING
    if now != asked.expect:
        raise MediaHygieneError(
            _(
                "The names of config.toml changed since the page listed them: "
                "nothing was deleted."
            ),
            _("Reload the home page: its confirmation lists them again."),
        )


def _forget_names(runtime: Runtime, *, names: bool) -> None:
    """Ask whether the names go too; delete them on a yes, and read the file back.

    Args:
        runtime: Output and mount points.
        names: `--names`: already confirmed.
    """
    config = runtime.locations.config_file
    if not runtime.persistent(MountKind.CONFIG) or not config.is_file():
        return
    output = runtime.output
    written = read_people(config)
    count = len(written.person)
    if not count and not written.ignored:
        return
    question = ngettext(
        "Also delete the {count} name of config.toml ([[people.person]]) and the "
        "faces ignored?",
        "Also delete the {count} names of config.toml ([[people.person]]) and the "
        "faces ignored?",
        count,
    ).format(count=count)
    if not names and not output.confirm(question):
        output.info(
            _(
                "The names stay in config.toml: they name no face until people "
                "finds the faces again. Answer yes in a terminal (docker run -it), "
                "or add --names, to delete them."
            )
        )
        return
    save_people(config, written.model_copy(update={"person": (), "ignored": ()}))
    back = read_people(config)
    gone = sorted(
        {person.name for person in written.person}
        - {person.name for person in back.person}
    )
    output.success(
        _("Read back from config.toml: {names} names, {ignored} faces ignored.").format(
            names=len(back.person), ignored=len(back.ignored)
        )
    )
    if gone:
        output.info(_("Names removed: {names}.").format(names=", ".join(gone)))
    output.info(
        _("The previous config.toml is kept in {folder}.").format(
            folder=history_root(config) / HISTORY_DIR
        )
    )
