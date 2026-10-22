"""The home page (0266): its state, its template, its assets, the words of a form.

The state in each situation of the mockup; the template with no undefined value; the
assets folder only; the words of a form checked, then handed to `mh` in a one-shot file.
"""

from __future__ import annotations

import asyncio
import json
import re
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest
from jinja2 import StrictUndefined

from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.docker_run import Shell
from media_hygiene.review.ending import STOPPED, Ending
from media_hygiene.review.home_app import HomeApp
from media_hygiene.review.home_assets import ASSETS_DIR, asset_file, asset_response
from media_hygiene.review.home_fields import STEP_FILE_NAME, FieldError, checked_words
from media_hygiene.review.home_step import StepDoor, shown, step_response
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
from media_hygiene.review.http import ContentType, Request
from media_hygiene.review.presence import Presence
from media_hygiene.services import home
from media_hygiene.services.home_audit import HomeAudit
from media_hygiene.services.launcher import launcher_script, render_script
from tests.support.home_states import SITUATIONS
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_launch import COMMANDS

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.layers import Layer
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.services.runtime import Runtime

# Never old: a quarantine of the fixtures is not proposed for its age, whatever the day.
_NEVER_OLD: Final[Layer] = {"clean": {"purge_hint_days": 100_000}}
_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}

# The next step of each situation, and the mark of the stages it changes.
_EXPECTED: Final = {
    "first run": ("audit", {"clean": "here"}),
    "audit done": ("clean", {"clean": "here", "import": "todo"}),
    "after clean": ("import", {"import": "here", "clean": "todo"}),
    "after import": ("purge", {"import": "done", "clean": "here"}),
    "quarantine freed": (None, {"clean": "done"}),
    "proposal waiting": ("sort", {"sort": "here", "clean": "done"}),
    "everything sorted": (None, {"sort": "done"}),
}


def _state(tmp_path: Path, situation: str) -> HomeState:
    """The state of the page in one situation of the mockup."""
    runtime = make_runtime(make_locations(tmp_path), _NEVER_OLD)
    SITUATIONS[situation](runtime)
    return home_state(runtime)


@pytest.mark.parametrize("situation", list(SITUATIONS))
def test_each_situation_gives_its_next_step_and_marks(
    tmp_path: Path, situation: str
) -> None:
    """The next step, its number in `mh menu`, and the stages it marks."""
    state = _state(tmp_path, situation)
    name, marks = _EXPECTED[situation]
    if name is None:
        assert state.proposed is None
    else:
        assert state.proposed is not None
        assert state.proposed.name == name
        action = state.action(name)
        assert action is not None
        assert action.proposed
        assert action.available
        assert action.number == state.proposed.number
        assert state.command_of(state.proposed.number) == state.proposed.command
    spaces = {space.id: space for space in state.spaces}
    for space, mark in marks.items():
        assert spaces[space].mark == mark, space
    assert [space.id for space in state.spaces if space.stage] == [
        "import",
        "clean",
        "sort",
        "find",
        "backup",
    ]
    assert all(space.mark != "here" for space in state.spaces if space.id not in marks)


def test_the_counts_and_the_reasons_come_from_the_tool_folders(tmp_path: Path) -> None:
    """The badges and tiles count; an action that cannot run says why."""
    state = _state(tmp_path, "audit done")
    spaces = {space.id: space for space in state.spaces}
    assert spaces["clean"].badge == "2,941"
    assert spaces["import"].badge == "214"
    assert spaces["clean"].total == 8
    tiles = {tile.label: tile for tile in state.tiles}
    assert tiles["Extra copies"].value == "2,941"
    assert tiles["Only on the NAS"].value == "214"
    assert state.findings is not None
    assert [row.action for row in state.findings.rows] == ["clean", "open", "import"]
    undo = state.action("undo")
    assert undo is not None
    assert not undo.available
    assert undo.reason == "Nothing to undo yet."
    assert undo.number is None
    sort = state.action("sort")
    assert sort is not None
    assert sort.reason == "No proposal to apply: ask classify for one first."


