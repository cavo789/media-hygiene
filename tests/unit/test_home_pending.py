"""The choices waiting in decisions.json, counted page by page (0522)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.cli.home_pending import home_pending
from media_hygiene.services.home import home_page

if TYPE_CHECKING:
    from pathlib import Path


def _write(folder: Path, body: dict[str, object]) -> None:
    """A decisions file in the reports folder."""
    said = {"version": 1, "roots": ["C:\\Photos"], **body}
    (folder / "decisions.json").write_text(json.dumps(said), "utf-8")


def test_each_page_counts_only_what_it_set_aside(tmp_path: Path) -> None:
    """A series kept whole, a pair left planned: not counted."""
    _write(
        tmp_path,
        {
            "bursts": [
                {"status": "done", "kept": ["C:\\a.jpg"], "discarded": ["C:\\b.jpg"]},
                {"status": "todo", "kept": ["C:\\c.jpg"], "discarded": []},
            ],
            "pairs": [
                {"kept_in": "C:\\A", "removed_from": "C:\\B", "action": "planned"}
            ],
            "chosen": [{"path": "C:\\d.jpg", "size": 1, "mtime_ns": 1}],
        },
    )
    pending = home_pending(tmp_path)
    assert pending is not None
    assert pending.total == 2
    assert [page.count for page in pending.pages] == [1, 1]


def test_nothing_waits_without_a_file_or_with_a_broken_one(tmp_path: Path) -> None:
    """No file, no reports folder, an unreadable file: no count shown."""
    assert home_pending(tmp_path) is None
    assert home_pending(None) is None
    (tmp_path / "decisions.json").write_text("{", "utf-8")
    assert home_pending(tmp_path) is None


def test_the_page_offers_apply_all() -> None:
    """The banner and its one button, the home page's `apply` step."""
    page = home_page().decode()
    assert "function pendingBanner()" in page
    assert '"applyAll"' in page
