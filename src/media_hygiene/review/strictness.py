"""The thresholds of a review, tried on its page, then kept in `config.toml` (0537).

Each page tries a value (`POST /api/strictness`): the proposals are computed again in
memory, the choices already made stay, and the page says which photos enter or leave
next to what the file holds. Only `save` writes, and the answer is the file read back.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.places.toml_edit import document_of, table_of, write_document
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.strictness_file import saved_values

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

    from media_hygiene.places.toml_edit import AnyTable
    from media_hygiene.review.http import Request

STRICTNESS_PATH: Final = "/api/strictness"
# Names said on the page, per direction: the count says the rest.
NAMES_SHOWN: Final = 12
_GET, _POST = "GET", "POST"

type Value = float | bool


class _Asked(BaseModel):
    """`POST /api/strictness`: the values to try, and whether to keep them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    values: dict[str, bool | float]
    save: bool = False


@dataclass(frozen=True, slots=True)
class ThresholdPlace:
    """Where a page's thresholds live: the file, the section, the keys it may change."""

    config_file: Path
    section: tuple[str, ...]
    names: tuple[str, ...]


class Strictness[S: BaseModel]:
    """The thresholds of one review: those tried, those in the file."""

    def __init__(
        self,
        place: ThresholdPlace,
        settings: S,
        apply: Callable[[S], Mapping[str, str]],
    ) -> None:
        """Start on the settings of the run.

        Args:
            place: Where they are saved.
            settings: The section's settings.
            apply: Applies settings to the review; returns what it then proposes
                (file name by path).
        """
        self._place = place
        self._tried = settings
        self._saved = settings
        self._apply = apply

    def current(self) -> dict[str, object]:
        """Say the values tried and those of the file.

        Returns:
            `values` and `saved`, by key.
        """
        return {"values": self._of(self._tried), "saved": self._of(self._saved)}

    def tune(self, values: Mapping[str, Value], *, save: bool) -> dict[str, object]:
        """Try values on the review; with `save`, keep them and read the file back.

        Args:
            values: The new values, by key.
            save: Write them to `config.toml`.

        Returns:
            `current()`, and the names entering and leaving the proposals.

        Raises:
            ValueError: A key this page does not change, or a value out of bounds.
        """
        unknown = set(values) - set(self._place.names)
        if unknown:
            raise ValueError(", ".join(sorted(unknown)))
        kind = type(self._saved)
        tried = kind.model_validate(self._tried.model_dump() | dict(values))
        before = self._apply(self._saved)
        after = self._apply(tried)
        self._tried = tried
        answer: dict[str, object] = {
            "entered": _names(after, before),
            "left": _names(before, after),
        }
        if save:
            read = self._write(tried)
            self._saved = kind.model_validate(self._saved.model_dump() | read)
            answer["proof"] = read
        return self.current() | answer

    def _write(self, tried: S) -> dict[str, object]:
        """Write the values that changed, and read them back from the disk.

        Args:
            tried: The settings to keep.

        Returns:
            Those values, as the file holds them.
        """
        new, old = self._of(tried), self._of(self._saved)
        changed = {key: value for key, value in new.items() if value != old[key]}
        place = self._place
        document = document_of(place.config_file)
        table: TOMLDocument | AnyTable = document
        for name in place.section:
            table = table_of(table, name)
        for key, value in changed.items():
            table[key] = value
        write_document(place.config_file, document)
        return saved_values(place.config_file, place.section, changed)

    def _of(self, settings: S) -> dict[str, object]:
        """The page's keys in these settings.

        Args:
            settings: The settings.

        Returns:
            The values, by key.
        """
        every = settings.model_dump()
        return {name: every[name] for name in self._place.names}


def _names(first: Mapping[str, str], second: Mapping[str, str]) -> dict[str, object]:
    """Who is in the first listing and not in the second.

    Args:
        first: File name by path.
        second: File name by path.

    Returns:
        Their `count`, and the first `names`.
    """
    found = sorted(path for path in first if path not in second)
    return {
        "count": len(found),
        "names": [first[path] for path in found[:NAMES_SHOWN]],
    }


def strictness_route[S: BaseModel](
    request: Request, strictness: Strictness[S]
) -> Response:
    """Answer `GET` and `POST /api/strictness`.

    Args:
        request: The request, from the page.
        strictness: The thresholds of the review.

    Returns:
        The values; 400 for a body that is no choice, 422 with its reason for a refused
        value, 500 when the file cannot be written.
    """
    if request.method == _GET:
        return json_response(HTTPStatus.OK, strictness.current())
    if request.method != _POST:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        asked = _Asked.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    try:
        return json_response(
            HTTPStatus.OK, strictness.tune(asked.values, save=asked.save)
        )
    except (ValueError, TypeError, OSError) as exc:
        return save_refused(exc)
