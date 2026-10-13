"""`classify` and the words sent to the model: definitions, the interface language."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from tests.support.cli import run

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


def _prompts(fake: FakeOllama, *, with_images: bool) -> list[str]:
    """The text of every chat request sent so far, describe or map."""
    found = []
    for path, body in fake.calls:
        messages = body.get("messages")
        if path != "/api/chat" or not isinstance(messages, list):
            continue
        if bool(messages[0].get("images")) is with_images:
            found.append(str(messages[0]["content"]))
    return found


def test_a_definition_is_sent_to_the_model_and_the_name_is_the_folder(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`Name = definition`: the prompt holds both, the folder is the name alone."""
    config = locations.config_dir / "config.toml"
    defined = '"Holidays and outings = trips and days out, beaches"'
    config.write_text(config.read_text().replace('"Holidays and outings"', defined))
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    (prompt, *_rest) = _prompts(fake, with_images=False)
    assert "Holidays and outings: trips and days out, beaches" in prompt
    assert "\nParties\n" in prompt  # a plain name, unchanged
    assert re.search(r"Holidays and outings\s+│\s+5 ", result.output)
    assert "trips and days out" not in result.output


def test_a_french_interface_describes_in_french_and_again(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """English descriptions are kept for English; French asks again, in French."""
    assert run(cli, "classify").exit_code == 0
    assert run(cli, "classify").exit_code == 0
    assert fake.described() == 9  # English: nothing redone
    assert all("Answer in English" in p for p in _prompts(fake, with_images=True))
    with using(Locale.FR):  # what `--locale fr` installs before the app is built
        french = run(cli, "classify")
    assert french.exit_code == 0, french.output
    assert fake.described() == 18
    assert "Réponds en français" in _prompts(fake, with_images=True)[-1]
