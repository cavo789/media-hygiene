"""The home page opened to a phone of the home network under `mh --lan` (0269).

The address taken (private IPv4 only), the code and token drawn from the run's secret,
the door in front of the home page (pairing, what a paired phone may ask, the Host and
Origin checks), the console line, the phone's page, and both `mh` scripts.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

import pytest

from media_hygiene.cli.menu_catalog_share import share_area
from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.doors import (
    LAN_DOOR_PORT,
    LAN_DOOR_VARIABLE,
    Door,
    lan_door_port,
)
from media_hygiene.review.ending import STOP_PATH, Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response, is_local
from media_hygiene.review.lan import (
    COOKIE_NAME,
    LAN_ADDRESS_VARIABLE,
    LAN_SECRET_VARIABLE,
    LanAccess,
    cookies,
    lan_access,
    private_address,
)
from media_hygiene.review.lan_app import LAN_PATH, MAX_FAILURES, LanApp
from media_hygiene.review.lan_problem import (
    LAN_PROBLEM_VARIABLE,
    LanProblem,
    lan_problem,
    with_problem,
)
from media_hygiene.review.listen import lan_handle, listening
from media_hygiene.review.local_app import LocalApp
from media_hygiene.services import home
from media_hygiene.services.home_lan import say_lan
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_lan import lan_command
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.ending import Handling

_PORT: Final = 8765
_ADDRESS: Final = "192.168.1.20"
_LAN_HOST: Final = f"{_ADDRESS}:{_PORT}"
_LAN_ORIGIN: Final = f"http://{_LAN_HOST}"
_SECRET: Final = b"ab" * 32
_PHONE_PAGE: Final = b"<p>phone</p>"
_JSON: Final = "application/json"


class _Home(LocalApp):
    """Stands for the home page: refuses another host, answers with what it saw."""

    __slots__ = ("seen",)

    def __init__(self) -> None:
        """Start without any request."""
        self.seen: list[Request] = []

    @override
    async def answer(self, request: Request) -> Response:
        """Keep the request, answer 200."""
        self.seen.append(request)
        return Response(HTTPStatus.OK, b"home")


def _access() -> LanAccess:
    return LanAccess(_ADDRESS, _PORT, _SECRET)


def _app() -> tuple[LanApp, _Home]:
    fake = _Home()
    return LanApp(fake, _access(), _PHONE_PAGE), fake


def _ask(app: Handling, request: Request) -> Response:
    """Ask through the door every page has, as the server does."""
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


def _phone(path: str, *, paired: bool = True, method: str = "GET") -> Request:
    headers = {"host": _LAN_HOST}
    if paired:
        headers["cookie"] = f"theme=dark; {COOKIE_NAME}={_access().token}"
    if method == "POST":
        headers |= {"content-type": _JSON, "origin": _LAN_ORIGIN}
    body = b"{}" if method == "POST" else b""
    return Request(method, path, headers, body, Door.LAN)


@pytest.mark.parametrize(
    ("given", "taken"),
    [
        ("192.168.1.20", "192.168.1.20"),
        (" 10.0.0.5 ", "10.0.0.5"),
        ("172.16.3.4", "172.16.3.4"),
        ("8.8.8.8", None),
        ("127.0.0.1", None),
        ("169.254.10.1", None),
        ("fd00::1", None),
        ("pc.example", None),
        ("", None),
    ],
)
def test_only_a_private_ipv4_address_is_taken(given: str, taken: str | None) -> None:
    """A home network only: never a public, loopback or link-local address."""
    assert private_address(given) == taken


def test_the_code_and_token_come_from_the_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same secret, the same code across the loop's restarts; the token apart."""
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, _ADDRESS)
    monkeypatch.setenv(LAN_SECRET_VARIABLE, "ab" * 32)
    first, second = lan_access(_PORT), lan_access(_PORT)
    assert first is not None
    assert second is not None
    assert first.code == second.code
    assert first.code.isdigit()
    assert len(first.code) == 8
    assert first.shown_code == f"{first.code[:4]} {first.code[4:]}"
    assert first.code not in first.token
    assert len(first.token) == 64
    assert first.pair_url == f"{_LAN_ORIGIN}/pair/{first.code}"
    other = LanAccess(_ADDRESS, _PORT, b"cd" * 32)
    assert other.token != first.token


