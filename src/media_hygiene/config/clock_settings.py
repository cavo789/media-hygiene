"""`[[classify.clocks]]` — a camera's clock off by an hour or a day, set right.

The shift is written once here, never into a photo: `classify` and `tags` read the
camera's EXIF dates through it.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Annotated, Final, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.i18n import _

_SHIFT: Final = re.compile(r"([+-])(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?")


class ClockRule(BaseModel):
    """One camera, the days its clock was wrong, and by how much.

    `camera` is a regular expression searched in the make and model (as the `camera`
    rule); `dates` the camera's own, wrong, days; `shift` what to add to them.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    camera: str = Field(min_length=1)
    dates: str = Field(min_length=1)  # `2010-07-01..2010-07-15`
    shift: str = Field(min_length=1)  # `+1h`, `-1d2h`, `+30m`

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        """Refuse a rule that cannot work, naming it.

        Returns:
            The rule, unchanged.

        Raises:
            ValueError: The camera, the dates or the shift cannot be read.
        """
        try:
            re.compile(self.camera)
            parse_one_off(self.dates)
            parse_shift(self.shift)
        except (ValueError, re.error) as exc:
            message = _("clock '{camera}': {reason}")
            raise ValueError(message.format(camera=self.camera, reason=exc)) from exc
        return self


def parse_shift(text: str) -> timedelta:
    """Read a shift: `+` or `-`, then days `d`, hours `h`, minutes `m`.

    Args:
        text: E.g. `+1h`, `-1d2h`, `+45m`.

    Returns:
        The shift.

    Raises:
        ValueError: The text is not written so, or shifts nothing.
    """
    found = _SHIFT.fullmatch(text.strip())
    if found is None or not any(found.groups()[1:]):
        message = _("'{text}' is not a shift such as +1h, -1d or +1d2h30m")
        raise ValueError(message.format(text=text))
    sign, days, hours, minutes = found.groups()
    shift = timedelta(
        days=int(days or 0), hours=int(hours or 0), minutes=int(minutes or 0)
    )
    if not shift:
        message = _("'{text}' shifts nothing").format(text=text)
        raise ValueError(message)
    return -shift if sign == "-" else shift


def check_clocks(rules: tuple[ClockRule, ...]) -> tuple[ClockRule, ...]:
    """Refuse two rules of one camera whose days overlap, naming both.

    Args:
        rules: The rules.

    Returns:
        Them, unchanged.

    Raises:
        ValueError: Two rules of the same `camera` share a day.
    """
    for index, rule in enumerate(rules):
        for other in rules[index + 1 :]:
            if rule.camera != other.camera:
                continue
            if parse_one_off(rule.dates).overlaps(parse_one_off(other.dates)):
                message = _("clock '{camera}': {first} and {second} overlap")
                message = message.format(
                    camera=rule.camera, first=rule.dates, second=other.dates
                )
                raise ValueError(message)
    return rules


ClockRules = Annotated[tuple[ClockRule, ...], AfterValidator(check_clocks)]