def test_after_a_clean_undo_and_the_quarantine_are_offered(tmp_path: Path) -> None:
    """The newest run undoable, its command, and the quarantine run by run."""
    state = _state(tmp_path, "after clean")
    assert state.undo is not None
    assert state.undo.command == "mh undo 20261020-143210"
    assert state.undo.number is not None
    assert [row.run_id for row in state.quarantine] == ["20261020-143210"]
    spaces = {space.id: space for space in state.spaces}
    assert spaces["history"].badge == "1"


def test_every_action_of_the_catalog_is_in_the_state(tmp_path: Path) -> None:
    """The 46 actions, with their doc in both languages; fields for the forms."""
    state = _state(tmp_path, "first run")
    names = {action.name for action in state.actions}
    assert names == {step.name for step in full_catalog().steps}
    album = state.action("album")
    assert album is not None
    assert [field.name for field in album.fields] == ["album"]
    assert album.number is None
    assert album.command == 'mh album "Crete 2023"'
    audit = state.action("audit")
    assert audit is not None
    assert audit.doc is not None
    assert audit.doc.url == audit.doc.url_en


def test_the_doc_links_follow_the_language(tmp_path: Path) -> None:
    """French page: the French chapter, and its English twin."""
    runtime = make_runtime(make_locations(tmp_path), _NEVER_OLD)
    with using(Locale.FR):
        state = home_state(runtime)
    audit = state.action("audit")
    assert audit is not None
    assert audit.doc is not None
    assert "/fr/commands/audit/" in audit.doc.url
    assert "/fr/" not in audit.doc.url_en
    assert state.docs.url.endswith("/fr/")


@pytest.mark.parametrize("locale", list(Locale))
def test_the_template_renders_with_no_undefined_value(
    monkeypatch: pytest.MonkeyPatch, locale: Locale
) -> None:
    """Every value the page names is given: an undefined one fails here."""
    strict = translated_environment("media_hygiene.review", escaped=("html", "j2"))
    strict.undefined = StrictUndefined
    monkeypatch.setattr(home, "translated_environment", lambda *_a, **_k: strict)
    with using(locale):
        page = home.home_page(relays_steps=True).decode()
    assert 'id="loading"' in page
    assert "fonts.googleapis" not in page
    assert page.count("/assets/fonts/") == 4
    texts = json.loads(re.search(r"const T = (\{.*?\});\n", page)[1])  # type: ignore[index]
    used = set(re.findall(r"\bT\.(\w+)", page))
    assert used <= set(texts)


def test_the_page_answers_without_reading_the_state(tmp_path: Path) -> None:
    """`GET /` never waits for the tool folders (0277); `GET /api/state` reads them."""
    runtime = make_runtime(make_locations(tmp_path), _NEVER_OLD)
    SITUATIONS["audit done"](runtime)
    reads: list[int] = []

    def state() -> HomeState:
        reads.append(1)
        return home_state(runtime)

    ending = Ending()
    app = HomeApp(
        home.home_page(),
        state,
        tmp_path,
        ending,
        HomeAudit(lambda _progress: pytest.fail("no audit")),
        Presence(ending, STOPPED),
    )
    host = {"host": "127.0.0.1"}
    page = asyncio.run(app.answer(Request("GET", "/", host)))
    assert page.status == HTTPStatus.OK
    assert b'id="loading"' in page.body
    assert not reads
    reply = asyncio.run(app.answer(Request("GET", "/api/state", host)))
    assert json.loads(reply.body)["proposed"]["name"] == "clean"
    assert reads == [1]


def test_assets_serves_only_its_own_files() -> None:
    """Images and fonts with their type; `../` and unknown types refused."""
    font = asyncio.run(
        asset_response("/assets/fonts/source-sans-3-latin-wght-normal.woff2")
    )
    assert font.status == HTTPStatus.OK
    assert font.content_type is ContentType.WOFF2
    assert font.max_age > 0
    image = asyncio.run(asset_response("/assets/images/avatar.webp"))
    assert image.content_type is ContentType.WEBP
    assert asset_file("/assets/../review/http.py") is None
    assert asset_file("/assets/%2e%2e/review/http.py") is None
    assert asset_file("/assets/images/__init__.py") is None
    assert asset_file("/assets/images/missing.webp") is None
    assert (ASSETS_DIR / "fonts" / "OFL-source-sans-3.txt").is_file()


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("", "a value is needed"),
        ('Noël "2025"', "no double quote"),
        ("Noël\n2025", "no control character"),
        ("--delete", "it cannot start with '-'"),
    ],
)
def test_each_refused_value_says_why(value: str, reason: str) -> None:
    """A quote, a control character, a leading `-`: refused with its reason."""
    album = full_catalog().step("album")
    with pytest.raises(FieldError, match=re.escape(reason)):
        checked_words(album, {"album": value})


