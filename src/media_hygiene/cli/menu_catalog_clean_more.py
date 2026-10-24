"""Stage 2, clean, "go further": other reviews, a second opinion, deleting at once."""

from __future__ import annotations

from media_hygiene.cli.menu_entry import Doc, Kind, Risk, Space, Step
from media_hygiene.i18n import _

REVIEW_PAGE = "commands/review/"


def clean_more_steps() -> tuple[Step, ...]:
    """The optional actions of the clean stage.

    Returns:
        Them, in order.
    """
    space = Space.CLEAN
    return (
        Step(
            "review-near",
            space,
            _("Settle the near duplicates"),
            _("The resized or recompressed copies, group by group."),
            "review --near",
            Risk.SAFE,
            Kind.PAGE,
            icon="near",
            keywords=_("near duplicates similar resized recompressed"),
            doc=Doc("clean/11-near-duplicates/"),
            optional=True,
        ),
        Step(
            "review-pairs",
            space,
            _("Decide folder by folder"),
            _("When two folders repeat each other: which one to keep, in one click."),
            "review --pairs",
            Risk.SAFE,
            Kind.PAGE,
            icon="pairs",
            keywords=_("pairs folders duplicated"),
            doc=Doc("clean/12-decide-pair-by-pair/"),
            optional=True,
        ),
        Step(
            "review-junk",
            space,
            _("Set the failed photos aside"),
            _("Blurred, dark, screenshots: the most likely unwanted first."),
            "review --junk",
            Risk.SAFE,
            Kind.PAGE,
            icon="junk",
            keywords=_("failed blurred dark unwanted screenshots"),
            doc=Doc("clean/14-unwanted-photos/"),
            optional=True,
        ),
        Step(
            "review-gone",
            space,
            _("Look again at the photos gone"),
            _("Those deleted in the Explorer since an audit: on purpose, or lost?"),
            "review --gone",
            Risk.SAFE,
            Kind.PAGE,
            icon="ghost",
            keywords=_("gone deleted lost explorer"),
            doc=Doc(REVIEW_PAGE, "#five-kinds-of-review", "#cinq-sortes-de-tri"),
            optional=True,
        ),
        Step(
            "crosscheck",
            space,
            _("Ask for a second opinion"),
            _("Czkawka, an independent finder, compares its duplicates with ours."),
            "crosscheck",
            Risk.SAFE,
            icon="scale",
            keywords=_("czkawka second opinion check compare"),
            doc=Doc("commands/crosscheck/"),
            optional=True,
        ),
        Step(
            "shrink",
            space,
            _("Lighten the heavy videos"),
            _(
                "Old camera clips re-encoded, about four times lighter: compare "
                "before and after in the browser, then lighten; each original in "
                "the quarantine."
            ),
            "shrink --try",
            Risk.UNDO,
            Kind.PAGE,
            icon="film",
            keywords=_("videos heavy lighten compress space mjpeg"),
            doc=Doc("commands/shrink/"),
            optional=True,
        ),
        Step(
            "clean-delete",
            space,
            _("Delete the copies at once"),
            _(
                "Instead of the quarantine, when room is urgent; undo rebuilds them "
                "from the copy kept."
            ),
            "clean --delete",
            Risk.FINAL,
            icon="trash",
            keywords=_("delete erase room fast"),
            doc=Doc(
                "clean/08-clean/",
                "#need-the-space-at-once---delete",
                "#besoin-de-la-place-tout-de-suite----delete",
            ),
            optional=True,
        ),
    )