def test_no_access_without_mh_lan_and_a_secret_drawn_by_hand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the address: none; without the secret: one for this server only."""
    monkeypatch.delenv(LAN_ADDRESS_VARIABLE, raising=False)
    monkeypatch.delenv(LAN_SECRET_VARIABLE, raising=False)
    assert lan_access(_PORT) is None
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, "8.8.8.8")
    assert lan_access(_PORT) is None
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, _ADDRESS)
    first, second = lan_access(_PORT), lan_access(_PORT)
    assert first is not None
    assert second is not None
    assert first.token != second.token


def test_cookies_are_read_by_name() -> None:
    """Several cookies, spaces around, one without a value."""
    assert cookies({"cookie": "a=1; mh_lan=xyz ; b"}) == {
        "a": "1",
        "mh_lan": "xyz",
        "b": "",
    }
    assert cookies({}) == {}


def test_the_loopback_passes_and_alone_gets_the_code() -> None:
    """The PC's page as before; `GET /api/lan`: the address, the code, the QR code."""
    app, fake = _app()
    local = {"host": f"127.0.0.1:{_PORT}"}
    assert _ask(app, Request("GET", "/api/state", local)).body == b"home"
    reply = _ask(app, Request("GET", LAN_PATH, local))
    assert reply.status == HTTPStatus.OK
    body = json.loads(reply.body)
    assert body["url"] == f"{_LAN_ORIGIN}/"
    assert body["code"] == _access().shown_code
    assert body["qr"].startswith("<svg")
    assert len(fake.seen) == 1
    # Even paired, a phone never reads the code.
    assert _ask(app, _phone(LAN_PATH)).status == HTTPStatus.FORBIDDEN


def test_another_host_is_refused_as_before() -> None:
    """A name of another site (DNS rebinding), or the address on another port."""
    app, fake = _app()
    for host in ("evil.example:8765", f"{_ADDRESS}:9999", _ADDRESS):
        request = Request("GET", "/api/state", {"host": host}, door=Door.LAN)
        assert _ask(app, request).status == HTTPStatus.FORBIDDEN, host
    assert not fake.seen


def test_an_unpaired_phone_gets_the_pairing_page_only() -> None:
    """Every GET: the form; anything else: 403; nothing reaches the home page."""
    app, fake = _app()
    for path in ("/", "/api/state", "/reports/index.html", "/assets/x.webp"):
        reply = _ask(app, _phone(path, paired=False))
        assert reply.status == HTTPStatus.UNAUTHORIZED, path
        assert reply.content_type is ContentType.HTML
        assert b'id="code"' in reply.body
    post = _phone("/api/audit", paired=False, method="POST")
    assert _ask(app, post).status == HTTPStatus.FORBIDDEN
    wrong = _phone("/", paired=False)
    wrong = replace(wrong, headers={**wrong.headers, "cookie": f"{COOKIE_NAME}=nope"})
    assert _ask(app, wrong).status == HTTPStatus.UNAUTHORIZED
    assert not fake.seen


def test_the_right_code_sets_the_cookie_and_opens_the_page() -> None:
    """303 to `/`, an HttpOnly cookie holding the token, never the code."""
    app, _fake = _app()
    code = _access().code
    reply = _ask(app, _phone(f"/pair/{code[:4]}%20{code[4:]}", paired=False))
    assert reply.status == HTTPStatus.SEE_OTHER
    assert "Location: /" in reply.headers
    cookie = next(line for line in reply.headers if line.startswith("Set-Cookie"))
    assert f"{COOKIE_NAME}={_access().token};" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert code not in cookie


def test_wrong_codes_close_the_pairing() -> None:
    """Each wrong code says so; from `MAX_FAILURES` on, the right one is refused."""
    app, _fake = _app()
    replies = [
        _ask(app, _phone("/pair/00000000x", paired=False))
        for _attempt in range(MAX_FAILURES)
    ]
    assert {reply.status for reply in replies} == {HTTPStatus.FORBIDDEN}
    assert b'id="code"' in replies[0].body
    assert b'id="code"' not in replies[-1].body  # the last one closed it: no form
    right = _phone(f"/pair/{_access().code}", paired=False)
    assert _ask(app, right).status == HTTPStatus.TOO_MANY_REQUESTS
    assert _ask(app, _phone("/", paired=False)).status == HTTPStatus.UNAUTHORIZED


