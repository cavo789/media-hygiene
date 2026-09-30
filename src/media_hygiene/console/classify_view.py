"""The console summary of `classify`: progress first, then what is proposed and left."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.classify.models import Band
from media_hygiene.classify.names import band_name
from media_hygiene.console.formatting import human_number, human_share
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal
    from media_hygiene.console.output import Output
    from media_hygiene.services.classify import ClassifyResult

_TOP_EVENTS: Final = 20
_TOP_CATEGORIES: Final = 10
_WORK: Final = frozenset({Band.UNSURE, Band.MANUAL})


def show_classification(output: Output, result: ClassifyResult) -> None:
    """Print what `classify` proposes.

    Args:
        output: Where to print.
        result: The proposals.
    """
    proposals = result.classification.proposals
    if not proposals:
        output.info(_("No photo nor video to classify."))
        return
    in_place = sum(1 for proposal in proposals if proposal.in_place)
    output.info(
        _("Already in place: {share}.").format(
            share=human_share(in_place, len(proposals))
        )
    )
    output.show(_bands_table(proposals))
    output.blank()
    output.show(_reasons_table(proposals))
    output.blank()
    unused = result.classification.unused_rules
    if unused:
        output.warning(
            _("Rules that decided nothing: {names}.").format(
                names=escape(", ".join(unused))
            )
        )
        output.tip(
            _("Check their dates, their patterns and their order in config.toml.")
        )
    _work_left(output, proposals)
    if result.duplicates:
        output.tip(
            _(
                "{count} exact duplicates are still there: run 'clean' first, "
                "otherwise both copies are sorted."
            ).format(count=human_number(result.duplicates))
        )
    output.tip(_("Nothing was changed: 'classify' only proposes."))


def _bands_table(proposals: tuple[Proposal, ...]) -> Table:
    """Files per band, and how many of them move.

    Args:
        proposals: Every proposal.

    Returns:
        The table.
    """
    table = Table(title=_("Proposal"), title_justify="left")
    table.add_column(_("Band"))
    table.add_column(_("Files"), justify="right")
    table.add_column(_("To move"), justify="right")
    for band in Band:
        members = [proposal for proposal in proposals if proposal.band is band]
        if members:
            moving = sum(1 for proposal in members if not proposal.in_place)
            table.add_row(
                band_name(band), human_number(len(members)), human_number(moving)
            )
    return table


def _reasons_table(proposals: tuple[Proposal, ...]) -> Table:
    """Why: the files each rule or reason decided, then the categories found most.

    Args:
        proposals: Every proposal.

    Returns:
        The table.
    """
    table = Table(title=_("Why"), title_justify="left", show_header=False)
    table.add_column(style="bold")
    table.add_column(justify="right")
    reasons = Counter(proposal.rule or proposal.reason.value for proposal in proposals)
    for reason, count in reasons.most_common():
        table.add_row(escape(reason), human_number(count))
    categories = Counter(p.category for p in proposals if p.category)
    for category, count in categories.most_common(_TOP_CATEGORIES):
        table.add_row(f"  {escape(category)}", human_number(count))
    return table


def _work_left(output: Output, proposals: tuple[Proposal, ...]) -> None:
    """Say how much is left to decide, and how much the largest events hold.

    Args:
        output: Where to print.
        proposals: Every proposal.
    """
    work = [proposal for proposal in proposals if proposal.band in _WORK]
    if not work:
        output.success(_("Nothing left to check nor to sort."))
        return
    sizes = Counter(proposal.event_id for proposal in work if proposal.event_id)
    counts = {"files": human_number(len(work)), "events": human_number(len(sizes))}
    text = ngettext(
        "To check or to sort: {files} files in {events} event.",
        "To check or to sort: {files} files in {events} events.",
        len(sizes),
    ).format(**counts)
    if len(sizes) > _TOP_EVENTS:
        held = sum(count for _event, count in sizes.most_common(_TOP_EVENTS))
        text += " " + _("The {top} largest events hold {held} of them.").format(
            top=_TOP_EVENTS, held=human_number(held)
        )
    output.info(text)
