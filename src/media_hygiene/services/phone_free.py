r"""`phone-prove`: the files ticked to leave a phone, each proven by its content (0248).

`mh` pipes the plan's lines of the files ticked in the page (`case<TAB>path<TAB>size
<TAB>date<TAB>reason…`, as `phone-plan` wrote them; a file imported by this run comes
as `destination` with its copy's relative path), after copying each one from the phone
into the staging folder under the same relative path. Every proof answers one line:
`proven<TAB>path<TAB>size<TAB>case<TAB>sha256<TAB>held<TAB>note`, or
`kept<TAB>path<TAB>size<TAB>reason`. Only a proven file may then leave the phone.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.purge import runs_in
from media_hygiene.index.repository import FactsRepository
from media_hygiene.services.phone_holdings import Holdings, LibraryRow
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import SEPARATOR, PhoneCase, file_of
from media_hygiene.services.phone_proof import Ticked, prove
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.returned import remembered_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Mapping
    from pathlib import PurePosixPath

    from media_hygiene.services.phone_proof import Proof
    from media_hygiene.services.runtime import Runtime

_ROWS: Final = "SELECT path, size, mtime_ns, full_digest FROM files"
_BOM: Final = "﻿"
_FILE_FIELDS: Final = 4  # case, path, size, date
# The cases a file may leave the phone from: a new file was not imported.
_FREEABLE: Final = frozenset(
    {PhoneCase.LIBRARY, PhoneCase.DESTINATION, PhoneCase.SET_ASIDE}
)
PROVEN: Final = "proven"
KEPT: Final = "kept"


@dataclass(frozen=True, slots=True)
class ProveQuery:
    """The files ticked, where their staged copies are, and the import's folder."""

    ticked: tuple[Ticked, ...]
    staging: Path  # in the container
    destination: Path | None = None


def read_ticked(lines: Iterable[str]) -> tuple[tuple[Ticked, ...], int]:
    """Read the plan's lines of the files ticked in the page.

    Args:
        lines: The lines `mh` piped in.

    Returns:
        The files, each path once, in the order given; and the count of lines
        skipped (not a plan line, or a case that cannot leave the phone).
    """
    ticked: dict[PurePosixPath, Ticked] = {}
    skipped = 0
    texts = (raw.strip().lstrip(_BOM) for raw in lines)
    for text in filter(None, texts):
        fields = text.split(SEPARATOR)
        case = next((case for case in _FREEABLE if case.value == fields[0]), None)
        file = file_of(fields[1:_FILE_FIELDS]) if len(fields) >= _FILE_FIELDS else None
        if case is None or file is None:
            skipped += 1
            continue
        ticked.setdefault(file.path, Ticked(case, file, tuple(fields[_FILE_FIELDS:])))
    return tuple(ticked.values()), skipped


def prove_ticked(runtime: Runtime, query: ProveQuery) -> tuple[Proof, ...]:
    """Prove each file ticked against the library, the import and the journals.

    Args:
        runtime: Settings, mount points and output.
        query: The files and their staged copies.

    Returns:
        A proof per file, in the order given.
    """
    holdings = holdings_of(runtime, query)
    return tuple(
        prove(ticked, query.staging.joinpath(*ticked.file.path.parts), holdings)
        for ticked in query.ticked
    )


def holdings_of(runtime: Runtime, query: ProveQuery) -> Holdings:
    """Gather what the PC holds of contents of those sizes.

    Args:
        runtime: Settings, mount points and output.
        query: The files ticked.

    Returns:
        The index's files of the same sizes, the journals' memory, the quarantines.
    """
    sizes = frozenset(ticked.file.size for ticked in query.ticked)
    with FactsRepository.open(runtime.index_file) as repository:
        connection = repository.connection
        library = _library(connection, sizes)
        remembered = remembered_of(runtime, connection)
    return Holdings(
        mapper=runtime.mapper,
        library=library,
        remembered=remembered,
        quarantined=frozenset(runs_in(mounted_quarantines(runtime).folders)),
        destination=query.destination,
    )


def _library(
    connection: sqlite3.Connection, sizes: frozenset[int]
) -> Mapping[int, tuple[LibraryRow, ...]]:
    """List the files of the index of those sizes, staging copies left out.

    Args:
        connection: The index.
        sizes: The sizes of the files ticked.

    Returns:
        By size, the files in path order.
    """
    found: defaultdict[int, list[LibraryRow]] = defaultdict(list)
    for path, size, mtime_ns, full in connection.execute(_ROWS):
        if size in sizes and STAGING_PREFIX not in path:
            found[int(size)].append(LibraryRow(Path(path), int(mtime_ns), full))
    return MappingProxyType(
        {
            size: tuple(sorted(rows, key=lambda row: row.path))
            for size, rows in found.items()
        }
    )


def proof_line(proof: Proof) -> str:
    """Write a proof as `mh` reads it.

    Args:
        proof: The proof of one file.

    Returns:
        One line, its fields separated by tabs, without the line end.
    """
    file = proof.file
    head = (file.path.as_posix(), str(file.size))
    if proof.proven is None:
        fields: tuple[str, ...] = (KEPT, *head, proof.note)
    else:
        fields = (PROVEN, *head, proof.proven.value, proof.digest, proof.held)
        fields += (proof.note,)
    return SEPARATOR.join(text.replace(SEPARATOR, " ") for text in fields)
