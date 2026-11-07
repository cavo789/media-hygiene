"""*Try on one month* of the Events tab (0640): `sort --trial latest` from the page.

The same cut, guards, journal and `undo` as the command; the files set aside stay in
place (0518). The answers are read back: the run's own entries, where the files went.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import open_trial
from media_hygiene.errors import MediaHygieneError, WorkbookError
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.aside_paths import set_aside
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_event import not_aside
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from media_hygiene.services.sort_trial import first_sample, latest_month
from media_hygiene.services.sort_trial_run import TrialRun, read_back

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_inputs import SortInputs
    from media_hygiene.services.sort_models import Prepared, SortResult


@dataclass(frozen=True, slots=True)
class SortTrial:
    """Offers and runs the trial of the latest classify plan."""

    runtime: Runtime

    def offer(self) -> dict[str, object] | None:
        """What the button says, or nothing when no trial applies.

        Returns:
            The month, its files and their folders, the whole sort's files; None
            without a plan, once a run moved files of it, or with one month to move.
        """
        try:
            whole = self._whole()
            sample = self._sample(whole)
        except MediaHygieneError:
            return None
        if sample is None:
            return None
        goes = Counter(
            self.runtime.mapper.to_host(group.folder)
            for group in sample.plan.groups
            for _move in group.moves
        )
        return {
            "month": latest_month(whole.inputs),
            "files": len(sample.plan.moves),
            "total": len(whole.plan.moves),
            "folders": [
                {"folder": path, "files": n} for path, n in sorted(goes.items())
            ],
        }

    def running(self) -> TrialRun | None:
        """The trial still open, read from the journal: a reload finds it back (0648).

        Returns:
            The run as it stands, or None: no trial, undone, or the sort went on.
        """
        try:
            inputs = self._inputs()
            journal = self.runtime.locations.journal_dir
            trial = open_trial(journal, inputs.plan.plan_id)
            if trial is None:
                return None
            rest = len(self._whole().plan.moves)
        except MediaHygieneError:
            return None
        return read_back(trial, rest)

    def run(self) -> TrialRun:
        """Sort the latest month.

        Returns:
            The run, read back.

        Raises:
            WorkbookError: No trial applies any more (sorted meanwhile).
        """
        sample = self._sample(self._whole())
        if sample is None:
            raise WorkbookError(_("No month left to try: files of this plan moved."))
        return self._executed(sample)

    def rest(self) -> TrialRun:
        """Sort what is left of the plan.

        Returns:
            The run, read back; no run id when nothing is left to move.
        """
        whole = self._whole()
        if not whole.plan.groups:
            return TrialRun("", 0, 0, intact=True, targets=(), rest=0)
        return self._executed(whole)

    def _service(self) -> SortService:
        """The sort, refused before anything when it is not possible here.

        Returns:
            It.
        """
        service = SortService(self.runtime, NullProgress())
        service.ensure_ready()
        return service

    def _inputs(self) -> SortInputs:
        """The latest plan, without the files set aside.

        Returns:
            Its inputs.
        """
        runtime = self.runtime
        inputs = load_inputs(runtime, find_workbook(runtime, None))
        return not_aside(inputs, set_aside(runtime))

    def _whole(self) -> Prepared:
        """The sort of what is left of the plan.

        Returns:
            It, ready.
        """
        return self._service().prepare(self._inputs())

    def _sample(self, whole: Prepared) -> Prepared | None:
        """The latest month of that sort.

        Args:
            whole: The sort.

        Returns:
            The sample, or None when no trial applies.
        """
        return first_sample(self.runtime, whole, self._service().prepare)

    def _executed(self, prepared: Prepared) -> TrialRun:
        """Run a sort, then count what is left.

        Args:
            prepared: The sort.

        Returns:
            The run, read back.
        """
        result: SortResult = self._service().execute(prepared, lambda: False)
        manifest = result.manifest
        return TrialRun(
            result.run_id,
            manifest.moved,
            manifest.verified,
            intact=manifest.intact,
            targets=tuple(
                sorted(
                    Path(entry.target) for entry in result.moves.moved if entry.target
                )
            ),
            rest=len(self._whole().plan.moves),
        )
