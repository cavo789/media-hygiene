"""Every command of the CLI has its page, in both languages, with its `--help`."""

from __future__ import annotations

import pytest

from media_hygiene.cli.commands import commands
from tests.support.docs.pages import specifications
from tests.support.docs.scenario import CAPTURES
from tests.unit.test_documentation import DOCUMENTATION, LOCALES

NAMES = sorted(command[0] for command in commands())


@pytest.mark.parametrize("locale", LOCALES)
def test_every_command_has_its_page(locale: str) -> None:
    """One page per command, and no page for a command that does not exist."""
    pages = {page.stem for page in (DOCUMENTATION / locale / "commands").glob("*.md")}
    assert pages == set(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_every_page_shows_the_help_of_its_command(name: str) -> None:
    """The page captures the command's own `--help`, which the scenario produces."""
    capture = f"help-{name}.txt"
    assert capture in CAPTURES
    for locale in LOCALES:
        page = DOCUMENTATION / locale / "commands" / f"{name}.md"
        assert capture in specifications(page)


@pytest.mark.parametrize("locale", LOCALES)
def test_the_reference_links_every_command(locale: str) -> None:
    """The commands reference lists every command, linked to its page."""
    reference = (DOCUMENTATION / locale / "reference-commands.md").read_text("utf-8")
    missing = [name for name in NAMES if f"(commands/{name}.md)" not in reference]
    assert not missing
