"""The line a fast path says before its question: what it skips, what shows it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def tell_sort_twin(runtime: Runtime) -> None:
    """Before `sort`'s question.

    Args:
        runtime: Settings, mount points and output.
    """
    runtime.output.info(
        _(
            "👁 Moves them without showing them: the classify report shows them "
            "first ('mh reports' lists it)."
        )
    )


def tell_clean_twin(runtime: Runtime, *, near: bool) -> None:
    """Before `clean`'s question.

    Args:
        runtime: Settings, mount points and output.
        near: A near tier: `review --near` shows those one group at a time.
    """
    said = (
        _(
            "👁 Acts on them without showing them: 'review --near' shows the near "
            "duplicates first, the report the copies ('mh reports' lists it)."
        )
        if near
        else _(
            "👁 Acts on them without showing them: the report shows them first "
            "('mh reports' lists it)."
        )
    )
    runtime.output.info(said)


def tell_undo_twin(runtime: Runtime) -> None:
    """Before `undo` of a whole run.

    Args:
        runtime: Settings, mount points and output.
    """
    runtime.output.info(
        _("👁 A whole run: 'undo --pick' shows the photos and puts back only a few.")
    )


def tell_purge_twin(runtime: Runtime) -> None:
    """Before `purge`'s question.

    Args:
        runtime: Settings, mount points and output.
    """
    runtime.output.info(
        _("👁 See these files as photos first: 'undo --pick' (nothing is erased there).")
    )
