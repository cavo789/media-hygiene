"""The two pages of the slideshow: the remote (phone, PC) and the screen (TV)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.review.http import NO_REFERRER
from media_hygiene.review.videos import NEAR_POLICY

if TYPE_CHECKING:
    from media_hygiene.i18n.live import Page


@dataclass(frozen=True, slots=True)
class ShowPages:
    """The two pages: the remote (phone, PC) and the screen (TV)."""

    remote: Page
    screen: Page
    policy: str = NEAR_POLICY  # the remote's: allows `[places] tiles` when set (0449)
    referrer: str = NO_REFERRER