def test_a_folder_must_look_like_one() -> None:
    """A NAS path or a drive letter: not a bare word."""
    nas = full_catalog().step("nas-add")
    with pytest.raises(FieldError, match="a folder as the Explorer shows it"):
        checked_words(nas, {"path": "Photos"})
    words = checked_words(nas, {"path": "\\\\NAS\\Photos"})
    assert words == ("folders", "add", "--backup", "\\\\NAS\\Photos")
    prune = full_catalog().step("reports-prune")
    with pytest.raises(FieldError, match="a number"):
        checked_words(prune, {"count": "ten"})


def _post(door: StepDoor, body: dict[str, object]) -> tuple[int, dict[str, str]]:
    """Send a step chosen to the server, as the page does."""
    request = Request("POST", "/api/step", _JSON, json.dumps(body).encode())
    reply = asyncio.run(step_response(door, request))
    return reply.status, json.loads(reply.body or b"{}")


def test_a_form_writes_the_one_shot_file_then_ends(tmp_path: Path) -> None:
    """The words written whole, then the server ends with the fields code."""
    ending = Ending()
    door = StepDoor(
        lambda: pytest.fail("no state"),
        ending,
        tmp_path,
        relays_steps=True,
        relays_fields=True,
    )
    fields = {"album": "Noël 2025"}
    status, body = _post(door, {"name": "album", "fields": fields})
    assert status == HTTPStatus.OK
    assert body["command"] == 'mh album "Noël 2025"'
    assert ending.asked == STEP_EXIT_BASE + FIELDS_STEP
    written = json.loads((tmp_path / STEP_FILE_NAME).read_text("utf-8"))
    assert written == {"words": ["album", "Noël 2025"]}


def test_a_refused_value_keeps_the_page_running(tmp_path: Path) -> None:
    """422 with the reason; nothing written, the server goes on."""
    ending = Ending()
    door = StepDoor(
        lambda: pytest.fail("no state"),
        ending,
        tmp_path,
        relays_steps=True,
        relays_fields=True,
    )
    status, body = _post(door, {"name": "album", "fields": {"album": 'a"b'}})
    assert status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "no double quote" in body["error"]
    assert ending.asked is None
    assert not (tmp_path / STEP_FILE_NAME).exists()


def test_an_mh_that_cannot_read_the_file_gets_the_command_to_copy(
    tmp_path: Path,
) -> None:
    """An older `mh`, or reports in a named volume: 409 and the command, no file."""
    ending = Ending()
    door = StepDoor(
        lambda: pytest.fail("no state"), ending, tmp_path, relays_steps=True
    )
    fields = {"path": "E:\\Archives"}
    status, body = _post(door, {"name": "folders-remove", "fields": fields})
    assert status == HTTPStatus.CONFLICT
    assert body["command"] == shown(("folders", "remove", "E:\\Archives"))
    assert ending.asked is None
    assert not (tmp_path / STEP_FILE_NAME).exists()


def test_powershell_reads_the_file_once_then_splats_its_words(
    tmp_path: Path,
) -> None:
    """mh.ps1: on the fields code only, the file's words run, the file removed first."""
    runtime: Runtime = make_runtime(make_locations(tmp_path))
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, COMMANDS))
    start = text.index("# A step with fields (0266)")
    block = text[start : text.index("$steps = @(", start)]
    code = STEP_EXIT_BASE + FIELDS_STEP
    assert f"if ($status -eq {code} -and (Test-Path -LiteralPath $file))" in block
    read = block.index("ConvertFrom-Json).words")
    removed = block.index("Remove-Item -LiteralPath $file")
    run = block.index("@words @typed")
    assert read < removed < run
    assert f'{STEP_FILE_NAME}"' in block
    assert "MEDIA_HYGIENE_LAUNCHER_STEPS=2" in text
