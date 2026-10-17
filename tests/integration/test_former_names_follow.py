"""The kept file remembers where the copies `clean` removed lay (TODO 0207).

One test per event that changes the kept file's path or the copy's: the clean, its
undo, a move by the tool, a folder renamed by the user, the kept file deleted.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import REMOVED_COPIES, Phase
from media_hygiene.constants import MediaKind
from media_hygiene.index.former_names import former_copies
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import Filters, SearchQuery, parse_terms
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify_inputs import media_input
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.tags import TagStep
from media_hygiene.services.undo import undo_run
from media_hygiene.tags.models import TagSource
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.classify.former import FormerCopy
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_LIMIT: Final = 50


def clean(runtime: Runtime) -> str:
    """Audit then clean to the quarantine; return the run identifier."""
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode())
    run_id, _outcome = service.execute(service.feasible(replace(findings.plan)))
    return run_id


def remembered(locations: Locations) -> dict[Path, tuple[FormerCopy, ...]]:
    """The removed copies the index remembers, by kept file."""
    with FactsRepository.open(locations.index_file) as repository:
        return former_copies(repository.connection)


def removed(locations: Locations, run_id: str) -> dict[str, str]:
    """The copies the run removed, and their kept file, from its journal."""
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    return {
        entry.path: entry.keeper
        for entry in done_states(entries, Phase.CLEAN)
        if entry.keeper and entry.action in REMOVED_COPIES
    }


def test_a_clean_writes_the_rows_and_its_undo_removes_them(
    locations: Locations,
) -> None:
    """Each copy removed is remembered by its kept file, until the undo."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    copies = removed(locations, run_id)
    assert copies
    rows = {
        str(copy.path): str(kept)
        for kept, found in remembered(locations).items()
        for copy in found
    }
    assert rows == copies
    roots = {copy.root for found in remembered(locations).values() for copy in found}
    assert roots <= {locations.data_dir / "c", locations.data_dir / "d"}
    undo_run(runtime, run_id, NullProgress())
    assert not remembered(locations)


def test_a_move_by_the_tool_carries_them(locations: Locations) -> None:
    """`sort` (or `undo`) moves the kept file: its rows go with it."""
    build_demo(locations.data_dir)
    run_id = clean(make_runtime(locations))
    kept = next(iter(sorted(set(removed(locations, run_id).values()))))
    before = remembered(locations)[Path(kept)]
    moved = str(Path(kept).with_name("moved.jpg"))
    with FactsRepository.open(locations.index_file) as repository:
        repository.move([(kept, moved)])
    after = remembered(locations)
    assert after[Path(moved)] == before
    assert Path(kept) not in after


def test_a_folder_renamed_by_the_user_carries_them(locations: Locations) -> None:
    """The next audit follows the kept file (0147), and its rows with it."""
    build_demo(locations.data_dir)
    run_id = clean(make_runtime(locations))
    kept = Path(next(iter(sorted(set(removed(locations, run_id).values())))))
    before = remembered(locations)[kept]
    renamed = kept.parent.with_name(kept.parent.name + " (renamed)")
    kept.parent.rename(renamed)
    AuditService(make_runtime(locations), NullProgress()).run()
    after = remembered(locations)
    assert after[renamed / kept.name] == before
    assert kept not in after


def test_the_kept_file_deleted_forgets_them(locations: Locations) -> None:
    """A kept file proven gone takes its rows away."""
    build_demo(locations.data_dir)
    run_id = clean(make_runtime(locations))
    kept = Path(next(iter(sorted(set(removed(locations, run_id).values())))))
    shutil.rmtree(kept.parent)
    AuditService(make_runtime(locations), NullProgress()).run()
    assert not any(path.is_relative_to(kept.parent) for path in remembered(locations))


def test_search_finds_the_kept_photo_by_a_removed_folder_word(
    locations: Locations,
) -> None:
    """`tags` makes words of the removed copies' folders; `search` finds them."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    with TagStep(runtime) as step:
        work = step.plan(())
        step.cheap(work)
    backup = str(locations.data_dir / "d/backup/2019/IMG_0002.jpg")
    kept = Path(removed(locations, run_id)[backup])
    query = SearchQuery(parse_terms("former:backup"), Filters())
    with SearchIndex.open(locations.index_file) as search:
        found = search.find(query, _LIMIT)
    paths = {hit.photo.path for hit in found.hits}
    assert kept in paths
    hit = next(hit for hit in found.hits if hit.photo.path == kept)
    assert "backup" in hit.tags[TagSource.FORMER]


def test_classify_reads_where_the_removed_copies_lay(locations: Locations) -> None:
    """The input of a kept file carries its removed copies (0208)."""
    build_demo(locations.data_dir)
    run_id = clean(make_runtime(locations))
    kept = Path(next(iter(sorted(set(removed(locations, run_id).values())))))
    stat = kept.stat()
    file = MediaFile(kept, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)
    with FactsRepository.open(locations.index_file) as repository:
        found = media_input(file, locations.data_dir / "c", repository)
    assert found.former == remembered(locations)[kept]
