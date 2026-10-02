"""The choices the sort review page sends: their JSON bodies, and what each one does."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.page_values import EventValue
from media_hygiene.classify.workbook.validation import folder_of
from media_hygiene.review.sort_files import SendFiles

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.review.sort_session import SortSession
    from media_hygiene.review.sort_state import EventView

EVENT_PATH: Final = "/api/event"
FILES_PATH: Final = "/api/files"
FORGET_PATH: Final = "/api/forget"


class _Frozen(BaseModel):
    """A request body: frozen, nothing more than its fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class _EventIn(_Frozen):
    """`POST /api/event`: an event's name and category, or "stay"."""

    event: str
    name: str = ""
    category: str = ""
    stay: bool = False


class _FilesIn(_Frozen):
    """`POST /api/files`: photos of an event, and where they go."""

    event: str
    rows: tuple[str, ...]
    category: str = ""
    stay: bool = False


class _ForgetIn(_Frozen):
    """`POST /api/forget`: photos whose choice is taken back; none: the event's."""

    event: str
    rows: tuple[str, ...] = ()


def _event(session: SortSession, body: bytes) -> EventView:
    """Name an event, give it a category, or leave it in place.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        The event, as chosen.
    """
    asked = _EventIn.model_validate_json(body)
    value = EventValue(
        name=folder_of(asked.name.strip()),
        category="" if asked.stay else folder_of(asked.category.strip()),
        stay=asked.stay,
    )
    return session.choose_event(asked.event, value)


def _files(session: SortSession, body: bytes) -> EventView:
    """Send photos of an event to another category, or leave them in place.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        The event, as chosen.
    """
    asked = _FilesIn.model_validate_json(body)
    category = "" if asked.stay else folder_of(asked.category.strip())
    return session.send(SendFiles(asked.event, asked.rows, category, asked.stay))


def _forget(session: SortSession, body: bytes) -> EventView:
    """Take back the page's choice of photos, or of the event.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        The event, as chosen now.
    """
    asked = _ForgetIn.model_validate_json(body)
    return session.forget(asked.event, asked.rows)


CHOICES: Final[Mapping[str, Callable[[SortSession, bytes], EventView]]] = (
    MappingProxyType(
        {
            EVENT_PATH: _event,
            FILES_PATH: _files,
            FORGET_PATH: _forget,
        }
    )
)
