"""The documentation's generated blocks: capture excerpts, refreshed in place."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.support.docs.pages import excerpt, refresh, specifications
from tests.support.docs.scenario import CAPTURES
from tests.unit.test_documentation import DOCUMENTATION

if TYPE_CHECKING:
    from pathlib import Path

SCREEN = """── Clean ──
Summary
┌───┐
└───┘

docker run --rm -v "C:\\Photos:/data/c/Photos:ro" -x jpg -C /out/czkawka.json
💡 A tip long enough for the terminal
to wrap it on a second line.
2 burst shots will be moved.
1 orphan sidecar will be moved.
❓ Delete? [y/N] y
── Clean ──
"""


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("screen|Summary|└", "Summary\n┌───┐\n└───┘"),
        ("screen|re:^Sum|<blank>", "Summary\n┌───┐\n└───┘"),
        (
            "screen|A tip|.",
            "💡 A tip long enough for the terminal\nto wrap it on a second line.",
        ),
        ("screen|❓|.", "❓ Delete? [y/N] y"),
        ("screen|burst|.", "2 burst shots will be moved."),
        (
            "screen|docker run|.",
            'docker run --rm -v "C:\\Photos:/data/c/Photos:ro" … -C /out/czkawka.json',
        ),
    ],
)
def test_excerpts_follow_their_bounds(spec: str, expected: str) -> None:
    """START and END pick the lines; wrapped lines follow; Czkawka's command is cut."""
    assert excerpt({"screen": SCREEN}, spec) == expected


def test_an_unknown_capture_is_refused() -> None:
    """A typo in a marker fails loudly instead of emptying the block."""
    with pytest.raises(KeyError, match=r"nothing\.txt"):
        excerpt({"screen": SCREEN}, "nothing.txt")


def test_refresh_replaces_only_the_generated_block(tmp_path: Path) -> None:
    """The prose and the fences stay; the block's body is the fresh capture."""
    page = tmp_path / "page.md"
    page.write_text(
        "Intro.\n\n<!-- capture: screen|❓|. -->\n```text\nold\n```\n\nOutro.\n",
        encoding="utf-8",
    )
    refresh(page, {"screen": SCREEN})
    fresh = (
        "Intro.\n\n<!-- capture: screen|❓|. -->\n```text\n❓ Delete? [y/N] y\n```\n"
    )
    assert page.read_text(encoding="utf-8") == f"{fresh}\nOutro.\n"


@pytest.mark.parametrize("page", sorted(DOCUMENTATION.rglob("*.md")), ids=str)
def test_markers_name_a_capture_of_the_scenario(page: Path) -> None:
    """`docs_screenshots` can refill every generated block of the documentation."""
    names = {spec.split("|")[0] for spec in specifications(page)}
    assert names <= CAPTURES
