r"""The decisions file the report downloads and `review` writes; `clean` reads it.

```json
{"version": 1, "report": "20260926-171446-audit", "roots": ["C:\\Photos"],
 "pairs": [{"kept_in": "C:\\Photos\\2019", "removed_from": "D:\\Old",
            "action": "swap"}],
 "bursts": [{"status": "done", "kept": ["C:\\Photos\\IMG_1.jpg"],
             "discarded": ["C:\\Photos\\IMG_2.jpg"]}],
 "chosen": [{"path": "C:\\Photos\\IMG_3.jpg", "size": 2048,
             "mtime_ns": 1700000000000000000, "found_by": "person:\"Ann\""}]}
```

Paths are host paths, as the report shows them. `roots` are the folders analysed by the
audit behind the decisions: `clean` refuses the file when it sees other folders. Pairs
left as planned are not listed. `review` lists every burst series from the start,
`todo` until seen, then `done`; a series kept whole has an empty `discarded`, a series
set aside whole an empty `kept`. Without `status` (older file, report), it is done.
`chosen` lists the files set aside in `search` (`chosen_decisions`): they need no
audit, so a file holding nothing else is not refused for its `roots`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.plan.review import PairAction
from media_hygiene.report.burst_decisions import BurstDecisions
from media_hygiene.report.chosen_decisions import ChosenFiles
from media_hygiene.report.near_decisions import NearGroups
from media_hygiene.text_files import decode_user_text

if TYPE_CHECKING:
    from pathlib import Path

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class PairDecision(BaseModel):
    """The decision on one folder pair, in host paths."""

    model_config = _FROZEN

    kept_in: str
    removed_from: str
    action: PairAction


class DecisionsFile(BaseModel):
    """Every decision of one review, and the audit it was made on."""

    model_config = _FROZEN

    version: Literal[1]
    report: str = ""
    roots: tuple[str, ...]
    pairs: tuple[PairDecision, ...] = ()
    bursts: BurstDecisions = ()  # `review` (`burst_decisions`)
    near: NearGroups = ()  # `review --near` (`near_decisions`)
    chosen: ChosenFiles = ()  # `search`, `browse` (`chosen_decisions`)

    @property
    def only_chosen(self) -> bool:
        """Tell whether the file holds files chosen in `search`, and nothing else.

        They are named one by one, with their size and date: they do not depend
        on the folders an audit analysed.

        Returns:
            True when it holds chosen files and no pair, series nor group.
        """
        return bool(self.chosen) and not (self.pairs or self.bursts or self.near)

    @field_validator("pairs")
    @classmethod
    def _each_pair_once(
        cls, pairs: tuple[PairDecision, ...]
    ) -> tuple[PairDecision, ...]:
        """Refuse a pair decided twice: which decision would win?

        Args:
            pairs: The decisions.

        Returns:
            The decisions, unchanged.

        Raises:
            ValueError: A pair appears twice.
        """
        seen: set[tuple[str, str]] = set()
        for pair in pairs:
            key = (pair.kept_in, pair.removed_from)
            if key in seen:
                message = f"{pair.kept_in} -> {pair.removed_from} is decided twice"
                raise ValueError(message)
            seen.add(key)
        return pairs


def read_decisions(path: Path) -> DecisionsFile:
    """Read and validate a decisions file, UTF-8 or UTF-16 as Windows tools save it.

    Args:
        path: The file, in the container.

    Returns:
        Its decisions.

    Raises:
        DecisionsError: The file is missing or is not a valid decisions file.
    """
    tip = _("Download it again from the report, next to it on /reports.")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        message = _("Cannot read the decisions file {path}.").format(path=path)
        raise DecisionsError(message, tip) from exc
    try:
        return DecisionsFile.model_validate_json(decode_user_text(raw))
    except UnicodeDecodeError as exc:
        message = _("{path} is not a valid decisions file ({error}).").format(
            path=path, error=exc.reason
        )
        raise DecisionsError(message, tip) from exc
    except ValidationError as exc:
        message = _("{path} is not a valid decisions file ({error}).").format(
            path=path, error=exc.errors()[0]["msg"]
        )
        raise DecisionsError(message, tip) from exc


def write_decisions(path: Path, decisions: DecisionsFile) -> None:
    """Save a decisions file at once: a crash never leaves half a file behind.

    UTF-8 without byte order mark, as JSON expects (RFC 8259, section 8.1).

    Args:
        path: The file, in the container.
        decisions: What to save.
    """
    draft = path.with_name(f".{path.name}.partial")
    draft.write_text(decisions.model_dump_json(indent=2) + "\n", encoding="utf-8")
    draft.replace(path)
