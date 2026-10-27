"""What a search request asks: its body read, or the one-line reason it is refused."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import ValidationError

from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.path_match import refusal
from media_hygiene.search.views import SearchAsked


def read_asked(body: bytes) -> SearchAsked | Response:
    """Read the body of `POST /api/search`.

    Args:
        body: The JSON the page sent.

    Returns:
        The search asked; 400 for a body that is not one, and 400 with the reason
        (`error`) for a *Path contains* regex that does not compile (0426).
    """
    try:
        asked = SearchAsked.model_validate_json(body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    refused = refusal(asked.folder)
    if refused is not None:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": refused})
    return asked