def test_a_paired_phone_reads_and_runs_the_audit_as_from_the_loopback() -> None:
    """The phone's page; the state, the reports, the audit passed on, Host rewritten."""
    app, fake = _app()
    page = _ask(app, _phone("/"))
    assert page.body == _PHONE_PAGE
    for path in ("/api/state", "/api/audit", "/reports/index.html"):
        assert _ask(app, _phone(path)).body == b"home", path
    assert _ask(app, _phone("/api/audit", method="POST")).body == b"home"
    hosts = {request.headers["host"] for request in fake.seen}
    assert hosts == {f"127.0.0.1:{_PORT}"}
    posted = fake.seen[-1]
    assert posted.headers["origin"] == f"http://127.0.0.1:{_PORT}"
    assert posted.headers["cookie"]  # the rest kept as sent
    assets = _ask(app, _phone("/assets/images/favicon.png"))
    assert assets.status in {HTTPStatus.OK, HTTPStatus.NOT_FOUND}
    assert len(fake.seen) == 4  # the theme is served by the door, not the page


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/step"),
        ("POST", STOP_PATH),
        ("POST", "/api/alive"),
        ("POST", "/api/apply"),
        ("GET", "/api/other"),
        ("PUT", "/api/audit"),
    ],
)
def test_a_paired_phone_never_runs_a_step_nor_quits(method: str, path: str) -> None:
    """A step, Quit, the presence: the PC's; the phone is told to run it there."""
    app, fake = _app()
    request = _phone(path, method="POST" if method == "POST" else "GET")
    request = replace(request, method=method)
    reply = _ask(app, request)
    assert reply.status == HTTPStatus.FORBIDDEN
    assert not fake.seen


def test_a_post_from_another_origin_is_refused() -> None:
    """The cookie alone is not enough: the page itself, at the PC's address."""
    app, fake = _app()
    request = _phone("/api/audit", method="POST")
    request = replace(request, headers={**request.headers, "origin": "http://evil"})
    assert _ask(app, request).status == HTTPStatus.FORBIDDEN
    assert not fake.seen


def test_the_window_says_the_address_and_the_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One line with the address and the code; a public address said refused."""
    runtime = make_runtime(make_locations(tmp_path))
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, _ADDRESS)
    say_lan(runtime.output, _access())
    said = output_of(runtime)
    assert f"{_LAN_ORIGIN}/" in said
    assert _access().shown_code in said
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, "8.8.8.8")
    say_lan(runtime.output, None)
    assert "8.8.8.8 is not an address of a home network" in output_of(runtime)
    monkeypatch.delenv(LAN_ADDRESS_VARIABLE)
    before = output_of(runtime)
    say_lan(runtime.output, None)
    assert output_of(runtime) == before


def test_the_phones_page_runs_no_step() -> None:
    """Drawn for a phone: no presence, no Quit, each step said to run on the PC."""
    phone = home.home_page(remote=True).decode()
    assert "const REMOTE = true;" in phone
    assert "const RELAYS = false;" in phone
    assert "const REMOTE = false;" in home.home_page(relays_steps=True).decode()
    assert 'id="lanCard"' in phone


_COMMANDS: Final = LauncherCommands(("audit", "home"), (), ("home",), (), _PORT)


def _render(shell: Shell, tmp_path: Path) -> str:
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    return render_script(launcher_script(runtime, shell, _COMMANDS))


def test_powershell_publishes_the_home_page_on_the_lan_address_only(
    tmp_path: Path,
) -> None:
    """`mh --lan`: the PC's private address, the secret, for `home` only; ASCII."""
    script = _render(Shell.POWERSHELL, tmp_path)
    lan = lan_command()
    assert script.isascii()
    assert "$rest[0] -eq '--lan'" in script
    assert "function global:_mh_lan {" in script
    assert "[Security.Cryptography.RandomNumberGenerator]::Create()" in script
    assert "Add-Type" not in script[script.index("function global:_mh_lan {") :]
    assert f"'{lan.private}'" in script
    assert "$command -notin @('home', 'slideshow')" in script
    assert f'"$($lan.address):${{port}}:{lan.door_port}"' in script
    assert f"{lan.door}={lan.door_port}" in script
    assert f"{lan.address}=$($lan.address)" in script
    assert f"{lan.secret}=$($lan.secret)" in script
    assert "$page += @(_mh_lan_page $command)" in script
    assert "0.0.0.0" not in script  # noqa: S104  # never every interface
    block = script[script.index("function global:_mh_lan {") :]
    assert "$profile" not in block.lower()  # PowerShell's own variable


