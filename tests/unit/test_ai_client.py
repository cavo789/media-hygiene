"""The Ollama client: retries, clear errors, the vision check (no server needed)."""

from __future__ import annotations

import asyncio
import io
import json
import urllib.error
from email.message import Message

import pytest

from media_hygiene.classify.ai.client import OllamaClient, post_json
from media_hygiene.config.classify_ai import AiSettings
from media_hygiene.errors import AiError

SETTINGS = AiSettings(url="http://ollama:11434/", model="m", retries=2)


class Script:
    """A poster answering from a list: bytes are answers, exceptions are raised."""

    def __init__(self, *steps: bytes | Exception) -> None:
        """Keep the steps."""
        self.steps = list(steps)
        self.urls: list[str] = []

    def __call__(self, url: str, _body: bytes, _timeout: float) -> bytes:
        """Play the next step."""
        self.urls.append(url)
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def http_error(code: int) -> urllib.error.HTTPError:
    """An HTTP error with this status."""
    return urllib.error.HTTPError("u", code, "x", Message(), io.BytesIO())


def chat(script: Script, settings: AiSettings = SETTINGS) -> str:
    """Ask one question through the script."""
    return asyncio.run(OllamaClient(settings, script).chat({"model": "m"}))


ANSWER = json.dumps({"message": {"content": "hi"}}).encode()


def test_timeouts_and_server_errors_are_tried_again() -> None:
    """Two failures, then the answer: the URL is joined without a double slash."""
    script = Script(TimeoutError(), http_error(503), ANSWER)
    assert chat(script) == "hi"
    assert script.urls == ["http://ollama:11434/api/chat"] * 3


def test_a_server_that_never_answers_names_the_docker_fix() -> None:
    """After the last retry: the URL, and the --add-host tip."""
    script = Script(*(urllib.error.URLError("refused") for _ in range(3)))
    with pytest.raises(AiError) as caught:
        chat(script)
    assert "does not answer" in caught.value.message
    assert "--add-host" in (caught.value.tip or "")


def test_an_unknown_model_says_how_to_install_it() -> None:
    """404 is not retried."""
    with pytest.raises(AiError) as caught:
        chat(Script(http_error(404)))
    assert "ollama pull m" in (caught.value.tip or "")


def test_other_refusals_and_nonsense_are_errors() -> None:
    """A 400, a last 500, a body that is not JSON, an answer without a message."""
    no_retry = SETTINGS.model_copy(update={"retries": 0})
    for script in (
        Script(http_error(400)),
        Script(http_error(500)),
        Script(b"<html>"),
        Script(b"[1]"),
        Script(b"{}"),
    ):
        with pytest.raises(AiError):
            chat(script, no_retry)


def test_a_model_without_vision_is_refused() -> None:
    """`/api/show` must list `vision`."""
    blind = Script(json.dumps({"capabilities": ["completion"]}).encode())
    with pytest.raises(AiError) as caught:
        asyncio.run(OllamaClient(SETTINGS, blind).require_vision("m"))
    assert "cannot see images" in caught.value.message
    seeing = Script(json.dumps({"capabilities": ["vision"]}).encode())
    asyncio.run(OllamaClient(SETTINGS, seeing).require_vision("m"))
    assert asyncio.run(OllamaClient(SETTINGS, Script(b"{}")).capabilities("m")) == (
        frozenset()
    )


def test_the_real_poster_reaches_a_closed_port_with_an_error() -> None:
    """The standard library raises what the client retries."""
    with pytest.raises(urllib.error.URLError):
        post_json("http://127.0.0.1:9/api/show", b"{}", 1)
