"""What a `subject` rule asks the model: the units, their samples, what is missing.

The rules run once without the `subject` rules: whatever they decide is never sent.
The samples of each unit come from the photos left; those not in the cache are the
work of this run, and its estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.classify.ai.sampling import choose_samples, units_of
from media_hygiene.classify.engine import classify
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.index.descriptions import PhotoVersion

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.ai.models import Unit
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.index.descriptions import DescriptionStore
    from media_hygiene.services.classify_inputs import ClassifyInputs


@dataclass(frozen=True, slots=True)
class SubjectPlan:
    """The units to ask about, their samples, and the samples not described yet."""

    rules: tuple[ClassifyRule, ...]
    units: tuple[Unit, ...]
    samples: Mapping[str, tuple[Path, ...]]
    versions: Mapping[Path, PhotoVersion]
    missing: tuple[PhotoVersion, ...]
    seconds_per_photo: float

    @property
    def sample_count(self) -> int:
        """How many photos answer for their units.

        Returns:
            The number of samples, described or not.
        """
        return sum(len(paths) for paths in self.samples.values())

    @property
    def estimate(self) -> float:
        """How long describing the missing samples should take.

        Returns:
            Seconds.
        """
        return len(self.missing) * self.seconds_per_photo


def subject_rules(settings: ClassifySettings) -> tuple[ClassifyRule, ...]:
    """The `subject` rules that are on.

    Args:
        settings: `[classify]`.

    Returns:
        Them, in order; `score = 0` turns one off.
    """
    return tuple(
        rule
        for rule in settings.rules
        if rule.match is RuleMatch.SUBJECT and rule.score != 0
    )


def plan_subjects(
    inputs: ClassifyInputs, settings: ClassifySettings, store: DescriptionStore
) -> SubjectPlan:
    """Find what the model would be asked about.

    Args:
        inputs: The files and the scope.
        settings: `[classify]`, with its `[classify.ai]` table.
        store: The descriptions already made.

    Returns:
        The plan.

    Raises:
        ConfigError: No model is set.
    """
    ai = settings.ai
    if not ai.model:
        raise ConfigError(
            _("A 'subject' rule or --sample needs a vision model."),
            escape(_("Set [classify.ai] model in config.toml, or remove the rule.")),
        )
    rules = subject_rules(settings)
    others = tuple(r for r in settings.rules if r.match is not RuleMatch.SUBJECT)
    first = classify(
        inputs.files, settings.model_copy(update={"rules": others}), inputs.scope
    )
    units = units_of(first.proposals, ai)
    versions = {f.path: PhotoVersion(f.path, f.size, f.mtime_ns) for f in inputs.files}
    described = frozenset(
        c.path
        for unit in units
        for c in unit.candidates
        if store.get(versions[c.path]) is not None
    )
    count = 0 if any(rule.per_photo for rule in rules) else ai.samples_per_event
    samples = {unit.key: choose_samples(unit, count, described) for unit in units}
    chosen = dict.fromkeys(p for paths in samples.values() for p in paths)
    return SubjectPlan(
        rules,
        units,
        samples,
        versions,
        tuple(versions[p] for p in chosen if p not in described),
        store.seconds_per_photo() or ai.seconds_per_photo,
    )
