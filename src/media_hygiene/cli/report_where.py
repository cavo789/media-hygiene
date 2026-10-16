"""Where the report just written is, said the way the user can open it.

Docker Desktop tells the host folder behind `/reports`: the report is named by it,
Ctrl+click opens it. Under the `mh` launcher, the container still cannot open a
browser, but `mh open` can, on the host (0175): the closing tip names that command.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.console.links import file_link
from media_hygiene.constants import REPORT_INDEX_FILE_NAME
from media_hygiene.i18n import _
from media_hygiene.services.launcher_host import OPEN
from media_hygiene.services.next_command import LAUNCHER_FUNCTION, LAUNCHER_VARIABLE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def announce_report(runtime: Runtime, report: Path) -> None:
    """Name the report written, then say how to see every report.

    Args:
        runtime: Settings, mount points and output.
        report: The report written, as the container sees it.
    """
    output = runtime.output
    mapper = runtime.mapper
    index = runtime.locations.reports_dir / REPORT_INDEX_FILE_NAME
    index_on_host = mapper.to_host(index)
    known = index_on_host != str(index)  # else the host folder of /reports is unknown
    shown = file_link(mapper.to_host(report)) if known else str(report)
    output.success(_("HTML report: {path}").format(path=shown))
    if os.environ.get(LAUNCHER_VARIABLE):
        command = f"{LAUNCHER_FUNCTION} {OPEN}"
        output.advise(
            Advice(
                TipKind.NEXT,
                _("Type {command}: your browser shows every report.").format(
                    command=command
                ),
            )
        )
        return
    if known:
        tip = _("Every report is listed in {path} (Ctrl+click opens it).").format(
            path=file_link(index_on_host)
        )
    else:
        tip = _(
            "Open index.html in the folder mounted on /reports: it lists every report."
        )
    output.advise(Advice(TipKind.DETAIL, tip))