def test_bash_refuses_mh_lan(tmp_path: Path) -> None:
    """The bash `mh` says PowerShell only, runs nothing, fails."""
    script = tmp_path / "mh.sh"
    script.write_text(_render(Shell.BASH, tmp_path), encoding="utf-8")
    code = f"docker() {{ echo ran; }}\nsource {script}\nmh --lan"
    result = run_bash(code, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    assert result.returncode == 1
    assert "ran" not in result.stdout
    assert "mh --lan works in Windows PowerShell only" in result.stderr


def test_powershell_opens_the_slideshow_to_the_lan_when_asked(tmp_path: Path) -> None:
    """`mh slideshow --lan`: address and secret drawn, the flag left out, cleared."""
    script = _render(Shell.POWERSHELL, tmp_path)
    assert "$rest[0] -in @('slideshow') -and $rest -contains '--lan'" in script
    assert "function global:_mh_lan_open($soft) {" in script
    assert "$plain = @($rest | Where-Object { $_ -ne '--lan' }) + $typed" in script
    assert "try { mh @plain } finally { $global:MediaHygieneLan = $null }" in script
    assert (
        "try { _mh_home @args } finally { $global:MediaHygieneLan = $null }" in script
    )


def test_bash_refuses_mh_slideshow_lan(tmp_path: Path) -> None:
    """`mh slideshow --lan` in bash: PowerShell only, nothing run."""
    script = tmp_path / "mh.sh"
    script.write_text(_render(Shell.BASH, tmp_path), encoding="utf-8")
    code = f"docker() {{ echo ran; }}\nsource {script}\nmh slideshow --chosen --lan"
    result = run_bash(code, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    assert result.returncode == 1
    assert "ran" not in result.stdout
    assert "Windows PowerShell only" in result.stderr


def test_the_albums_open_from_the_share_area_and_the_phones_home() -> None:
    """The share area's panel and the phone's home view both open `/albums` (0297)."""
    phone = home.home_page(remote=True).decode()
    assert '"albums": "/albums"' in phone
    assert "albums: () =>" in phone
    assert '${hero()}${REMOTE ? EXTRAS.albums() : ""}' in phone
    assert share_area().groups[0].extra == "albums"


_LOCAL: Final = {"host": f"127.0.0.1:{_PORT}"}


@pytest.mark.parametrize(
    ("given", "taken"),
    [("none", LanProblem.NONE), ("public", LanProblem.PUBLIC), ("", None), ("x", None)],
)
def test_the_problem_is_read_from_mh(
    monkeypatch: pytest.MonkeyPatch, given: str, taken: LanProblem | None
) -> None:
    """`mh` names what keeps a phone away; anything else is no problem (0367)."""
    monkeypatch.setenv(LAN_PROBLEM_VARIABLE, given)
    assert lan_problem() is taken


def test_no_home_network_still_answers_the_card(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without an address: the PC's `/api/lan` says why, the rest passes on (0367)."""
    monkeypatch.setenv(LAN_PROBLEM_VARIABLE, "none")
    fake = _Home()
    app = with_problem(fake)
    reply = _ask(app, Request("GET", LAN_PATH, _LOCAL))
    assert json.loads(reply.body) == {"problem": "none"}
    assert _ask(app, Request("GET", "/api/state", _LOCAL)).body == b"home"
    assert (
        b"problem"
        not in _ask(
            app, Request("GET", LAN_PATH, {"host": _LAN_HOST}, door=Door.LAN)
        ).body
    )


def test_a_public_network_keeps_the_code_and_says_so(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A public network: the QR code and code still there, the problem beside (0367)."""
    monkeypatch.setenv(LAN_PROBLEM_VARIABLE, "public")
    app, _fake = _app()
    body = json.loads(_ask(with_problem(app), Request("GET", LAN_PATH, _LOCAL)).body)
    assert body["problem"] == "public"
    assert body["code"] == _access().shown_code


def test_without_a_problem_nothing_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """No variable: the handler as it was."""
    monkeypatch.delenv(LAN_PROBLEM_VARIABLE, raising=False)
    fake = _Home()
    assert with_problem(fake) is fake


def test_the_pc_page_holds_the_problem_lines() -> None:
    """The card's lines for no network, a public one, the firewall prompt."""
    page = home.home_page().decode()
    for name in ("lanNone", "lanPublic", "lanPair"):
        assert f'id="{name}"' in page
    assert "Private network" in page


def _render_lan(tmp_path: Path, *, lan: bool) -> str:
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    commands = replace(_COMMANDS, lan=lan)
    return render_script(launcher_script(runtime, Shell.POWERSHELL, commands))


def test_powershell_opens_mh_alone_to_the_lan_by_default(tmp_path: Path) -> None:
    """`mh` alone: the LAN path, never failing for want of a home network (0367)."""
    script = _render_lan(tmp_path, lan=True)
    assert "_mh_lan @typed  # open to the home network too" in script
    assert "$null = _mh_lan_open $true" in script
    assert "@{ problem = 'none' }; return $true" in script
    assert "$problem = 'public'" in script
    assert f'"{LAN_PROBLEM_VARIABLE}=$($lan.problem)"' in script
    assert "if (-not $lan.address) { return $options }" in script
    assert script.isascii()


def test_powershell_lan_off_keeps_mh_alone_on_the_pc(tmp_path: Path) -> None:
    """`[review] lan = false`: `mh` alone on the PC only; `--lan` still opens."""
    script = _render_lan(tmp_path, lan=False)
    assert "_mh_home @typed  # [review] lan = false" in script
    assert "_mh_lan @typed  # open" not in script
    assert "$rest[0] -eq '--lan'" in script


def test_the_setting_reaches_the_launcher() -> None:
    """`[review] lan` defaults to off until 0384 is fixed, the launcher's too."""
    assert ReviewSettings().lan is False
    assert _COMMANDS.lan is False


_FORGED: Final = ("127.0.0.1:8765", "localhost:8765", "[::1]:8765", _LAN_HOST)


@pytest.mark.parametrize("host", _FORGED)
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_a_forged_host_by_the_lan_door_never_passes_for_the_pc(
    host: str, method: str
) -> None:
    """0384: whatever `Host` it writes, an unpaired device of the Wi-Fi gets nothing.

    Every route the home page, the reviews and the stop answer is walked.
    """
    app, fake = _app()
    paths = (
        "/", "/api/state", LAN_PATH, STOP_PATH, "/api/alive", "/api/audit",
        "/api/step", "/search", "/browse", "/thumb/x", "/file/x", "/albums",
        "/reports/x", "/preview/x", "/assets/x", "/person",
    )  # fmt: skip
    for path in paths:
        headers = {"host": host, "content-type": _JSON}
        request = Request(method, path, headers, b"{}", Door.LAN)
        reply = _ask(app, request)
        assert reply.status in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}, path
    assert not fake.seen


def test_is_local_needs_the_pcs_door() -> None:
    """The loopback `Host` alone is not enough: the socket says the PC (0384)."""
    local = {"host": "127.0.0.1:8765"}
    assert is_local(Request("GET", "/", local))
    assert not is_local(Request("GET", "/", local, door=Door.LAN))


def test_the_lan_door_marks_its_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the socket of the home network's door marks a request `Door.LAN`."""
    seen: list[Door] = []

    async def handle(request: Request) -> Response:
        seen.append(request.door)
        return Response(HTTPStatus.OK)

    asyncio.run(lan_handle(handle)(Request("GET", "/", {})))
    assert seen == [Door.LAN]
    monkeypatch.setenv(LAN_DOOR_VARIABLE, "48088")
    assert lan_door_port() == LAN_DOOR_PORT
    monkeypatch.setenv(LAN_DOOR_VARIABLE, "x")
    assert lan_door_port() is None


def test_both_doors_listen_under_mh_lan(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request on the second socket reaches the page as `Door.LAN`; the first: PC."""
    seen: list[Door] = []

    async def handle(request: Request) -> Response:
        seen.append(request.door)
        return Response(HTTPStatus.OK)

    async def ask(port: int) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        await writer.drain()
        await reader.read()
        writer.close()

    async def run() -> None:
        probe = await asyncio.start_server(lambda _r, _w: None, "127.0.0.1", 0)
        free = probe.sockets[0].getsockname()[1]
        probe.close()
        await probe.wait_closed()
        monkeypatch.setenv(LAN_DOOR_VARIABLE, str(free))
        async with listening(handle, 0) as server:
            await ask(server.sockets[0].getsockname()[1])
            await ask(free)

    asyncio.run(run())
    assert seen == [Door.PC, Door.LAN]
