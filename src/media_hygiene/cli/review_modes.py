"""The modes of `review` other than the burst series: one page each, one key each.

`review` alone reviews the burst series (`cmd_review`); `--near` the near duplicates,
`--pairs` the folder pairs of the exact duplicates, `--junk` the photos most likely
unwanted, `--gone` the files deleted in the Explorer (`gone_review_flow`), `--intruders`
the files neither photos nor videos (`intruders_review_flow`). One mode per
run: each page writes its own key of the same decisions file,
keeping the others.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.cli.apply_step import end_on_applied, page_apply
from media_hygiene.cli.gone_review_flow import run_gone
from media_hygiene.cli.intruders_review_flow import run_intruders
from media_hygiene.cli.near_review_flow import tell_near_opened, tell_near_stopped
from media_hygiene.cli.pairs_review_flow import tell_pairs_opened, tell_pairs_stopped
from media_hygiene.cli.unwanted_review_flow import (
    tell_unwanted_opened,
    tell_unwanted_stopped,
)
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.review.apply_api import ReviewStart
from media_hygiene.services import (
    near_reviewing,
    pairs_reviewing,
    unwanted_reviewing,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import typer

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


class ReviewMode(StrEnum):
    """What `review` puts on its page."""

    BURSTS = "bursts"
    NEAR = "near"
    PAIRS = "pairs"
    JUNK = "junk"
    GONE = "gone"
    INTRUDERS = "intruders"


@dataclass(frozen=True, slots=True)
class ReviewRun:
    """One `review` run: its command line, runtime, decisions file and port."""

    ctx: typer.Context
    runtime: Runtime
    target: Path
    port: int


def review_mode(given: Mapping[ReviewMode, bool]) -> ReviewMode:
    """Choose the mode from the options, one at most.

    Args:
        given: Whether `--near`, `--pairs`, `--junk`, `--gone`, `--intruders`
            were given.

    Returns:
        The mode; the burst series without an option.

    Raises:
        ConfigError: Two options or more are given.
    """
    chosen = [mode for mode, on in given.items() if on]
    if len(chosen) > 1:
        raise ConfigError(
            _(
                "--near, --pairs, --junk, --gone and --intruders are separate "
                "reviews: one per run."
            ),
            _("Run them one after the other: they all save in one file."),
        )
    return chosen[0] if chosen else ReviewMode.BURSTS


def run_mode(run: ReviewRun, mode: ReviewMode, findings: AuditFindings) -> None:
    """Open the page of a mode other than the bursts, serve it, then sum it up.

    Args:
        run: The command line, runtime, decisions file and port.
        mode: `NEAR`, `PAIRS`, `JUNK`, `GONE` or `INTRUDERS`.
        findings: The audit just run.
    """
    runs = {
        ReviewMode.PAIRS: _run_pairs,
        ReviewMode.JUNK: _run_junk,
        ReviewMode.GONE: run_gone,
        ReviewMode.INTRUDERS: run_intruders,
    }
    runs.get(mode, _run_near)(run, findings)


def _run_near(run: ReviewRun, findings: AuditFindings) -> None:
    """`review --near`: the near duplicates, group by group.

    Args:
        run: The command line, runtime, decisions file and port.
        findings: The audit just run.
    """
    runtime = run.runtime
    if not findings.similar.groups:
        runtime.output.success(_("No near duplicates: nothing to review."))
        return
    session = near_reviewing.open_near_review(runtime, findings, run.target)
    tell_near_opened(runtime, session)
    # Opened from the home page: `mh` runs the step *Apply now* ends on (0288).
    start = ReviewStart(run.port, page_apply(runtime))
    end_on_applied(runtime, near_reviewing.serve_near_review(runtime, session, start))
    tell_near_stopped(run.ctx, runtime, session)


def _run_pairs(run: ReviewRun, findings: AuditFindings) -> None:
    """`review --pairs`: the folder pairs of the exact duplicates, one by one.

    Args:
        run: The command line, runtime, decisions file and port.
        findings: The audit just run.
    """
    runtime = run.runtime
    if not findings.plan.decisions:
        runtime.output.success(_("No folder pairs: nothing to review."))
        return
    session = pairs_reviewing.open_pairs_review(runtime, findings, run.target)
    tell_pairs_opened(runtime, session)
    start = ReviewStart(run.port, page_apply(runtime))
    end_on_applied(runtime, pairs_reviewing.serve_pairs_review(runtime, session, start))
    tell_pairs_stopped(run.ctx, runtime, session)


def _run_junk(run: ReviewRun, findings: AuditFindings) -> None:
    """`review --junk`: the photos most likely unwanted, group by group.

    Args:
        run: The command line, runtime, decisions file and port.
        findings: The audit just run.
    """
    runtime = run.runtime
    if not unwanted_reviewing.audit_unwanted(runtime, findings):
        runtime.output.success(_("No photo looks unwanted: nothing to review."))
        return
    session = unwanted_reviewing.open_unwanted_review(runtime, findings, run.target)
    tell_unwanted_opened(runtime, session)
    start = ReviewStart(run.port, page_apply(runtime))
    served = unwanted_reviewing.serve_unwanted_review(runtime, session, start)
    end_on_applied(runtime, served)
    tell_unwanted_stopped(run.ctx, runtime, session)
