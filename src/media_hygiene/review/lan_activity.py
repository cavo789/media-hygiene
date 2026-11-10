"""What each paired phone did, per day: pages opened, pictures viewed (0683).

Counts only, never which page nor which photo, kept `ACTIVITY_DAYS` in
`/lan/activity.json`: the PC's card answers "did someone look at the photos while I was
away?". Counted in memory and written every `FLUSH_EVERY` at most (a draft renamed
over the file, 0600), never once per picture: a stop loses at most those last minutes.
Each write merges with the file as on disk (a `/lan` restored from an older copy adds
its days), drops the days too old and the phones no longer paired.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.review.lan_phone_care import now_utc, touch
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.videos import VIDEO_PREFIX
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.folders import BROWSE_PATH
from media_hygiene.search.views import ORIGINAL_PREFIX, PREVIEW_PREFIX

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.review.lan_phone_model import Phone
    from media_hygiene.review.lan_phones import PhoneBook

ACTIVITY_FILE: Final = "activity.json"
ACTIVITY_DAYS: Final = 30
FLUSH_EVERY: Final = timedelta(minutes=5)
_PAGES: Final = frozenset({PAGE_PATH, SEARCH_PAGE_PATH, BROWSE_PATH})
# A photo or a video opened large; the thumbnails of a grid are not counted.
_PICTURES: Final = (PREVIEW_PREFIX, ORIGINAL_PREFIX, VIDEO_PREFIX)

type Days = dict[str, dict[str, int]]  # day → {"pages": n, "pictures": n}


class ActivityFile(BaseModel):
    """The content of `activity.json`: per phone `id`, per day, two counts."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    devices: dict[str, Days] = Field(default_factory=dict)


def _kind(request: Request) -> str | None:
    """What a request counts as.

    Args:
        request: A paired phone's request.

    Returns:
        `pages`, `pictures`, or None for anything else.
    """
    if request.method != "GET":
        return None
    if request.path in _PAGES:
        return "pages"
    return "pictures" if request.path.startswith(_PICTURES) else None


class Activity:
    """This run's counts, in memory, written to `/lan/activity.json` now and then."""

    __slots__ = ("_book", "_clock", "_counts", "_flushed")

    def __init__(
        self, book: PhoneBook, clock: Callable[[], datetime] = now_utc
    ) -> None:
        """Start empty.

        Args:
            book: The phones' file, beside which `activity.json` lives.
            clock: Now, in UTC (a test's own).
        """
        self._book = book
        self._clock = clock
        self._counts: defaultdict[str, Days] = defaultdict(dict)
        self._flushed = clock()

    def saw(self, phone: Phone, request: Request) -> None:
        """Note a paired phone's request: its last seen, and what it counts as.

        Args:
            phone: The phone, as just read from the file.
            request: Its request.
        """
        now = self._clock()
        touch(self._book, phone, (request.peer, now))
        kind = _kind(request)
        if kind is not None:
            day = self._counts[phone.id].setdefault(now.date().isoformat(), {})
            day[kind] = day.get(kind, 0) + 1
        if now - self._flushed >= FLUSH_EVERY:
            self.flush()

    def _read(self) -> dict[str, Days]:
        """The file merged with this run's counts, the old days and old phones out.

        Returns:
            Per phone `id`, per day, the counts.
        """
        try:
            on_disk = ActivityFile.model_validate_json(self._path().read_bytes())
            merged = {key: dict(days) for key, days in on_disk.devices.items()}
        except OSError, ValidationError:
            merged = {}
        for key, days in self._counts.items():
            mine = merged.setdefault(key, {})
            for day, counts in days.items():
                was = mine.get(day, {})
                mine[day] = {
                    k: was.get(k, 0) + counts.get(k, 0) for k in {*was, *counts}
                }
        oldest = (self._clock() - timedelta(days=ACTIVITY_DAYS)).date().isoformat()
        paired = {p.id for p in (*self._book.listed(), *self._book.tvs().listed())}
        return {
            key: {day: c for day, c in days.items() if day > oldest}
            for key, days in merged.items()
            if key in paired
        }

    def _path(self) -> Path:
        """Where the counts are kept.

        Returns:
            `activity.json` beside `phones.json`.
        """
        return self._book.path.parent / ACTIVITY_FILE

    def flush(self) -> None:
        """Write the counts (merged, pruned) and start counting again from zero."""
        merged = self._read()
        draft = self._path().with_suffix(".json.new")
        try:
            draft.write_text(ActivityFile(devices=merged).model_dump_json(), "utf-8")
            draft.chmod(0o600)
            draft.replace(self._path())
        except OSError:
            return  # kept in memory: the next write tries again
        self._counts.clear()
        self._flushed = self._clock()

    def of(self, phone_id: str) -> list[dict[str, object]]:
        """A phone's days, newest first, for the PC's card.

        Args:
            phone_id: Its `id`.

        Returns:
            Each day with `day`, `pages` and `pictures`.
        """
        days = self._read().get(phone_id, {})
        return [
            {"day": day, "pages": c.get("pages", 0), "pictures": c.get("pictures", 0)}
            for day, c in sorted(days.items(), reverse=True)
        ]
