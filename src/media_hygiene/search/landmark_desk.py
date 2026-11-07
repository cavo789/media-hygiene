"""`POST /api/landmark`: the landmark a photo shows, from the large view (0649).

*📍 Landmark…* (key L) proposes the GeoNames landmarks within `NEAR_M` (nearest first,
with their distance), the OpenStreetMap name if one was fetched, and a free field;
*Wrong name* rejects one. The name goes into the photo's sidecar (the truth), then into
`spots` (source `user`); the answer is what the sidecar says once read back.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.geo.landmarks import near_cells, shared_landmarks
from media_hygiene.geo.point import Point
from media_hygiene.geo.reverse import rounded
from media_hygiene.i18n import _
from media_hygiene.index.spot_user import give_landmark
from media_hygiene.review.serving import json_response
from media_hygiene.services.landmark_sidecars import LandmarkAsked, sidecar_landmark
from media_hygiene.services.place_names import read_names, spot_key

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.landmark_sidecars import LandmarkWriter

LANDMARK_PATH: Final = "/api/landmark"
NEAR_M: Final = 500.0  # 0489: 19.9 % of located photos have one within 500 m
_NAME_MAX: Final = 200
_POSITION: Final = "SELECT latitude, longitude FROM files WHERE path = ?"


class LandmarkPost(BaseModel):
    """What the page asks for one photo: names to propose, one given, one wrong."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["propose", "set", "wrong"] = "propose"
    key: int
    name: str = Field(default="", max_length=_NAME_MAX)


@dataclass(frozen=True, slots=True)
class LandmarkDesk:
    """The index, the sidecars' writer, the cache of online names."""

    index: SearchIndex
    writer: LandmarkWriter
    cache_dir: Path

    async def answer(self, body: bytes) -> Response:
        """Propose names, or write one (or its rejection) into the sidecar.

        Args:
            body: `LandmarkPost`, as JSON.

        Returns:
            The proposals, or the name read back; 400 for a bad body or key, 409
            when nothing can be written.
        """
        try:
            asked = LandmarkPost.model_validate_json(body)
        except ValidationError:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": "body"})
        found = self.index.source_of(asked.key)
        if found is None:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": "key"})
        if asked.action == "propose":
            return json_response(HTTPStatus.OK, self.proposals(found.path))
        name = " ".join(asked.name.split())
        if not name:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": "name"})
        wanted = LandmarkAsked(found.path, name, wrong=asked.action == "wrong")
        try:
            run = await asyncio.to_thread(self.writer.write, wanted)
        except MediaHygieneError as exc:
            said = " ".join(filter(None, (exc.message, exc.tip)))
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        return json_response(HTTPStatus.OK, self._read_back(found.path, run))

    def proposals(self, photo: Path) -> dict[str, object]:
        """The names to offer for a photo, those rejected left out.

        Args:
            photo: The photo.

        Returns:
            `name` (today's), `ours`, `near` (`{name, m}`), `osm`.
        """
        known = sidecar_landmark(photo)
        refused = {each.casefold() for each in known.rejected}
        row = self.index.connection.execute(_POSITION, (str(photo),)).fetchone()
        near: list[dict[str, object]] = []
        osm = ""
        if row is not None and row[0] is not None and row[1] is not None:
            point = Point(row[0], row[1])
            landmarks = shared_landmarks(near_cells((point,)))
            near = [
                {"name": name, "m": metres}
                for name, metres in landmarks.around_far(point, NEAR_M)
                if name.casefold() not in refused
            ]
            osm = read_names(self.cache_dir).get(spot_key(rounded(point)), "")
        return {
            "name": known.name,
            "ours": known.ours,
            "near": near,
            "osm": "" if osm.casefold() in refused else osm,
        }

    def _read_back(self, photo: Path, run: str) -> dict[str, object]:
        """Read the sidecar back, cache its name, say what it holds.

        Args:
            photo: The photo.
            run: The run written; empty when nothing changed.

        Returns:
            `saved` (the line), `name`, `run`.
        """
        known = sidecar_landmark(photo)
        if known.ours:
            give_landmark(self.index.connection, str(photo), known.name)
        if not known.ours:
            said = _("Its sidecar names {name}, set by another application: kept.")
        elif known.name:
            said = _("📍 {name}, read back from its sidecar.")
        else:
            said = _("No landmark in its sidecar now.")
        said = said.format(name=known.name)
        if run:
            said += " " + _("'mh undo {run}' takes it back.").format(run=run)
        return {"saved": said, "name": known.name, "run": run}
