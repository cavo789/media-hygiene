r"""Stage 1, import: the photos of a phone, then what only the NAS still holds."""

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

FOLDERS_PAGE = "start/03-several-folders/"
LAUNCHER_PAGE = "commands/launcher/"


def import_steps() -> tuple[Step, ...]:
    """The actions of the import stage.

    Returns:
        Them, in the order of its guides.
    """
    space = Space.IMPORT
    return (
        Step(
            "phone",
            space,
            _("Copy the new photos of the phone"),
            _("Plug it in over USB: only the new ones are copied, nothing is erased."),
            "phone",
            Risk.SAFE,
            Kind.HOST,
            icon="phone",
            keywords=_("phone smartphone iphone android usb cable copy dcim"),
            doc=Doc(
                LAUNCHER_PAGE,
                "#a-phone-copy-only-its-new-photos-mh-phone",
                "#un-téléphone--copiez-seulement-ses-nouvelles-photos--mh-phone",
            ),
            windows=True,
        ),
        Step(
            "phone-free",
            space,
            _("Make room on the phone"),
            _(
                "Only what the PC already holds, proven file by file, and that you "
                "tick on a page."
            ),
            "phone --free",
            Risk.FINAL,
            Kind.HOST,
            icon="phone",
            keywords=_("phone room free space delete erase memory full"),
            doc=Doc(
                LAUNCHER_PAGE,
                "#free-the-phone-mh-phone---free",
                "#libérer-le-téléphone--mh-phone---free",
            ),
            optional=True,
            windows=True,
            # Start opens a page; only its own button erases, file by file (0311).
            confirm=(
                _("Make room on the phone: launching erases nothing"),
                _(
                    "A page opens with the files the PC already holds, all ticked: "
                    "untick those you keep. Nothing leaves the phone before that "
                    "page's \u201cDelete \u2026 from the phone\u201d button, and each "
                    "file is compared with the PC's copy once more just before."
                ),
            ),
        ),
        Step(
            "nas-add",
            space,
            _("Plug in your NAS or an old disk"),
            _(
                "Compared with your photos, never changed: the audit says what only "
                "it keeps."
            ),
            "folders add --backup {path}",
            Risk.SAFE,
            Kind.HOST,
            icon="nas",
            keywords=_("nas synology backup old disk share network smb"),
            doc=Doc(
                FOLDERS_PAGE,
                "#a-backup-or-an-old-disk-compare-it",
                "#une-sauvegarde-ou-un-ancien-disque--comparez-le",
            ),
            fields=(
                Field(
                    "path",
                    _("The backup folder, as the Explorer shows it"),
                    r"\\NAS\Photos",
                    kind=FieldKind.FOLDER,
                ),
            ),
        ),
        Step(
            "import",
            space,
            _("Get back what only the NAS holds"),
            _("Never what you set aside or deleted on purpose; each copy is checked."),
            "import",
            Risk.UNDO,
            icon="import",
            keywords=_("nas get back restore backup copy missing"),
            doc=Doc("commands/import/"),
            slot=Slot.IMPORT,
        ),
        Step(
            "folders-add",
            space,
            _("Add a photo folder"),
            _("Windows lets you choose the folder; mh keeps it for every command."),
            "folders add",
            Risk.SAFE,
            Kind.HOST,
            icon="folder-plus",
            keywords=_("folder add disk usb photos"),
            doc=Doc(
                FOLDERS_PAGE,
                "#add-a-folder-mh-folders-add",
                "#ajouter-un-dossier--mh-folders-add",
            ),
        ),
    )


def import_area() -> Area:
    """The import stage: two independent guides, then one more action.

    Returns:
        It.
    """
    return Area(
        Space.IMPORT,
        _("Import"),
        _("Import photos"),
        _(
            "Gather your photos on the PC: those of the phone, and those only your "
            "NAS still keeps. Nothing leaves the phone or the NAS without your say."
        ),
        "import",
        (
            Group(_("From a phone"), ("phone", "phone-free"), numbered=True),
            Group(
                _("From your NAS or an old disk"), ("nas-add", "import"), numbered=True
            ),
            Group(_("Go further"), ("folders-add",)),
        ),
        Doc(FOLDERS_PAGE),
        _("3. Several folders and disks"),
        stage=1,
    )
