"""`clean --decisions`: refuse a folder pair decision touching what must stay."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.plan.pair_links import link_refusal
from media_hygiene.plan.review import PairAction
from media_hygiene.services.policy import keep_policy

if TYPE_CHECKING:
    from media_hygiene.plan.pairs import FolderPair
    from media_hygiene.services.runtime import Runtime


def check_pair(runtime: Runtime, pair: FolderPair, action: PairAction) -> None:
    """Refuse a swap or a link the pair does not allow.

    Args:
        runtime: Settings, mount points and output.
        pair: The folder pair.
        action: What the review decided for it.

    Raises:
        DecisionsError: A swap inside one folder or from a protected folder; a link
            across drives, or to a protected folder.
    """
    if action is PairAction.SWAP:
        _check_swap(runtime, pair)
    elif action is PairAction.LINK:
        _check_link(runtime, pair)


def _check_swap(runtime: Runtime, pair: FolderPair) -> None:
    """Refuse a swap that would delete what must stay.

    Args:
        runtime: Settings, mount points and output.
        pair: The folder pair, swapped.

    Raises:
        DecisionsError: The pair is inside one folder, or its kept folder is protected.
    """
    kept = runtime.mapper.to_host(pair.kept_in)
    if pair.kept_in == pair.removed_from:
        message = _("{folder}: copies inside one folder cannot be swapped.")
        raise DecisionsError(message.format(folder=kept))
    protected = keep_policy(runtime.settings, runtime.mapper).protected
    if any(is_within(pair.kept_in, folder) for folder in protected):
        message = _("{folder} is protected: its copies are always kept.")
        raise DecisionsError(message.format(folder=kept))


def _check_link(runtime: Runtime, pair: FolderPair) -> None:
    """Refuse a pair keeping both names that hard links cannot serve (0213).

    Args:
        runtime: Settings, mount points and output.
        pair: The folder pair, its copies to become links.

    Raises:
        DecisionsError: The folders are on two drives, or the kept one is protected.
    """
    protected = keep_policy(runtime.settings, runtime.mapper).protected
    reason = link_refusal(pair, runtime.mapper, protected)
    if reason is None:
        return
    message = _("{kept} -> {removed}: both names cannot be kept ({reason}).")
    raise DecisionsError(
        message.format(
            kept=runtime.mapper.to_host(pair.kept_in),
            removed=runtime.mapper.to_host(pair.removed_from),
            reason=reason,
        ),
        _("Choose another decision for this pair, or leave it as planned."),
    )
