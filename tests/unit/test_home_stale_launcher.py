"""The home page says when `mh` is older than its image, `mh update` a button (0368).

The console's line of 0290 was never seen from a shortcut (a minimised window): the
page's server, run by the same `docker run`, has the launcher's stamp and shows it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_state import home_state
from media_hygiene.services import launcher_stamp
from media_hygiene.services.home import home_page
from media_hygiene.services.launcher_stamp import LAUNCHER_STAMP_VARIABLE
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_IMAGE: Final = "0.5.0+aaaaaaaaaaaa"


def _stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, written: str | None) -> str:
    """The state's line for an `mh` that passed `written` (None: no stamp at all)."""
    monkeypatch.setattr(launcher_stamp, "image_stamp", lambda: _IMAGE)
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    if written is None:
        monkeypatch.delenv(LAUNCHER_STAMP_VARIABLE, raising=False)
    else:
        monkeypatch.setenv(LAUNCHER_STAMP_VARIABLE, written)
    return home_state(make_runtime(make_locations(tmp_path))).stale


def test_an_older_mh_gets_the_line_with_mh_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another stamp, or none (an `mh` before 0290): the line, `mh update`."""
    for written in ("0.4.0+bbbbbbbbbbbb", None):
        line = _stale(tmp_path, monkeypatch, written)
        assert "mh update" in line
        assert "0.5.0 (build aaaaaaaaaaaa)" in line


def test_the_same_stamp_or_no_mh_gets_no_banner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After `mh update` the stamps agree: nothing; outside `mh`: nothing."""
    assert not _stale(tmp_path, monkeypatch, _IMAGE)
    monkeypatch.delenv(LAUNCHER_VARIABLE)
    assert not home_state(make_runtime(make_locations(tmp_path))).stale


def test_the_banner_offers_the_update_step_as_a_button() -> None:
    """Drawn first on the home view, its button runs the step `update`."""
    page = home_page(relays_steps=True).decode()
    assert "function staleBanner()" in page
    button = '<button class="btn btn-primary" type="button" data-run="update">'
    assert "${esc(S.stale)}</p>" + button in page
    assert "${staleBanner()}${updateBanner()}" in page
