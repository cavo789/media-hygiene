"""`people --forget`: delete every face, then, when asked, the names of `config.toml`.

Each deletion is read back and shown: the faces from the index, the names from the
file. The names are only deleted after an explicit yes in a terminal; without one
they stay, and the console says how to delete them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.people.config_file import read_people, save_people

if TYPE_CHECKING:
    from media_hygiene.index.face_rows import FaceStore
    from media_hygiene.services.runtime import Runtime


def forget_people(runtime: Runtime, store: FaceStore) -> None:
    """Delete every face, show what the index holds now, then offer the names.

    Args:
        runtime: Output and mount points.
        store: The faces of the open index.
    """
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
    _forget_names(runtime)


def _forget_names(runtime: Runtime) -> None:
    """Ask whether the names go too; delete them on a yes, and read the file back.

    Args:
        runtime: Output and mount points.
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
    if not output.confirm(question):
        output.info(
            _(
                "The names stay in config.toml: they name no face until people "
                "finds the faces again. Answer yes in a terminal (docker run -it) to "
                "delete them."
            )
        )
        return
    save_people(config, written.model_copy(update={"person": (), "ignored": ()}))
    back = read_people(config)
    output.success(
        _("Read back from config.toml: {names} names, {ignored} faces ignored.").format(
            names=len(back.person), ignored=len(back.ignored)
        )
    )
