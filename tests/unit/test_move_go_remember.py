"""*Move to an event…*: a plain filing writes no event, the ticked box does (0573)."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search import move_event, move_go
from media_hygiene.services.selection_models import MoveView, SourceFolder

if TYPE_CHECKING:
    from media_hygiene.search.rule_desk import RuleDesk
    from media_hygiene.services.selection_models import Picked

_CONFIG = (
    '# mine\n[[classify.rules]]\nname = "Existing folders"\nmatch = "existing_folder"\n'
)
_TEMPLATES = Path(move_go.__file__).parent / "templates"


class _Mover:
    """A mover that moves nothing: the route's own work is what is tested."""

    def __init__(self, config: Path) -> None:
        """Keep where `config.toml` lies."""
        self.runtime = SimpleNamespace(
            locations=SimpleNamespace(config_file=config),
            settings=SimpleNamespace(classify=SimpleNamespace(timezone="")),
        )

    def move(self, chosen: Picked, name: str) -> dict[str, object]:
        """Answer one file moved."""
        return {"run_id": "r1", "moved": len(chosen.paths), "name": name}


def _answer(tmp_path: Path, *, remember: bool) -> dict[str, object]:
    """Move one dated photo to "Napoleon", the box ticked or not."""
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE files (media_date TEXT, camera TEXT)")
        connection.execute("INSERT INTO files VALUES ('2019:07:22 10:00:00', NULL)")
        index = SimpleNamespace(
            connection=connection,
            source_of=lambda _key: SimpleNamespace(path=Path("/data/c/a.mp4")),
            built=None,
        )
        desk = cast(
            "RuleDesk",
            SimpleNamespace(
                index=index,
                mover=_Mover(tmp_path / "config.toml"),
                mapper=HostPathMapper(Path("/data")),
                aside=frozenset,
            ),
        )
        body = json.dumps({"keys": [1], "name": "Napoleon", "remember": remember})
        response = asyncio.run(
            move_go.move_answer(desk, move_go.MOVE_PATH, body.encode())
        )
    return cast("dict[str, object]", json.loads(response.body))


def _tree(root: Path) -> dict[str, bytes]:
    """Every file under `root`, with its bytes."""
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def test_unticked_the_move_writes_nothing_besides_the_files(tmp_path: Path) -> None:
    """`config.toml` byte-identical, no `events/` file: a filing is not an event."""
    (tmp_path / "config.toml").write_text(_CONFIG, encoding="utf-8")
    before = _tree(tmp_path)
    answer = _answer(tmp_path, remember=False)
    assert answer["moved"] == 1
    assert not answer["remembered"]
    assert _tree(tmp_path) == before


def test_ticked_the_event_is_written_and_read_back(tmp_path: Path) -> None:
    """The box ticked: today's behaviour, the sentence read back from disk."""
    config = tmp_path / "config.toml"
    config.write_text(_CONFIG, encoding="utf-8")
    answer = _answer(tmp_path, remember=True)
    assert "2019-07-22..2019-07-22" in str(answer["remembered"])
    events = [r for r in read_rules(config) if r.match is RuleMatch.DATE_RANGE]
    assert [event.name for event in events] == ["Napoleon"]


def test_the_dialog_box_is_there_unticked() -> None:
    """The box, unticked but for late photos (0612); no 'No rule is written'."""
    page = (_TEMPLATES / "move_dialog.html.j2").read_text(encoding="utf-8")
    assert '<input id="moveRemember" type="checkbox">' in page
    assert "No rule is written" not in page
    script = (_TEMPLATES / "move_dialog.js.j2").read_text(encoding="utf-8")
    ticked = "checked = Boolean(window.mhLate && window.mhLate.shown());"
    assert ticked in script


def _view(
    *counts: tuple[int, bool], target: str = r"C:\Photos\2019\2019-07\Trip"
) -> MoveView:
    """A move view of source folders of these counts, ticked or not."""
    sources = tuple(
        SourceFolder(folder=f"C:\\F{n}", files=files, keys=(n,), ticked=ticked)
        for n, (files, ticked) in enumerate(counts)
    )
    return MoveView(
        proposed="Trip",
        name="Trip",
        month="2019/2019-07",
        target=target,
        sources=sources,
    )


def test_the_events_card_says_where_the_files_go_singular_and_plural() -> None:
    """0574: one file, ten files; the unticked folder is not counted; no target."""
    assert move_event.goes_said(_view((1, True))) == (
        r"This file will go to C:\Photos\2019\2019-07\Trip."
    )
    plural = move_event.goes_said(_view((4, True), (6, True), (3, False)))
    assert plural == r"These 10 files will go to C:\Photos\2019\2019-07\Trip."
    assert "Another folder" in move_event.goes_said(_view((2, True), target=""))
    assert "Another folder" in move_event.goes_said(_view((2, False)))
