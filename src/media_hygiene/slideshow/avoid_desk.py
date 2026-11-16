"""People kept off the show, from its remote (0825): their photos set "do not show".

Every way into a show (the library's ▶ on this PC or on the TV, an album, the home
page's TV choices) ends on the remote, so the remote is where people are avoided. `GET
/api/avoid`: the people seen on the show's photos (found once, at the first ask), each
with their count, those ticked, how many photos are out for them. `POST /api/avoid`
with `{"names": [...]}` (`"fresh": true`: a name changed, the people found again,
0830): the photos of those people are set out of the show, as by "Do
not show", so they move to the remote's *Will not be shown* group with the name (0831);
the photos a name no longer ticked had set out come back. A photo set out by hand
stays out, one shown again by hand stays in (`why_out`). The TV is told nothing.
Remembered (0834): every show starts with the names of `[slideshow] avoid` ticked,
listed even when on none of its photos; a tick of the PC writes that list
(`avoid_memory`), read back from the disk; a phone's (`PHONE_MARK`) is for this show.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.slideshow.avoid_memory import Remembering, remember

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.slideshow.avoid_seen import Seen
    from media_hygiene.slideshow.desk import Desk

AVOID_PATH: Final = "/api/avoid"
PHONE_MARK: Final = "x-mh-phone"  # set by `Door.local` on a phone's request


def from_phone(request: Request) -> bool:
    """Did a paired phone send it (read-only: for this show only)?

    Args:
        request: The request.

    Returns:
        True for a phone's.
    """
    return PHONE_MARK in request.headers


@dataclass(frozen=True, slots=True)
class Memory:
    """`[slideshow] avoid`: the file, and the names of it that are people known."""

    config_file: Path | None = None
    names: list[str] = field(default_factory=list)


class AvoidAsked(BaseModel):
    """`POST /api/avoid`: the names ticked, all of them each time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    names: tuple[str, ...]
    fresh: bool = False  # a name changed on a photo (0830): find the people again


@dataclass(frozen=True, slots=True)
class AvoidDesk:
    """The people seen on a show's photos, and what the remote ticked."""

    present: Callable[[], dict[str, Seen]]
    ticked: list[str] = field(default_factory=list)
    set_out: set[int] = field(default_factory=set)
    found: list[dict[str, Seen]] = field(default_factory=list)  # once
    memory: Memory = field(default_factory=Memory)

    def people(self) -> dict[str, Seen]:
        """The people of the show, found at the first call.

        Returns:
            By name, alphabetical, the keys of the show's photos they are on.
        """
        if not self.found:
            self.found.append(self.present())
        return self.found[0]

    def start(self, desk: Desk) -> None:
        """Set out the photos of the people remembered, as the show begins.

        Args:
            desk: The show.
        """
        if self.memory.names:
            self._apply(desk, self.memory.names)

    def view(self, request: Request | None = None) -> dict[str, object]:
        """What the remote shows.

        Args:
            request: Who asks: a phone is told its ticks are for this show only.

        Returns:
            The people with their counts (✓ named, ≈ guessed; none: remembered but on
            no photo), those ticked, those remembered, the photos out.
        """
        present = self.people()
        people = [
            {"name": name, "sure": len(on.sure), "guessed": len(on.guessed)}
            for name, on in present.items()
        ]
        people += [
            {"name": name, "sure": 0, "guessed": 0}
            for name in self.memory.names
            if name not in present
        ]
        phone = request is not None and from_phone(request)
        return {
            "people": people,
            "ticked": self.ticked,
            "out": len(self.set_out),
            "remembered": self.memory.names,
            "phone": phone or self.memory.config_file is None,
        }

    def ask(self, desk: Desk, request: Request) -> Response:
        """Set out the photos of the people ticked; on the PC, remember them.

        Args:
            desk: The show, and the pages waiting for a change.
            request: The `POST` of the remote, its JSON the names ticked.

        Returns:
            The view; 400 for a body that is not a list of names, 500 when
            `config.toml` cannot be written.
        """
        try:
            asked = AvoidAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if asked.fresh:  # what the old names set out comes back first
            self._apply(desk, [])
            self.found.clear()
        offered = [*self.people(), *self.memory.names]
        names = [name for name in dict.fromkeys(offered) if name in asked.names]
        self._apply(desk, names)
        config_file = self.memory.config_file
        if config_file is not None and not from_phone(request):
            try:
                kept = remember(config_file, Remembering(tuple(offered), tuple(names)))
            except OSError, ValueError:
                message = _("The people avoided could not be saved in config.toml.")
                return json_response(
                    HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message}
                )
            self.memory.names[:] = [
                name for name in dict.fromkeys(offered) if name in kept
            ]
        return json_response(HTTPStatus.OK, self.view(request))

    def _apply(self, desk: Desk, names: list[str]) -> None:
        """Set out the photos of `names`, back in those of the others."""
        why = desk.why
        for name, seen in self.people().items():
            ticked = name in names
            sure, guessed = seen.sure, seen.guessed - seen.sure
            why.apply(desk.show, f"person:✓ {name}", sure if ticked else frozenset())
            why.apply(desk.show, f"person:≈ {name}", guessed if ticked else frozenset())
        self.set_out.clear()
        self.set_out.update(
            key
            for key, groups in why.held.items()
            if any(group.startswith("person:") for group in groups)
        )
        self.ticked[:] = names
        desk.changes.notify()


def _nobody() -> dict[str, Seen]:
    """No show matched: nobody to avoid.

    Returns:
        Nobody.
    """
    return {}


NO_AVOID: Final = AvoidDesk(_nobody)
