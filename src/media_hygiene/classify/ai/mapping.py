"""Map descriptions to the categories of a `subject` rule: text only, in batches.

A new list of categories costs seconds, not a night: the descriptions stay, only this
step runs again, and its answers are cached too. A batch whose answer does not hold
one known category per description is asked again one description at a time.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.ai.prompts import map_request, read_mapping, version

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.ai.client import OllamaClient
    from media_hygiene.index.descriptions import DescriptionStore
    from media_hygiene.scan.progress import ProgressSink


@dataclass(frozen=True, slots=True)
class MapDeps:
    """What mapping needs: the model, the cache, the progress."""

    client: OllamaClient
    store: DescriptionStore
    progress: ProgressSink


async def map_all(
    summaries: Sequence[str], categories: Sequence[str], deps: MapDeps
) -> dict[str, str]:
    """Choose a category for every description.

    Args:
        summaries: The descriptions (duplicates are asked once).
        categories: The rule's categories.
        deps: Model, cache and progress.

    Returns:
        The category of each description the model answered (empty: none fits).
    """
    model = deps.client.settings.text_model
    keys = {
        text: mapping_key(text, model, categories) for text in dict.fromkeys(summaries)
    }
    found: dict[str, str] = {}
    for text, key in keys.items():
        cached = deps.store.mapping(key)
        if cached is not None:
            found[text] = cached
    missing = [text for text in keys if text not in found]
    size = deps.client.settings.batch_size
    for start in range(0, len(missing), size):
        batch = missing[start : start + size]
        for text, category in (await _ask(batch, categories, deps)).items():
            deps.store.put_mapping(keys[text], category)
            found[text] = category
        deps.progress.advance()
    return found


def batches(count: int, size: int) -> int:
    """How many calls mapping `count` new descriptions takes.

    Args:
        count: Descriptions not mapped yet.
        size: `batch_size`.

    Returns:
        The number of batches.
    """
    return -(-count // size)


def mapping_key(text: str, model: str, categories: Sequence[str]) -> str:
    """The key of one mapping: everything the answer depends on.

    Args:
        text: The description.
        model: The text model.
        categories: The rule's categories, in order.

    Returns:
        A SHA-256 digest.
    """
    parts = [model, version("map"), list(categories), text]
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()


async def _ask(
    batch: Sequence[str], categories: Sequence[str], deps: MapDeps
) -> dict[str, str]:
    """Ask for one batch; one description at a time when the answer is unusable.

    Args:
        batch: The descriptions.
        categories: The rule's categories.
        deps: Model, cache and progress.

    Returns:
        The category of each description answered.
    """
    model = deps.client.settings.text_model
    content = await deps.client.chat(map_request(model, batch, categories))
    answers = read_mapping(content, len(batch), categories)
    if answers is not None:
        return dict(zip(batch, answers, strict=True))
    if len(batch) == 1:
        return {}  # asked again at the next run
    found: dict[str, str] = {}
    for text in batch:
        found.update(await _ask((text,), categories, deps))
    return found
