"""How sure a proposal is, and which layout that gives.

The score of a reason comes from its rule or from `[classify] scores`, never from the
code; it is capped by the date's confidence. `≥ sure` is sure, `≥ unsure` goes to
"to check", the rest to "to sort". A file dated by its mtime only is "undated".
Without `{category}` in the layout, a reliable date is enough: `{year}/{month}` needs
no taxonomy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band, DateSource, SortReason, Verdict

if TYPE_CHECKING:
    from media_hygiene.classify.models import Dating
    from media_hygiene.classify.signals import Signal
    from media_hygiene.config.classify_settings import ClassifySettings


def verdict(signal: Signal, dating: Dating, settings: ClassifySettings) -> Verdict:
    """Decide how sure a proposal is.

    Args:
        signal: What the folders (and the rules) said.
        dating: The file's date.
        settings: Scores and thresholds.

    Returns:
        The verdict.
    """
    if dating.source is DateSource.MTIME:
        return Verdict(Band.UNDATED, SortReason.UNDATED, 0)
    reason = signal.reason
    if reason is SortReason.NO_SIGNAL and "{category}" not in settings.layout:
        reason = SortReason.DATE_ONLY
    own = signal.score
    if own is None:
        own = settings.scores.get(reason.value, 0)
    score = min(own, dating.confidence)
    if score >= settings.sure:
        return Verdict(Band.SURE, reason, score, signal.rule)
    if score >= settings.unsure:
        return Verdict(Band.UNSURE, reason, score, signal.rule)
    return Verdict(Band.MANUAL, reason, score, signal.rule)


def layout_of(band: Band, settings: ClassifySettings, *, camera: bool) -> str:
    """The layout of a band.

    Args:
        band: The band.
        settings: The layouts.
        camera: For undated files: whether a camera took it (else received).

    Returns:
        The layout; empty means "stay where it is".
    """
    layouts = {
        Band.SURE: settings.layout,
        Band.UNSURE: settings.unsure_layout,
        Band.MANUAL: settings.manual_layout,
        Band.STAY: "",
    }
    if band is Band.UNDATED:
        return settings.undated_layout if camera else settings.received_layout
    return layouts[band]


def band_folders(settings: ClassifySettings) -> tuple[str, ...]:
    """The fixed folder names the layouts write ("To check", "À trier"…).

    Args:
        settings: The layouts.

    Returns:
        Every segment without a placeholder: never a meaning for the next run.
    """
    layouts = (
        settings.layout,
        settings.unsure_layout,
        settings.manual_layout,
        settings.undated_layout,
        settings.received_layout,
    )
    return tuple(
        segment
        for layout in layouts
        for segment in layout.split("/")
        if segment and "{" not in segment
    )
