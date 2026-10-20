"""`home`: the home page shows `status` and `mh menu`, and ends with the step chosen."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import typer

import media_hygiene
from media_hygiene.cli.context import user_errors
from media_hygiene.cli.home_audit import page_audit
from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.menu_steps import build_menu, choice_lines
from media_hygiene.cli.status_view import status_lines
from media_hygiene.constants import ExitCode
from media_hygiene.errors import PageClosed
from media_hygiene.review import presence
from media_hygiene.review.app import DECIDE_PATH, FILE_PATH, ReviewApp
from media_hygiene.review.ending import (
    STOP_PATH,
    STOPPED,
    Ending,
    EndingDoor,
    run_server,
    serve_until_ended,
)
from media_hygiene.review.home_app import STEP_PATH, HomeApp
from media_hygiene.review.home_views import STEP_EXIT_BASE
from media_hygiene.review.presence import Presence
from media_hygiene.services import home
from media_hygiene.services.home import home_page, launcher_relays_steps
from media_hygiene.services.home_audit import HomeAudit
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.review_file import review_page
from media_hygiene.services.status import read_status
from tests.support.cli import run
from tests.support.review import (
    JSON_HEADERS,
    PAGE,
    Call,
    Reply,
    review_session,
    send_call,
    write_burst,
)
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.ending import Handling
    from media_hygiene.services.runtime import Runtime


def audited(cli: CliRunner, locations: Locations) -> Runtime:
    """Audit the demo tree, as the user would, then build a runtime on its folders."""
    assert run(cli, "audit").exit_code == 0
    return make_runtime(locations)


def serve(
    make: Callable[[Ending], Handling], calls: Sequence[Call]
) -> tuple[list[Reply], int | None]:
    """Serve a page, send each call, then tell how the server ended.

    Returns:
        The replies, and the exit code the page asked for (None: still serving).
    """

    async def scenario() -> tuple[list[Reply], int | None]:
        ending = Ending()
        ports: asyncio.Queue[int] = asyncio.Queue()
        door = EndingDoor(make(ending), ending)
        server = asyncio.create_task(serve_until_ended(door, 0, ports.put_nowait))
        port = await ports.get()
        replies = [await send_call(port, call) for call in calls]
        try:
            code: int | None = await asyncio.wait_for(asyncio.shield(server), 2)
        except TimeoutError:
            server.cancel()
            code = None
        return replies, code

    return asyncio.run(scenario())


def step(number: int, command: str, headers: tuple[str, ...] = JSON_HEADERS) -> Call:
    """`POST /api/step`, as the page sends it."""
    body = json.dumps({"number": number, "command": command}).encode()
    return Call("POST", STEP_PATH, body, headers)


def home_app(
    runtime: Runtime, *, relays_steps: bool = True
) -> Callable[[Ending], HomeApp]:
    """Build the home page's app on a runtime, its launcher running steps or not."""
    state = partial(home_state, runtime)
    audit = HomeAudit(page_audit(runtime))
    return lambda ending: HomeApp(
        home_page(relays_steps=relays_steps),
        state,
        runtime.locations.reports_dir,
        ending,
        audit,
        Presence(ending, STOPPED),
        relays_steps=relays_steps,
    )


def test_the_state_is_what_status_and_the_menu_say(
    cli: CliRunner, locations: Locations
) -> None:
    """The lines of `status`, the steps of `mh menu` with their numbers, the reports."""
    runtime = audited(cli, locations)
    state = home_state(runtime)
    status = read_status(runtime)
    assert state.lines == status_lines(status)
    menu = build_menu(status, runtime.settings.clean.purge_hint_days)
    numbered = {
        f"{step.number}\t{step.command}"
        for section in state.sections
        for step in section.steps
        if step.number
    }
    assert numbered == {
        f"{number}\tmh {command}"
        for number, _tab, command in (
            line.partition("\t") for line in choice_lines(menu)
        )
        if number != "0"
    }
    assert state.proposed is not None
    assert menu.proposed is not None
    assert state.proposed.command == f"mh {menu.proposed.command}"
    assert [report.label for report in state.reports] == ["Last audit"]
    assert state.index == "/reports/index.html"
    assert state.previews
    assert all(url.startswith("/reports/") for url in state.previews)


def test_a_step_ends_the_server_with_100_plus_its_number(
    cli: CliRunner, locations: Locations
) -> None:
    """The step's button ends the server with `100 + n`; a stale menu is refused."""
    runtime = audited(cli, locations)
    proposed = home_state(runtime).proposed
    assert proposed is not None
    replies, code = serve(
        home_app(runtime),
        [
            step(proposed.number, "mh purge 20010101-000000"),
            step(proposed.number, proposed.command),
        ],
    )
    stale, chosen = replies
    assert stale.status == 409
    assert "changed" in str(stale.json())
    assert chosen.status == 200
    assert chosen.json() == {"number": proposed.number, "command": proposed.command}
    assert code == STEP_EXIT_BASE + proposed.number


