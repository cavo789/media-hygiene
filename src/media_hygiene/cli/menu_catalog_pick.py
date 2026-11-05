"""The import stage's visual paths: the files as photos before the copy (0590)."""

from __future__ import annotations

from media_hygiene.cli.menu_entry import Doc, Field, FieldKind, Kind, Risk, Space, Step
from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _

PICK_ANCHORS = (
    "#see-them-first-mh-import---pick",
    "#les-voir-dabord--mh-import---pick",
)


def folder_field() -> Field:
    """The folder a step of the import takes.

    Returns:
        The field.
    """
    return Field(
        "path",
        _("The folder, as the Explorer shows it"),
        r"E:\DCIM",
        kind=FieldKind.FOLDER,
    )


def import_pick_step() -> Step:
    """What only the backups hold, as photos.

    Returns:
        The action.
    """
    space = Space.IMPORT
    return Step(
        "import-pick",
        space,
        _("See what only the NAS or the disk holds, then copy it"),
        _("As photos: unpick what you do not want, then copy; each copy checked."),
        "import --pick",
        Risk.UNDO,
        Kind.PAGE,
        icon="import",
        keywords=_("nas get back see photos pick backup copy missing"),
        doc=Doc("commands/import/", *PICK_ANCHORS),
        slot=Slot.IMPORT,
    )


def import_folder_pick_step() -> Step:
    """What a folder named holds, as photos: it needs its own mount.

    Returns:
        The action.
    """
    space = Space.IMPORT
    return Step(
        "import-folder-pick",
        space,
        _("See what a USB disk, an SD card or a folder holds, then copy it"),
        _("As photos: only what your photos lack; the folder is only read."),
        "import --pick {path}",
        Risk.UNDO,
        Kind.PAGE,
        icon="import",
        keywords=_("usb disk card sd camera folder see photos pick"),
        doc=Doc("commands/import/", *PICK_ANCHORS),
        fields=(folder_field(),),
    )
