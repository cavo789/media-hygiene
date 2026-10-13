"""What the `classify` summary says of the rules that decided nothing, and of `--year`.

Without `--year`, the rules that decided nothing are named: a date or a pattern to
check. With `--year`, most rules are written for other years: one line counts them,
and another the files left out because only the disk dates them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.classify.engine import Classification
    from media_hygiene.console.output import Output


def show_unused_rules(output: Output, classification: Classification) -> None:
    """Name the rules that decided nothing; under `--year`, count them in one line.

    Args:
        output: Where to print.
        classification: The proposals, the rules left unused, the years.
    """
    unused = classification.unused_rules
    years, undated = classification.years
    if years is None:
        if unused:
            names = escape(", ".join(unused))
            output.warning(
                _("Rules that decided nothing: {names}.").format(names=names)
            )
            output.tip(
                _("Check their dates, their patterns and their order in config.toml.")
            )
        return
    span = str(years[0]) if years[0] == years[1] else f"{years[0]}-{years[1]}"
    if unused:
        output.info(
            ngettext(
                "{count} rule decided nothing in {years}: normal for those written "
                "for other years.",
                "{count} rules decided nothing in {years}: normal for those written "
                "for other years.",
                len(unused),
            ).format(count=human_number(len(unused)), years=span)
        )
    show_undated_left(output, undated)


def show_undated_left(output: Output, undated: int) -> None:
    """Under `--year`, count the files only the disk dates, left out of the run.

    Args:
        output: Where to print.
        undated: How many.
    """
    if undated:
        output.info(
            ngettext(
                "{count} file dated only by the disk left out: a classify without "
                "--year proposes it.",
                "{count} files dated only by the disk left out: a classify without "
                "--year proposes them.",
                undated,
            ).format(count=human_number(undated))
        )
