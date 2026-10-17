"""A camera's clock set right by `[[classify.clocks]]`, and dates in the future doubted.

The shift applies to the EXIF date of the files whose make and model match the rule,
on the camera's own (wrong) days only. Nothing is written into a photo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.dates import DOUBTED, exif_date
from media_hygiene.classify.dating_models import DateSource
from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.config.clock_settings import parse_shift

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date, datetime, timedelta

    from media_hygiene.classify.dating_models import Dating
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.calendar import OneOff
    from media_hygiene.config.clock_settings import ClockRule


@dataclass(frozen=True, slots=True)
class Clock:
    """One rule, read once: which camera, which days, how much."""

    camera: re.Pattern[str]
    days: OneOff
    shift: timedelta
    note: tuple[str, str]  # (shift, camera) as written, shown in the workbook

    def covers(self, file: MediaInput, day: date) -> bool:
        """Tell whether the rule covers a file's day, as the `camera` rule matches.

        Args:
            file: The file: its make and model.
            day: Its EXIF day, as the camera wrote it.

        Returns:
            True when the day is in the rule's range and the camera matches.
        """
        if not self.days.contains(day):
            return False
        metadata = file.metadata
        names = (file.camera, *((metadata.make, metadata.model) if metadata else ()))
        return bool(re.search(self.camera, " ".join(name for name in names if name)))


def clocks_of(rules: Sequence[ClockRule]) -> tuple[Clock, ...]:
    """Read the rules of `[[classify.clocks]]` once per run.

    Args:
        rules: The rules, already validated.

    Returns:
        Them, ready to apply.
    """
    return tuple(
        Clock(
            re.compile(rule.camera),
            parse_one_off(rule.dates),
            parse_shift(rule.shift),
            (rule.shift.strip(), rule.camera),
        )
        for rule in rules
    )


def clock_of(file: MediaInput, when: datetime, clocks: Sequence[Clock]) -> Clock | None:
    """Find the rule that covers a file's EXIF date.

    Args:
        file: The file: its make and model.
        when: Its EXIF date, as the camera wrote it.
        clocks: The rules.

    Returns:
        The first rule of its camera whose days hold the date, or None.
    """
    day = when.date()
    return next((clock for clock in clocks if clock.covers(file, day)), None)


def set_right(file: MediaInput, clocks: Sequence[Clock]) -> datetime | None:
    """The EXIF date of a file, its camera's clock set right.

    Args:
        file: The file.
        clocks: The rules.

    Returns:
        The date, shifted when a rule covers it; None without an EXIF date.
    """
    when = exif_date(file.taken_at)
    if when is None:
        return None
    clock = clock_of(file, when, clocks)
    return when if clock is None else when + clock.shift


def shifted(dating: Dating, file: MediaInput, clocks: Sequence[Clock]) -> Dating:
    """Apply the rule covering an EXIF dating, and say which.

    Args:
        dating: The date the chain found.
        file: Its file.
        clocks: The rules.

    Returns:
        The dating, shifted and noted when a rule covers it; else unchanged.
    """
    if dating.source is not DateSource.EXIF or not clocks:
        return dating
    clock = clock_of(file, dating.when, clocks)
    if clock is None:
        return dating
    return replace(dating, when=dating.when + clock.shift, clock=clock.note)


def doubt_future(dating: Dating, today: date) -> Dating:
    """Doubt a date after the day of the run: a clock set wrong, to check.

    Args:
        dating: The date the chain found.
        today: The day of the run.

    Returns:
        The dating, doubted and flagged when it is in the future; else unchanged.
    """
    if dating.source is DateSource.MTIME or dating.when.date() <= today:
        return dating
    return replace(dating, confidence=min(dating.confidence, DOUBTED), future=True)
