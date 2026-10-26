"""Name a group on the page, keep the name on the next run, find the person by name."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.people.app import PeopleApp
from media_hygiene.review.http import Request
from tests.support.cli import run
from tests.support.faces import coloured

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

JSON = {"host": "127.0.0.1:8766", "content-type": "application/json"}


def flat(text: str) -> str:
    """The output on one line, as the console wraps it."""
    return " ".join(text.split())


def post(app: object, body: dict[str, object]) -> dict[str, object]:
    """Send a change to the page app, return its JSON answer."""
    assert isinstance(app, PeopleApp)
    request = Request("POST", "/api/people", JSON, json.dumps(body).encode())
    answer = asyncio.run(app.handle(request))
    result = json.loads(answer.body)
    assert isinstance(result, dict)
    return result


def state(app: object) -> dict[str, object]:
    """The state of the page app."""
    assert isinstance(app, PeopleApp)
    answer = asyncio.run(app.handle(Request("GET", "/api/groups", JSON)))
    result = json.loads(answer.body)
    assert isinstance(result, dict)
    return result


def keys(section: object) -> list[int]:
    """The face numbers a section shows."""
    assert isinstance(section, dict)
    return [face["key"] for face in section["shown"]]


def name_largest(cli: CliRunner, apps: list[object]) -> dict[str, object]:
    """Run people, name its largest group Chloé on the page."""
    assert run(cli, "people").exit_code == 0
    sections = state(apps[-1])["sections"]
    assert isinstance(sections, list)
    return post(
        apps[-1], {"action": "name", "name": "Chloé", "faces": keys(sections[0])}
    )


def test_a_name_is_saved_read_back_and_kept_by_the_next_run(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """The name lands in config.toml with its comments; the next run shows it."""
    config = locations.config_dir / "config.toml"
    config.write_text("# mine\n[people]\n# my threshold\nmin_face = 10\n")
    saved = name_largest(cli, apps)
    assert (
        saved["saved"] == "Saved in config.toml, read back: Chloé, 4 confirmed faces."
    )
    sections = saved["sections"]
    assert isinstance(sections, list)
    assert sections[0]["name"] == "Chloé"
    assert saved["people"] == ["Chloé"]
    text = config.read_text()
    assert "# mine" in text
    assert "# my threshold" in text
    assert "[[people.person]]" in text
    shown = flat(run(cli, "config").output)
    assert "Chloé (4 faces)" in shown
    assert "0 faces" in shown
    again = flat(run(cli, "people").output)
    assert "Named: Chloé: 4 photos." in again
    assert state(apps[-1])["sections"][0]["name"] == "Chloé"  # type: ignore[index]


def test_reject_and_ignore_are_saved(cli: CliRunner, apps: list[object]) -> None:
    """A face taken out of Chloé is rejected; an ignored group is no longer shown."""
    saved = name_largest(cli, apps)
    sections = saved["sections"]
    assert isinstance(sections, list)
    out = keys(sections[0])[0]
    rejected = post(apps[-1], {"action": "reject", "name": "Chloé", "faces": [out]})
    assert rejected["saved"] == (
        "Saved in config.toml, read back: Chloé, 3 confirmed faces."
    )
    chloe = rejected["sections"][0]  # type: ignore[index]
    assert out not in keys(chloe)
    assert chloe["faces"] == len(keys(sections[0])) - 1
    other = keys(sections[1])
    ignored = post(apps[-1], {"action": "ignore", "faces": other})
    assert ignored["saved"] == "Saved in config.toml, read back: 3 faces ignored."
    assert ignored["ignored"] == 1
    refused = post(apps[-1], {"action": "name", "name": " ", "faces": other})
    assert refused["error"] == "Not saved: type a name first."


def test_attributed_faces_are_confirmed_a_page_at_a_time(
    cli: CliRunner, apps: list[object]
) -> None:
    """Half a group named: the rest is attributed; confirmed, it moves to verified."""
    assert run(cli, "people").exit_code == 0
    group = keys(state(apps[-1])["sections"][0])  # type: ignore[index]
    half = len(group) // 2
    named = post(apps[-1], {"action": "name", "name": "Chloé", "faces": group[:half]})
    verified, attributed = named["sections"][:2]  # type: ignore[index]
    assert (verified["name"], verified["verified"]) == ("Chloé", True)
    assert sorted(keys(verified)) == sorted(group[:half])
    assert (attributed["name"], attributed["verified"]) == ("Chloé", False)
    assert sorted(keys(attributed)) == sorted(group[half:])
    confirmed = post(
        apps[-1], {"action": "name", "name": "Chloé", "faces": keys(attributed)}
    )
    assert confirmed["saved"] == (
        f"Saved in config.toml, read back: Chloé, {len(group)} confirmed faces."
    )
    sections = confirmed["sections"]
    assert isinstance(sections, list)
    assert sorted(keys(sections[0])) == sorted(group)
    assert all(section["name"] != "Chloé" for section in sections[1:])


def test_search_finds_the_person_by_name(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Chloé holidays` mixes sources; `person:chloe` folds accents; unknown: said."""
    monkeypatch.setenv("COLUMNS", "200")
    name_largest(cli, apps)
    assert run(cli, "tags").exit_code == 0
    both = flat(run(cli, "search", "Chloé", "Holidays").output)
    assert "2 files found." in both
    assert "IMG_0.png" in both
    assert "IMG_1.png" not in both
    named = flat(run(cli, "search", "person:chloe").output)
    assert "4 files found." in named
    unknown = flat(run(cli, "search", "person:Manon").output)
    assert 'Nobody is named "Manon" yet' in unknown


