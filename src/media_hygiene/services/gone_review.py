"""`clean --decisions`: the answers of `review --gone`, matched to the index's records.

An answer is about one version of a file (host path, size, modification time): one
the index no longer records (answered already, reappeared since) is left out, said.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _
from media_hygiene.index.gone_rows import gone_records
from media_hygiene.index.repository import FactsRepository
from media_hygiene.plan.gone import GoneAnswer

if TYPE_CHECKING:
    from media_hygiene.report.gone_decisions import GoneEntry
    from media_hygiene.services.runtime import Runtime


def gone_answers(
    runtime: Runtime, entries: tuple[GoneEntry, ...]
) -> tuple[GoneAnswer, ...]:
    """Match the answers to the files gone the index records.

    Args:
        runtime: Settings, mount points and output.
        entries: The `gone` key of the decisions file.

    Returns:
        The answers whose file is still recorded as gone.
    """
    if not entries or runtime.index_file is None:
        return ()
    mapper = runtime.mapper
    with FactsRepository.open(runtime.index_file) as repository:
        records = {
            (mapper.to_host(Path(record.path)), record.size, record.mtime_ns): record
            for record in gone_records(repository.connection)
        }
    answers = tuple(
        GoneAnswer(record, entry.deleted)
        for entry in entries
        if (record := records.get((entry.path, entry.size, entry.mtime_ns)))
    )
    deleted = sum(answer.deleted for answer in answers)
    if answers:
        runtime.output.info(
            _(
                "Your decisions — files deleted in the Explorer on purpose: "
                "{deleted}, moved elsewhere: {moved}."
            ).format(
                deleted=human_number(deleted),
                moved=human_number(len(answers) - deleted),
            )
        )
    return answers
