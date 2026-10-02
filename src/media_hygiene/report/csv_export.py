"""The whole plan as a spreadsheet: one row per file, readable by Excel in any language.

The HTML report caps the groups it lists; this file never does. Excel reads a CSV with
the list separator of the regional settings (`;` in French, `,` in English) and needs a
byte order mark to read accents: both follow the interface language. Excel computes a
cell that starts with `=`, `+`, `-` or `@`: such text gets a leading apostrophe, so that
a file named `-2019 trip.jpg` shows its name, not `#NAME?` (`spreadsheet_text`).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import BrokenReason, Locale, MediaKind
from media_hygiene.i18n import _, active_locale
from media_hygiene.report.reasons import broken_reason_label, keep_reason_label

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.scan.models import BrokenFile, MediaFile

type Row = tuple[str | int, ...]

_SEPARATORS: Final = {Locale.FR: ";"}
_DEFAULT_SEPARATOR: Final = ","
# The byte order mark tells Excel the file is UTF-8.
CSV_ENCODING: Final = "utf-8-sig"
CSV_DATE_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
_NANOSECONDS: Final = 1_000_000_000
# What makes Excel read a cell as a formula, and the prefix that keeps it text.
_FORMULA_STARTS: Final = ("=", "+", "-", "@", "\t", "\r")
_TEXT_PREFIX: Final = "'"


def spreadsheet_text(text: str) -> str:
    """Text that Excel shows as it is, never computes.

    Args:
        text: A cell's text: a name, a folder, a camera.

    Returns:
        The text, with a leading apostrophe when it starts like a formula.
    """
    return _TEXT_PREFIX + text if text.startswith(_FORMULA_STARTS) else text


def list_separator() -> str:
    """The list separator Excel expects in the interface language.

    Returns:
        `;` in French, `,` otherwise.
    """
    return _SEPARATORS.get(active_locale(), _DEFAULT_SEPARATOR)


def write_plan_csv(target: Path, plan: CleanPlan, mapper: HostPathMapper) -> None:
    """Write every file of the plan: group by group, the broken files, the orphans.

    Args:
        target: The CSV file to write.
        plan: The plan of the audit or clean.
        mapper: Host/container path translator.
    """
    rows = _Rows(mapper)
    with target.open("w", encoding=CSV_ENCODING, newline="") as stream:
        writer = csv.writer(stream, delimiter=list_separator())
        writer.writerow(
            (
                _("Group"),
                _("SHA-256"),
                _("Size (bytes)"),
                _("Action"),
                _("File"),
                _("Folder"),
                _("Modified (UTC)"),
                _("Detail"),
            )
        )
        writer.writerows(rows.duplicates(plan))
        writer.writerows(rows.broken(plan))
        orphan = _Line(
            _("move to the quarantine"),
            detail=_("Orphan sidecar: no file of the same name left next to it"),
        )
        writer.writerows(rows.row(file, orphan) for file in plan.orphans)


@dataclass(frozen=True, slots=True)
class _Line:
    """What a row says about its file, beyond the file itself."""

    action: str
    group: str = ""
    digest: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class _Rows:
    """Builds the rows, in host paths."""

    mapper: HostPathMapper

    def duplicates(self, plan: CleanPlan) -> Iterator[Row]:
        """One row per file of every duplicate group, the kept copy first.

        Args:
            plan: The plan.

        Yields:
            The rows.
        """
        for number, decision in enumerate(plan.decisions, start=1):
            group, digest = str(number), decision.digest
            reason = keep_reason_label(decision.reason)
            keep = _Line(_("keep"), group, digest, reason)
            yield self.row(decision.keeper, keep)
            for file in decision.removable:
                moved = file.kind is MediaKind.OTHER
                action = _("move to the quarantine") if moved else _("delete")
                yield self.row(file, _Line(action, group, digest))
            for file in decision.protected:
                yield self.row(file, _Line(_("protected, kept"), group, digest))
            for file in decision.spared:
                yield self.row(file, _Line(_("kept (your decision)"), group, digest))

    def broken(self, plan: CleanPlan) -> Iterator[Row]:
        """One row per broken file, handled or left alone in a protected folder.

        Args:
            plan: The plan.

        Yields:
            The rows.
        """
        for item in plan.broken:
            empty = item.reason is BrokenReason.EMPTY
            action = _("delete") if empty else _("move to the quarantine")
            yield self.row(item.file, _Line(action, detail=_describe(item)))
        for item in plan.protected_broken:
            line = _Line(_("protected, kept"), detail=_describe(item))
            yield self.row(item.file, line)

    def row(self, file: MediaFile, line: _Line) -> Row:
        """One row: what the plan does to a file, and why.

        Args:
            file: The file.
            line: The action, its group and details.

        Returns:
            The row, in host paths.
        """
        modified = datetime.fromtimestamp(file.mtime_ns / _NANOSECONDS, UTC)
        texts = (
            line.group,
            line.digest,
            str(file.size),
            line.action,
            self.mapper.to_host(file.path),
            self.mapper.to_host(file.path.parent),
            modified.strftime(CSV_DATE_FORMAT),
            line.detail,
        )
        return tuple(spreadsheet_text(text) for text in texts)


def _describe(item: BrokenFile) -> str:
    """Say why a file is broken, with the decoder's message when there is one.

    Args:
        item: The broken file.

    Returns:
        The translated reason.
    """
    reason = broken_reason_label(item.reason)
    return f"{reason} — {item.detail}" if item.detail else reason