def test_without_a_launcher_that_runs_steps_the_page_keeps_serving(
    cli: CliRunner, locations: Locations
) -> None:
    """An `mh` that does not relay `100 + n`: the step is refused, the server stays.

    The maintainer's `mh` (before TODO 0210) lost the code: the page ended and nothing
    ran. Without the variable, a button copies its command instead of posting it.
    """
    runtime = audited(cli, locations)
    proposed = home_state(runtime).proposed
    assert proposed is not None
    replies, code = serve(
        home_app(runtime, relays_steps=False),
        [Call("GET", "/"), step(proposed.number, proposed.command)],
    )
    page, refused = replies
    assert b"const relaysSteps = false;" in page.body
    assert b'id="copyBox"' in page.body
    assert refused.status == 409
    assert "type the command" in str(refused.json())
    assert code is None


def test_the_launcher_variable_says_whether_steps_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`MEDIA_HYGIENE_LAUNCHER_STEPS`, set by `mh`, is the one signal; not carried."""
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    assert not launcher_relays_steps()
    assert b"const relaysSteps = false;" in home_page()
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    assert LAUNCHER_STEPS_VARIABLE == "MEDIA_HYGIENE_LAUNCHER_STEPS"
    assert launcher_relays_steps()
    assert b"const relaysSteps = true;" in home_page(relays_steps=True)


def test_every_step_button_sends_the_step_it_shows(
    cli: CliRunner, locations: Locations
) -> None:
    """Each numbered step, and the proposed one, is accepted with its own command.

    The page sends the number and command of the button clicked, the server runs only
    the pair its state agrees with: whatever button, the step run is the one shown.
    """
    runtime = audited(cli, locations)
    state = home_state(runtime)
    shown = [
        (item.number, item.command)
        for section in state.sections
        for item in section.steps
        if item.number
    ]
    assert len({number for number, _command in shown}) == len(shown)
    assert state.proposed is not None
    assert (state.proposed.number, state.proposed.command) in shown
    for number, command in shown:
        assert state.command_of(number) == command


def test_the_page_its_state_and_the_reports_are_served(
    cli: CliRunner, locations: Locations
) -> None:
    """The page, its state, a report and a preview; nothing outside the reports."""
    runtime = audited(cli, locations)
    state = home_state(runtime)
    assert state.reports
    replies, code = serve(
        home_app(runtime),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            Call("GET", state.reports[0].url),
            Call("GET", state.previews[0]),
            Call("GET", "/reports/"),
            Call("GET", "/reports/%2e%2e/config/config.toml"),
            Call("GET", "/reports/nothing.html"),
            Call("GET", "/nowhere"),
            Call("POST", "/", b"{}", JSON_HEADERS),
        ],
    )
    page, served, report, preview, index, outside, missing, nowhere, post = replies
    assert code is None
    assert page.status == 200
    assert b"/api/step" in page.body
    assert served.json() == json.loads(state.model_dump_json())
    assert report.status == 200
    assert report.headers["content-type"].startswith("text/html")
    assert preview.headers["content-type"] == "image/jpeg"
    assert index.status == 200
    assert (outside.status, missing.status, nowhere.status) == (404, 404, 404)
    assert post.status == 405


def test_another_host_and_a_form_are_refused(
    cli: CliRunner, locations: Locations
) -> None:
    """A page of another site can neither read the page, choose a step nor stop it."""
    runtime = audited(cli, locations)
    proposed = home_state(runtime).proposed
    assert proposed is not None
    form = ("Host: 127.0.0.1", "Content-Type: application/x-www-form-urlencoded")
    replies, code = serve(
        home_app(runtime),
        [
            Call("GET", "/", headers=("Host: evil.example",)),
            step(
                proposed.number,
                proposed.command,
                ("Host: evil.example", *JSON_HEADERS[1:]),
            ),
            step(proposed.number, proposed.command, form),
            Call("POST", STOP_PATH, b"{}", ("Host: evil.example", *JSON_HEADERS[1:])),
            Call("POST", STOP_PATH, b"{}", form),
            Call("GET", STOP_PATH),
        ],
    )
    assert [reply.status for reply in replies] == [403, 403, 415, 403, 415, 405]
    assert code is None


@pytest.mark.usefixtures("cli")
def test_stop_ends_any_page_with_0(locations: Locations) -> None:
    """`POST /api/stop`, the "⌂ Home" link of every page, ends its server with 0."""
    write_burst(locations.data_dir)
    session = review_session(locations)

    async def scenario() -> tuple[Reply, int]:
        with ThreadPoolExecutor(1) as executor:
            ports: asyncio.Queue[int] = asyncio.Queue()
            app = ReviewApp(session, PAGE, executor)
            server = asyncio.create_task(run_server(app, 0, ports.put_nowait))
            port = await ports.get()
            reply = await send_call(port, Call("POST", STOP_PATH, b"{}", JSON_HEADERS))
            return reply, await asyncio.wait_for(server, 2)

    reply, code = asyncio.run(scenario())
    assert reply.status == 200
    assert reply.json() == {"stopped": True}
    assert code == 0


def test_every_page_links_home(cli: CliRunner, locations: Locations) -> None:
    """The review's page carries the "⌂ Home" link, which posts to the stop path."""
    audited(cli, locations)
    write_burst(locations.data_dir)
    session = review_session(locations)
    page = review_page("review.html.j2", session.place, (DECIDE_PATH, FILE_PATH))
    assert b'id="homeLink"' in page
    assert STOP_PATH.encode() in page


