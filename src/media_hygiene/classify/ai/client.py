"""A minimal Ollama client: the standard library's `urllib`, in a thread, with retries.

Two calls: `/api/show` (does the model see images?) and `/api/chat`. A timeout or a
server error is tried again `retries` times; an unknown model or a silent server is a
clear error.
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.errors import AiError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.config.classify_ai import AiSettings

type Json = dict[str, object]
type Poster = Callable[[str, bytes, float], bytes]

SHOW: Final = "/api/show"
CHAT: Final = "/api/chat"
VISION: Final = "vision"
_JSON_HEADERS: Final = {"Content-Type": "application/json"}
_RETRIED: Final = (TimeoutError, ConnectionError, urllib.error.URLError)


def post_json(url: str, body: bytes, timeout: float) -> bytes:
    """POST a JSON body and read the answer.

    Args:
        url: The full URL.
        body: The JSON body.
        timeout: Seconds before giving up.

    Returns:
        The body of the answer.
    """
    request = urllib.request.Request(  # noqa: S310 - the URL is the user's setting
        url, data=body, headers=_JSON_HEADERS, method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as answer:  # noqa: S310
        return bytes(answer.read())


@dataclass(frozen=True, slots=True)
class OllamaClient:
    """Talks to one Ollama server, as `[classify.ai]` says."""

    settings: AiSettings
    post: Poster = post_json

    async def capabilities(self, model: str) -> frozenset[str]:
        """What a model can do, such as `vision` or `completion`.

        Args:
            model: Its name.

        Returns:
            Its capabilities.
        """
        answer = await self.call(SHOW, {"model": model})
        found = answer.get("capabilities")
        return frozenset(map(str, found if isinstance(found, list) else []))

    async def require_vision(self, model: str) -> None:
        """Refuse a model that cannot see images.

        Args:
            model: Its name.

        Raises:
            AiError: It lacks the `vision` capability.
        """
        if VISION not in await self.capabilities(model):
            raise AiError(
                _("The model {model} cannot see images.").format(model=model),
                escape(
                    _("Choose a vision model in [classify.ai] model, e.g. qwen2.5vl.")
                ),
            )

    async def chat(self, request: Mapping[str, object]) -> str:
        """Ask one question and read the answer's text.

        Args:
            request: The `/api/chat` body.

        Returns:
            The content of the answer.

        Raises:
            AiError: The answer holds no message.
        """
        answer = await self.call(CHAT, {**request, "stream": False})
        message = answer.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise AiError(_("The model sent an answer without a message."))
        return content

    async def call(self, path: str, body: Json) -> Json:
        """POST to the server, trying again after a timeout or a server error.

        Args:
            path: `/api/show` or `/api/chat`.
            body: The JSON body.

        Returns:
            The JSON answer.
        """
        url = self.settings.url.rstrip("/") + path
        data = json.dumps(body).encode()
        last = self.settings.retries
        attempt = 0
        while True:
            try:
                raw = await asyncio.to_thread(
                    self.post, url, data, self.settings.timeout_seconds
                )
            except urllib.error.HTTPError as exc:
                exc.close()  # its body is not read: release the connection
                if exc.code < HTTPStatus.INTERNAL_SERVER_ERROR or attempt == last:
                    raise self._refused(exc, body) from exc
            except _RETRIED as exc:
                if attempt == last:
                    raise self._unreachable() from exc
            else:
                return _object(raw)
            attempt += 1

    def _refused(self, error: urllib.error.HTTPError, body: Json) -> AiError:
        """The error of an answer with an HTTP error status.

        Args:
            error: The error.
            body: What was sent (its model is named).

        Returns:
            The error to raise.
        """
        model = str(body.get("model", ""))
        if error.code == HTTPStatus.NOT_FOUND:
            return AiError(
                _("The model {model} is not installed at {url}.").format(
                    model=model, url=self.settings.url
                ),
                _("Install it with: ollama pull {model}").format(model=model),
            )
        return AiError(
            _("The model server {url} answered {status}.").format(
                url=self.settings.url, status=error.code
            )
        )

    def _unreachable(self) -> AiError:
        """The error of a server that does not answer.

        Returns:
            The error to raise, with the Docker networking tip.
        """
        return AiError(
            _("The model server {url} does not answer.").format(url=self.settings.url),
            _(
                "Is Ollama running? On Docker Engine (Linux, WSL), add "
                "--add-host=host.docker.internal:host-gateway and let Ollama listen "
                "beyond 127.0.0.1 (OLLAMA_HOST=0.0.0.0)."
            ),
        )


def _object(raw: bytes) -> Json:
    """Read a JSON object; anything else is an error.

    Args:
        raw: The answer's body.

    Returns:
        The object.

    Raises:
        AiError: The body is not a JSON object.
    """
    try:
        value = json.loads(raw)
    except json.JSONDecodeError, UnicodeDecodeError:
        value = None
    if not isinstance(value, dict):
        raise AiError(_("The model server sent an answer that is not JSON."))
    return value
