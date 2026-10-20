"""Stages 4 and 5: find a photo, then back up to the NAS (planned, TODO 0264)."""

from __future__ import annotations

from media_hygiene.cli.menu_entry import (
    Area,
    Doc,
    Field,
    FieldKind,
    Group,
    Kind,
    Risk,
    Space,
    Step,
)
from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _


def find_steps() -> tuple[Step, ...]:
    """The actions of the find stage, then those of the backup, planned.

    Returns:
        Them, in order.
    """
    space = Space.FIND
    return (
        Step(
            "tags",
            space,
            _("Give your photos words"),
            _(
                "Their folders, their name, their date, their place, and what a "
                "local AI sees in them if you have one."
            ),
            "tags",
            Risk.SAFE,
            icon="tag",
            keywords=_("words tags labels ai"),
            doc=Doc("commands/tags/"),
            slot=Slot.TAGS,
            ai=True,
        ),
        Step(
            "search",
            space,
            _("Find a photo by its words"),
            _("A word, a place, a year, a person: with previews, in the browser."),
            "search",
            Risk.SAFE,
            Kind.PAGE,
            icon="search",
            keywords=_("search look for find photo"),
            doc=Doc("commands/search/"),
        ),
        Step(
            "browse",
            space,
            _("Walk through your folders"),
            _("As in the Explorer, full size with ← and →; set photos aside."),
            "browse",
            Risk.SAFE,
            Kind.PAGE,
            icon="image",
            keywords=_("browse explore folders gallery"),
            doc=Doc("commands/browse/"),
            optional=True,
        ),
        Step(
            "xmp",
            space,
            _("Carry the words into other photo software"),
            _(
                "digiKam, darktable, Lightroom, Immich: .xmp files next to the "
                "photos, never inside them."
            ),
            "xmp",
            Risk.UNDO,
            icon="file-xmp",
            keywords=_("xmp lightroom digikam darktable immich sidecar"),
            doc=Doc("commands/xmp/"),
            optional=True,
        ),
        Step(
            "inventory",
            space,
            _("All your photos in Excel"),
            _("From the cache alone: no file is read again."),
            "inventory",
            Risk.SAFE,
            icon="table",
            keywords=_("excel inventory csv table list"),
            doc=Doc("commands/inventory/"),
            optional=True,
        ),
        Step(
            "backup-to",
            Space.BACKUP,
            _("Choose the backup folder on the NAS"),
            _("A folder of its own, never mixed with your other shares."),
            "backup --to {path}",
            Risk.SAFE,
            Kind.HOST,
            icon="nas",
            keywords=_("backup nas destination"),
            fields=(
                Field(
                    "path",
                    _("The backup folder, as the Explorer shows it"),
                    r"\\NAS\backup_photos",
                    kind=FieldKind.FOLDER,
                ),
            ),
            planned=True,
        ),
        Step(
            "backup",
            Space.BACKUP,
            _("Back up what the NAS lacks"),
            _(
                "Only what is new; a photo moved by sort is renamed on the NAS, "
                "not sent again."
            ),
            "backup",
            Risk.UNDO,
            Kind.HOST,
            icon="shield",
            keywords=_("backup nas copy robocopy"),
            planned=True,
        ),
    )


def find_areas() -> tuple[Area, ...]:
    """The find stage, then the backup stage, planned.

    Returns:
        Both.
    """
    find = Area(
        Space.FIND,
        _("Find"),
        _("Find a photo"),
        _(
            "Give your photos words, then find them again by a word, a place, a "
            "year or a person."
        ),
        "search",
        (
            Group(_("The guide"), ("tags", "search"), numbered=True),
            Group(_("Go further"), ("browse", "xmp", "inventory")),
        ),
        Doc("find/quick-guide/"),
        _("Find in short"),
        stage=4,
    )
    backup = Area(
        Space.BACKUP,
        _("Back up"),
        _("Back up to the NAS"),
        _(
            "Copy to your NAS only what it lacks, at Windows' speed. A photo deleted "
            "by mistake on the PC is never deleted from the NAS."
        ),
        "shield",
        (
            Group(_("The guide"), ("backup-to", "backup"), numbered=True),
            Group(_("And to go back"), ("import",)),
        ),
        stage=5,
        planned=True,
    )
    return find, backup
