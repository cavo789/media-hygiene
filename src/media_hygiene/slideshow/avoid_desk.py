"""People kept off the show, from its remote (0825): their photos set "do not show".

Every way into a show (the library's ▶ on this PC or on the TV, an album, the home
page's TV choices) ends on the remote, so the remote is where people are avoided. `GET
/api/avoid`: the people seen on the show's photos (found once, at the first ask), each
with their count, those ticked, how many photos are out for them. `POST /api/avoid`
with `{"names": [...]}`: the photos of those people are set out of the show, as by "Do
not show", so they stay visible on the remote, greyed; the photos a name no longer
ticked had set out come back. A photo set out by hand stays out. Nothing is stored:
the show in memory only, and the TV is told nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.slideshow.desk import Desk

AVOID_PATH: Final = "/api/avoid"


class AvoidAsked(BaseModel):
    """`POST /api/avoid`: the names ticked, all of them each time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Seen:
    """Where a person is in a show: the keys with a face named theirs, those guessed."""

    sure: frozenset[int] = frozenset()
    guessed: frozenset[int] = frozenset()

    @property
    def keys(self) -> frozenset[int]:
        """Every key of theirs, sure or guessed."""
        return self.sure | self.guessed


@dataclass(frozen=True, slots=True)
class AvoidDesk:
    """The people seen on a show's photos, and what the remote ticked."""

    present: Callable[[], dict[str, Seen]]
    ticked: list[str] = field(default_factory=list)
    set_out: set[int] = field(default_factory=set)
    found: list[dict[str, Seen]] = field(default_factory=list)  # once

    def people(self) -> dict[str, Seen]:
        """The people of the show, found at the first call.

        Returns:
            By name, alphabetical, the keys of the show's photos they are on.
        """
        if not self.found:
            self.found.append(self.present())
        return self.found[0]

    def view(self) -> dict[str, object]:
        """What the remote shows.

        Returns:
            The people with their counts (✓ named, ≈ guessed), those ticked, the
            photos out.
        """
        people = [
            {"name": name, "sure": len(on.sure), "guessed": len(on.guessed)}
            for name, on in self.people().items()
        ]
        return {"people": people, "ticked": self.ticked, "out": len(self.set_out)}

    def ask(self, desk: Desk, body: bytes) -> Response:
        """Set out the photos of the people ticked, back in those of the others.

        Args:
            desk: The show, and the pages waiting for a change.
            body: The JSON the remote sent.

        Returns:
            The view; 400 for a body that is not a list of names.
        """
        try:
            asked = AvoidAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        people = self.people()
        names = [name for name in people if name in asked.names]
        wanted: frozenset[int] = frozenset().union(
            *(people[name].keys for name in names)
        )
        show = desk.show
        for key in sorted(self.set_out - wanted):
            show.set_out(key, out=False)
        added = {key for key in wanted - self.set_out if key not in show.skipped}
        for key in sorted(added):
            show.set_out(key, out=True)
        self.set_out.intersection_update(wanted)
        self.set_out.update(added)
        self.ticked[:] = names
        desk.changes.notify()
        return json_response(HTTPStatus.OK, self.view())


def _nobody() -> dict[str, Seen]:
    """No show matched: nobody to avoid.

    Returns:
        Nobody.
    """
    return {}


NO_AVOID: Final = AvoidDesk(_nobody)
