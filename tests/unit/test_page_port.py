"""`[review] port` (0260): the port of every page, `--port` still winning."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.cli.review_options import page_port
from media_hygiene.config.review_settings import PAGE_PORT, ReviewSettings
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_the_default_is_8088_and_a_port_is_checked() -> None:
    """8088 unless set; 0 and 70000 are no port."""
    assert ReviewSettings().port == PAGE_PORT == 8088
    assert ReviewSettings(port=9000).port == 9000
    for wrong in (0, 70_000):
        with pytest.raises(ValidationError):
            ReviewSettings(port=wrong)


def test_port_given_wins_else_the_setting(locations: Locations) -> None:
    """`--port` when typed; else `[review] port`."""
    runtime = make_runtime(locations).with_overrides({"review": {"port": 9000}})
    assert page_port(runtime, None) == 9000
    assert page_port(runtime, 9100) == 9100