def test_forget_asks_before_deleting_the_names(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Without a yes the names stay; with one they go, read back from the file."""
    name_largest(cli, apps)
    kept = flat(run(cli, "people", "--forget").output)
    assert "The names stay in config.toml" in kept
    assert 'name = "Chloé"' in (locations.config_dir / "config.toml").read_text()
    name_largest(cli, apps)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "media_hygiene.console.output.Output.confirm", lambda _self, _question: True
        )
        gone = flat(run(cli, "people", "--forget").output)
    assert "Read back from config.toml: 0 names, 0 faces ignored." in gone
    # The default file's comments hold "Chloé" as an example: only the entry is gone.
    assert 'name = "Chloé"' not in (locations.config_dir / "config.toml").read_text()


def test_a_face_too_small_for_the_page_is_named_by_nobody(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Page, `people` counts and `search` agree: a 30 px face is no one's (0316)."""
    coloured(locations.data_dir / "c" / "Holidays" / "tiny.png", 0, (30, 30))
    assert run(cli, "audit").exit_code == 0
    saved = name_largest(cli, apps)
    verified = saved["sections"][0]  # type: ignore[index]
    assert (verified["name"], verified["photos"]) == ("Chloé", 4)
    assert "Chloé: 4 photos" in flat(run(cli, "people").output)
    assert run(cli, "tags").exit_code == 0
    found = flat(run(cli, "search", "person:chloe").output)
    assert "4 files found." in found
    assert "tiny.png" not in found


def test_a_verified_section_comes_folded_as_a_strip_its_sample_on_opening(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verified: a strip of a few faces; `/api/sample/<n>` sends the sample (0323)."""
    monkeypatch.setattr("media_hygiene.people.views.STRIP", 2)
    saved = name_largest(cli, apps)
    verified, other = saved["sections"][:2]  # type: ignore[index]
    assert (verified["verified"], verified["folded"], verified["faces"]) == (
        True,
        True,
        4,
    )
    assert len(keys(verified)) == 2
    assert other["folded"] is False
    app = apps[-1]
    assert isinstance(app, PeopleApp)
    first = keys(verified)[0]
    request = Request("GET", f"/api/sample/{first}", JSON)
    sample = json.loads(asyncio.run(app.handle(request)).body)["shown"]
    assert len(sample) == 4
    unknown = Request("GET", "/api/sample/x", JSON)
    assert json.loads(asyncio.run(app.handle(unknown)).body) == {"shown": []}