def test_the_command_exits_with_the_step_chosen(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`home` exits with `100 + n` and names the step; closed, it exits with 0."""
    audited(cli, locations)
    proposed = home_state(make_runtime(locations)).proposed
    assert proposed is not None
    monkeypatch.setattr(
        home,
        "serve_home",
        lambda _runtime, _state, _port: STEP_EXIT_BASE + proposed.number,
    )
    result = run(cli, "home")
    assert result.exit_code == STEP_EXIT_BASE + proposed.number
    assert proposed.command in result.output
    monkeypatch.setattr(home, "serve_home", lambda _runtime, _state, _port: 0)
    closed = run(cli, "home")
    assert closed.exit_code == 0
    assert "Home page closed" in closed.output


def test_every_page_template_includes_the_home_link() -> None:
    """Each page served but the home page itself includes the "⌂ Home" fragment."""
    source = Path(media_hygiene.__file__).parent
    pages = [
        page
        for page in source.glob("*/templates/*.html.j2")
        if page.parent.parent.name in {"review", "search", "places", "people"}
        # The page freeing a phone ends into `mh phone`, never the home page (0248).
        and page.name
        not in {"home.html.j2", "home_link.html.j2", "phone_review.html.j2"}
    ]
    assert len(pages) >= 9
    for page in pages:
        assert 'include "home_link.html.j2"' in page.read_text("utf-8"), page.name


def test_a_closed_tab_or_quit_ends_home_with_0(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tab said it leaves and none came back, or Quit: home ends with 0 (0261)."""
    monkeypatch.setattr(presence, "LEAVING_GRACE_SECONDS", 0.05)
    runtime = audited(cli, locations)
    page = home_page(relays_steps=True).decode()
    assert 'id="quit"' in page
    assert presence.PRESENCE_PATH in page
    assert STOP_PATH in page
    leaving = Call("POST", presence.PRESENCE_PATH, b'{"leaving": true}', JSON_HEADERS)
    replies, code = serve(home_app(runtime), [leaving])
    assert replies[0].status == 200
    assert code == STOPPED
    replies, code = serve(
        home_app(runtime), [Call("POST", STOP_PATH, b"{}", JSON_HEADERS)]
    )
    assert replies[0].status == 200
    assert code == STOPPED


def test_a_page_whose_tab_was_closed_raises_page_closed(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0262: any page served by run_server: its tab left, none came back."""
    monkeypatch.setattr(presence, "LEAVING_GRACE_SECONDS", 0.05)
    write_burst(locations.data_dir)
    session = review_session(locations)
    leaving = Call("POST", presence.PRESENCE_PATH, b'{"leaving": true}', JSON_HEADERS)

    async def scenario() -> Reply:
        with ThreadPoolExecutor(1) as executor:
            ports: asyncio.Queue[int] = asyncio.Queue()
            app = ReviewApp(session, PAGE, executor)
            server = asyncio.create_task(run_server(app, 0, ports.put_nowait))
            reply = await send_call(await ports.get(), leaving)
            with pytest.raises(PageClosed):
                await asyncio.wait_for(server, 2)
            return reply

    assert asyncio.run(scenario()).status == 200


def test_a_closed_page_exits_with_its_own_code(locations: Locations) -> None:
    """0262: `user_errors` says it in one line and exits with PAGE_CLOSED."""
    runtime = make_runtime(locations)
    with pytest.raises(typer.Exit) as ended, user_errors(runtime.output):
        raise PageClosed
    assert ended.value.exit_code == ExitCode.PAGE_CLOSED
