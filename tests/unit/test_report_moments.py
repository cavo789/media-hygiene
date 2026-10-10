"""Report dates: written in UTC, shown by the browser in the reader's time zone."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from media_hygiene.report.environment import make_environment, when

_UTC_TIME = '<time datetime="2026-10-10T07:52:00+00:00">2026-10-10 07:52 UTC</time>'


def test_a_moment_is_a_time_element_in_utc() -> None:
    """Whatever its zone, a moment is written in UTC, readable without scripts."""
    brussels = timezone(timedelta(hours=2))
    assert when(datetime(2026, 10, 10, 9, 52, tzinfo=brussels)) == _UTC_TIME
    assert when(datetime(2026, 10, 10, 7, 52)) == _UTC_TIME  # noqa: DTZ001


def test_pages_turn_times_into_local_time() -> None:
    """The filter is not escaped, and every page carries the converting script."""
    page = make_environment().from_string(
        '{% extends "base.html.j2" %}{% block content %}{{ at | when }}{% endblock %}'
    )
    html = page.render(at=datetime(2026, 10, 10, 7, 52, tzinfo=UTC))
    assert _UTC_TIME in html
    assert 'querySelectorAll("time[datetime]")' in html
