"""The audit's last step: the thumbnails of the library, Ctrl+C to skip (0674)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import ngettext
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.thumbs_ahead import AheadRun, make_thumbnails, pictures

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


def thumbs_after_audit(runtime: Runtime, findings: AuditFindings) -> None:
    """Make the thumbnails the library page will show, once the audit is written.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just written (its listed files).
    """
    if findings.listed is None or runtime.previews_dir is None:
        return
    output = runtime.output
    with RichProgress(output.console) as progress, StopRequest() as stop:
        outcome = make_thumbnails(
            runtime, pictures(findings.listed), AheadRun(progress, stop.requested)
        )
    if outcome is None:
        return
    if outcome.left:
        output.info(
            ngettext(
                "Thumbnails stopped: {left} photo left, made when a page shows it.",
                "Thumbnails stopped: {left} photos left, made when a page shows them.",
                outcome.left,
            ).format(left=outcome.left)
        )
    elif outcome.made:
        output.info(
            ngettext(
                "🖼 {made} new thumbnail ready: the library opens at once.",
                "🖼 {made} new thumbnails ready: the library opens at once.",
                outcome.made,
            ).format(made=outcome.made)
        )
