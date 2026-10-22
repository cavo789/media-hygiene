"""The share area, outside the cycle: the ways to show the photos to others (0294).

The albums on this PC or a paired phone (0297), the slideshow on the TV (0291), an
album made ready to send (0296), and an album's folder of hard links on the disk
(0298): one album, several uses.
"""

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
from media_hygiene.i18n import _


def share_steps() -> tuple[Step, ...]:
    """The actions of the share area.

    Returns:
        Them, in order.
    """
    return (
        Step(
            "slideshow",
            Space.SHARE,
            _("Show your photos on the TV"),
            _("A folder on the big screen; the phone chooses the next photo."),
            "slideshow --folder {path}",
            Risk.SAFE,
            Kind.PAGE,
            icon="image",
            keywords=_("slideshow tv television chromecast phone remote holidays"),
            doc=Doc("commands/slideshow/"),
            fields=(
                Field(
                    "path",
                    _("The folder to show, as the Explorer shows it"),
                    r"C:\Photos\2026 Holidays",
                    kind=FieldKind.FOLDER,
                ),
            ),
            optional=True,
        ),
        Step(
            "share",
            Space.SHARE,
            _("Prepare an album for sending"),
            _(
                "Resized copies without the GPS position, a folder and a zip: for a "
                "mail, a social network or a USB stick. Your photos are only read."
            ),
            "share --album {album}",
            Risk.SAFE,
            icon="album",
            keywords=_("send mail email attach zip facebook social network album gps"),
            doc=Doc("commands/share/"),
            fields=(Field("album", _("The album's name"), _("Crete 2023")),),
            optional=True,
        ),
        Step(
            "album",
            Space.SHARE,
            _("A folder of links on the disk"),
            _(
                "The album's photos in one folder of the Explorer, as hard links: no "
                "copy, no room taken, undone by undo."
            ),
            "album {album}",
            Risk.UNDO,
            icon="album",
            keywords=_("album folder explorer links christmas holidays"),
            doc=Doc("commands/album/"),
            fields=(Field("album", _("The album's name"), _("Crete 2023")),),
            optional=True,
        ),
    )


def share_area() -> Area:
    """The share area: no stage number, it is a goal, not a step of the cycle.

    Returns:
        It.
    """
    return Area(
        Space.SHARE,
        _("Share"),
        _("Share your photos"),
        _(
            "Your albums on the TV, on a phone, ready to send by mail, or as a "
            "folder on the disk."
        ),
        "image",
        (
            Group(_("Your albums"), (), extra="albums"),  # on a phone too (0297)
            Group(_("The commands"), ("slideshow", "share", "album")),
        ),
        Doc("commands/slideshow/"),
        _("mh slideshow"),
    )
