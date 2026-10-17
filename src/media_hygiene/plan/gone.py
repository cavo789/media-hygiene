"""The answers of `review --gone`, checked against the index, for `clean` (0224)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.index.gone_rows import GoneRecord


@dataclass(frozen=True, slots=True)
class GoneAnswer:
    """A file gone, and the user's answer: deleted on purpose, or moved elsewhere.

    `clean --decisions` writes a journal mark for a file deleted on purpose, so that
    it is set aside if it comes back, and forgets the record of both answers.
    """

    record: GoneRecord
    deleted: bool
