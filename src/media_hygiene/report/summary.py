"""The machine-readable summary stored next to every report (`summary.json`)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_hygiene.constants import RunKind

if TYPE_CHECKING:
    from media_hygiene.crosscheck.compare import CrossCheckResult


_OLD_ONLY_OURS: Final = "only_media_dedup"


class CrossCheckSummary(BaseModel):
    """The verdict of a cross-check with Czkawka, as stored in `summary.json`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agrees: bool
    groups: int
    copies: int
    only_ours: int
    only_czkawka: int
    set_aside: int
    results_date: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_the_0_2_name(cls, data: object) -> object:
        """Read `only_media_dedup`, the name media-dedup 0.2 wrote for `only_ours`.

        Args:
            data: The raw input.

        Returns:
            The input, the old key renamed.
        """
        if not isinstance(data, dict) or _OLD_ONLY_OURS not in data:
            return data
        others = {key: value for key, value in data.items() if key != _OLD_ONLY_OURS}
        return {"only_ours": data[_OLD_ONLY_OURS], **others}

    @classmethod
    def of(cls, result: CrossCheckResult | None) -> CrossCheckSummary | None:
        """Summarise a comparison.

        Args:
            result: The comparison, or None when there was none.

        Returns:
            The summary, or None.
        """
        if result is None:
            return None
        return cls(
            agrees=result.agrees,
            groups=len(result.ours),
            copies=result.copies,
            only_ours=len(result.only_ours),
            only_czkawka=len(result.only_theirs),
            set_aside=sum(result.outside.values()),
            results_date=result.results_date,
        )


class ReportSummary(BaseModel):
    """Headline numbers of one audit or clean, listed by the `reports` command."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str
    kind: RunKind
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    files_scanned: int
    duplicate_groups: int
    duplicate_files: int
    reclaimable_bytes: int
    broken_files: int
    orphan_sidecars: int = 0
    freed_bytes: int = 0
    run_id: str | None = None
    plan_file: str | None = None
    crosscheck: CrossCheckSummary | None = None
