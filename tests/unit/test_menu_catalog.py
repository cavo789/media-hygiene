"""The catalog stays exhaustive: every command has its place, every doc link works.

Built like `test_docs_commands.py`: a new verb fails here until it has its entry in
`cli/menu_catalog_*.py`; until then the menu shows it under "Other commands".
"""

from __future__ import annotations

import re

import pytest

from media_hygiene.cli.commands import commands
from media_hygiene.cli.menu_catalog import catalog, named
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.review_modes import ReviewMode
from media_hygiene.services.launcher_host import HOST_COMMANDS
from tests.unit.test_documentation import DOCUMENTATION, anchors

CATALOG = catalog()
ACTIVE = [step for step in CATALOG.steps if not step.planned]
VERBS = {named(step)[0] for step in ACTIVE}
EVERY_VERB = sorted({command[0] for command in commands()} | set(HOST_COMMANDS))


@pytest.mark.parametrize("verb", EVERY_VERB)
def test_every_command_has_a_place_in_the_menu(verb: str) -> None:
    """Every `--help` command and every command `mh` runs itself has an entry."""
    assert verb in VERBS, (
        f"`{verb}` has no place in the menu: add it to `cli/menu_catalog_<space>.py`"
    )


@pytest.mark.parametrize(
    "mode", [mode for mode in ReviewMode if mode is not ReviewMode.BURSTS]
)
def test_every_review_mode_has_its_entry(mode: ReviewMode) -> None:
    """`review --near`, `--pairs`, `--junk`, `--gone`: each its own action."""
    flags = {named(step) for step in ACTIVE}
    assert ("review", f"--{mode.value}") in flags, (
        f"`review --{mode.value}` has no place in the menu: add it to "
        "`cli/menu_catalog_clean_more.py`"
    )


def test_every_entry_names_an_existing_command() -> None:
    """No stale entry after a rename: each verb is a command, unless it is planned."""
    stale = sorted(VERBS - set(EVERY_VERB))
    assert not stale, f"no command named {stale}: rename or remove their entries"


def test_names_are_unique_and_every_group_names_an_entry() -> None:
    """One entry per name; every group lists known names; every entry is shown."""
    names = [step.name for step in CATALOG.steps]
    assert len(names) == len(set(names))
    listed = {
        name for area in CATALOG.areas for group in area.groups for name in group.steps
    }
    assert listed <= set(names)
    assert set(names) <= listed
    assert all(
        step.space in {area.space for area in CATALOG.areas} for step in CATALOG.steps
    )


def test_the_cycle_has_five_stages_then_share_then_three_tools() -> None:
    """Import, clean, sort, find, back up; share, outside the cycle; then the tools."""
    stages = [area.space for area in CATALOG.areas if area.stage]
    assert stages == [Space.IMPORT, Space.CLEAN, Space.SORT, Space.FIND, Space.BACKUP]
    assert [area.stage for area in CATALOG.areas if area.stage] == [1, 2, 3, 4, 5]
    apart = [area.space for area in CATALOG.areas if not area.stage]
    assert apart == [Space.SHARE, Space.HISTORY, Space.REPORTS, Space.SETTINGS]


def test_the_slideshow_is_in_share_and_nowhere_else() -> None:
    """Share holds the slideshow and the album's uses; Find no longer lists it."""
    areas = {area.space: area for area in CATALOG.areas}
    listed = {name for group in areas[Space.SHARE].groups for name in group.steps}
    assert listed == {"slideshow", "share", "album"}
    assert CATALOG.step("album").space is Space.SHARE  # one album, several uses
    assert CATALOG.step("share").space is Space.SHARE
    assert CATALOG.step("slideshow").space is Space.SHARE
    find = {name for group in areas[Space.FIND].groups for name in group.steps}
    assert "slideshow" not in find
    assert "tv" in CATALOG.step("slideshow").keywords


def test_the_fields_appear_in_their_command() -> None:
    """Each field is a `{name}` word of its command; its example fits its pattern."""
    for step in CATALOG.steps:
        for field in step.fields:
            assert f"{{{field.name}}}" in step.command.split(), step.name
            assert re.fullmatch(field.pattern, field.example), step.name


DOCS = sorted(
    {
        (doc.page, doc.en, doc.fr)
        for doc in (
            *(step.doc for step in CATALOG.steps),
            *(area.guide for area in CATALOG.areas),
        )
        if doc is not None
    }
)


@pytest.mark.parametrize(("page", "en", "fr"), DOCS)
def test_every_doc_link_exists_in_both_languages(page: str, en: str, fr: str) -> None:
    """The page in `documentation/en` and `fr`, each with its anchor (GitHub's slug)."""
    for locale, anchor in (("en", en), ("fr", fr)):
        target = f"{locale}/{page}"
        assert (DOCUMENTATION / target.rstrip("/")).with_suffix(".md").is_file(), target
        if anchor:
            assert anchor.removeprefix("#") in anchors(
                (DOCUMENTATION / target.rstrip("/")).with_suffix(".md")
            ), f"{target}{anchor}"


def test_every_active_entry_but_the_extras_has_its_doc() -> None:
    """The page links each action to its chapter; only the planned ones wait."""
    missing = [step.name for step in ACTIVE if step.doc is None]
    assert not missing


def test_phone_free_is_filed_under_clean_and_still_second_from_a_phone() -> None:
    """It erases for good (Clean up), yet reads as step 2 of "From a phone"."""
    step = next(s for s in CATALOG.steps if s.name == "phone-free")
    assert step.space is Space.CLEAN
    areas = {a.space: a for a in CATALOG.areas}
    phone = next(g for g in areas[Space.IMPORT].groups if g.title == "From a phone")
    assert phone.steps[1] == "phone-free"
    further = next(g for g in areas[Space.CLEAN].groups if g.title == "Go further")
    assert "phone-free" in further.steps
