"""The docs captures write the reports' paths as a Windows reader sees them (0196)."""

from __future__ import annotations

from tests.support.docs.host_paths import WINDOWS_REPORTS, as_on_windows


def test_a_report_path_becomes_the_readers_windows_folder() -> None:
    r"""`/reports/<path>` → `C:\Users\you\media-hygiene\reports\<path>`."""
    screen = "✅ Index: /reports/2026/index.html\n👉 next"
    assert as_on_windows(screen) == (
        f"✅ Index: {WINDOWS_REPORTS}\\2026\\index.html\n👉 next"
    )


def test_a_path_too_long_for_the_terminal_goes_to_the_next_line() -> None:
    """As Rich wraps it: the label alone, then the whole path."""
    screen = "✅ Report with the photos: /reports/20261016-192346-classify/report.html"
    assert as_on_windows(screen).split("\n") == [
        "✅ Report with the photos:",
        f"{WINDOWS_REPORTS}\\20261016-192346-classify\\report.html",
    ]


def test_mount_options_and_bare_mount_points_are_left_alone() -> None:
    """`-v …:/reports`, `/reports` alone and other folders: unchanged."""
    for line in (
        '  -v "$HOME\\media-hygiene\\reports:/reports" `',
        "in the folder mounted on /reports.",
        "/journal/20261016-1923.jsonl",
    ):
        assert as_on_windows(line) == line
