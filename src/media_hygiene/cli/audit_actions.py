"""Show what an audit lets the user do, with gain and effort, before the report."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.report.actions import (
    ActionCommands,
    AuditAction,
    actions_title,
    audit_actions,
)
from media_hygiene.services.next_command import CHANGING, NextVerb, next_command

if TYPE_CHECKING:
    import typer

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


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
    )
    actions = audit_actions(findings, commands)
    if actions:
        output = runtime.output
        output.info(f"[bold]{actions_title()}[/]")
        for action in actions:
            output.info(f"{action.icon} {action.text}")
        output.blank()
    return actions
