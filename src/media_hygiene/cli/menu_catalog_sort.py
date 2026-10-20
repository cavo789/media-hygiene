"""Stage 3, sort: the guide of "Sort in short", then an album."""

from __future__ import annotations

from media_hygiene.cli.menu_entry import (
    Area,
    Doc,
    Field,
    Group,
    Kind,
    Risk,
    Space,
    Step,
)
from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _


def sort_steps() -> tuple[Step, ...]:
    """The actions of the sort stage.

    Returns:
        Them, in order.
    """
    space = Space.SORT
    return (
        Step(
            "classify",
            space,
            _("Propose a tidy tree"),
            _("By year, event, place or person, in a workbook you correct."),
            "classify",
            Risk.SAFE,
            icon="folders",
            keywords=_("classify tidy propose tree workbook excel year event"),
            doc=Doc("commands/classify/"),
            slot=Slot.CLASSIFY,
            ai=True,
        ),
        Step(
            "review-sort",
            space,
            _("Name the events"),
            _("One by one, with their photos, in the browser."),
            "review-sort",
            Risk.SAFE,
            Kind.PAGE,
            icon="calendar",
            keywords=_("events name parties holidays"),
            doc=Doc("commands/review-sort/"),
            optional=True,
        ),
        Step(
            "places",
            space,
            _("Name your places on a map"),
            _("To sort by place and by trip; no position leaves the PC."),
            "places",
            Risk.SAFE,
            Kind.PAGE,
            icon="pin",
            keywords=_("places map gps trips spots"),
            doc=Doc("commands/places/"),
            optional=True,
        ),
        Step(
            "people",
            space,
            _("Name the faces"),
            _("Faces that look alike are grouped; they stay in the cache."),
            "people",
            Risk.SAFE,
            Kind.PAGE,
            icon="face",
            keywords=_("faces people names family"),
            doc=Doc("commands/people/"),
            slot=Slot.PEOPLE,
            optional=True,
        ),
        Step(
            "sort",
            space,
            _("Move the photos as the workbook says"),
            _("Checks the workbook, asks, then moves: undoable, proven."),
            "sort",
            Risk.UNDO,
            icon="arrow-right",
            keywords=_("sort move tidy apply workbook"),
            doc=Doc("commands/sort/"),
            slot=Slot.SORT,
        ),
        Step(
            "album",
            space,
            _("Gather a selection into an album"),
            _("Links, not copies: no room taken."),
            "album {name} --category {category}",
            Risk.UNDO,
            icon="album",
            keywords=_("album selection links christmas holidays"),
            doc=Doc("commands/album/"),
            fields=(
                Field("name", _("The album's name"), _("Christmas 2025")),
                Field("category", _("The workbook's category"), _("Christmas")),
            ),
            optional=True,
        ),
    )


def sort_area() -> Area:
    """The sort stage: its guide, then an album.

    Returns:
        It.
    """
    guide = ("classify", "review-sort", "places", "people", "sort")
    return Area(
        Space.SORT,
        _("Sort out"),
        _("Sort the photos"),
        _(
            "Get a proposed tree, correct it in a workbook or in the browser, then "
            "apply it. Nothing moves before you agree."
        ),
        "folders",
        (
            Group(_("The guide"), guide, numbered=True),
            Group(_("Go further"), ("album",)),
        ),
        Doc("sort/quick-guide/"),
        _("Sort in short"),
        stage=3,
    )
