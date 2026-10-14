"""Show what an audit lets the user do, with gain and effort, before the report."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.next_steps import carried
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.i18n import _
from media_hygiene.report.actions import (
    ActionCommands,
    AuditAction,
    actions_title,
    audit_actions,
)
from media_hygiene.services.crosscheck import (
    crosscheck_command,
    czkawka_command,
    czkawka_executable,
)
from media_hygiene.services.next_command import CHANGING, NextVerb, next_command

if TYPE_CHECKING:
    import typer

    from media_hygiene.plan.models import AuditFindings, CleanPlan
    from media_hygiene.services.runtime import Runtime

# Below this many copies, a second tool is noise on a first try: shown when verbose.
SECOND_OPINION_FROM: Final = 100


def show_actions(
    ctx: typer.Context, runtime: Runtime, findings: AuditFindings
) -> tuple[AuditAction, ...]:
    """Print the actions, at most three lines, and hand them to the report.

    Args:
        ctx: Typer context of the audit, whose options the commands keep.
        runtime: Settings, mount points and output.
        findings: The audit.

    Returns:
        The actions, with the full command of each.
    """

    def command(verb: str, *, changes: bool = True, port: int | None = None) -> str:
        """Build the full command of one action.

        Args:
            verb: The command and its own options.
            changes: Whether the command modifies the data mounts.
            port: The port its page listens on, if it serves one.

        Returns:
            The command, ready to paste.
        """
        needs = CHANGING if changes else ()
        built = next_command(
            runtime, NextVerb(carried(runtime, verb, ctx), needs, port)
        )
        return built.command

    commands = ActionCommands(
        clean=command("clean"),
        near=command("clean --tier near"),
        review=command("review", changes=False, port=PAGE_PORT),
        near_review=command("review --near", changes=False, port=PAGE_PORT),
    )
    actions = audit_actions(findings, commands)
    if actions:
        output = runtime.output
        output.info(f"[bold]{actions_title()}[/]")
        for action in actions:
            output.info(f"{action.icon} {action.text}")
        output.blank()
    return actions


def second_opinion(runtime: Runtime, plan: CleanPlan) -> None:
    """Suggest a second opinion before a large clean: `crosscheck`, or Czkawka.

    On a small audit (a first try), the setup hints and `--prefer` matter more: the
    tip then needs `--verbosity verbose`; the `clean` confirmation names `crosscheck`.

    Args:
        runtime: Settings, mount points and output.
        plan: What the audit proposes to set aside.
    """
    if not plan.decisions:  # broken files or orphan sidecars alone: no copy
        return
    if plan.removable_count < SECOND_OPINION_FROM and not runtime.output.verbose:
        return
    if czkawka_executable() is not None:
        runtime.output.advise(
            Advice(
                TipKind.DISCOVERY,
                _(
                    "Second opinion: 'crosscheck' runs Czkawka, an independent "
                    "duplicate finder, on the same folders, then compares group by "
                    "group:"
                ),
                crosscheck_command(runtime, carried(runtime, "crosscheck")),
            )
        )
        return
    runtime.output.advise(
        Advice(
            TipKind.DISCOVERY,
            _(
                "Second opinion: run Czkawka, an independent duplicate finder, on "
                "the same folders, then 'media-hygiene crosscheck' "
                "(same -v options):"
            ),
            czkawka_command(runtime).render(),
        )
    )
