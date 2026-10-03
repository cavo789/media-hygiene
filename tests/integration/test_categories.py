"""Categories with `--ext`: a user's mixed category, Czkawka's command, the messages."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.constants import MediaKind
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.crosscheck import czkawka_command
from tests.support.cli import run
from tests.support.media import MediaFactory
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

_WEB: Layer = {"scan": {"categories": {"web": ["png", "svg"]}, "extensions": ["web"]}}
_LOGO = b'<svg xmlns="http://www.w3.org/2000/svg"/>'


def test_a_mixed_category_decodes_images_and_quarantines_the_rest(
    locations: Locations,
) -> None:
    """PNG files stay images (deleted with --delete), SVG files are other files."""
    media = MediaFactory(locations.data_dir)
    media.copy(media.image("c/Site/logo.png", seed=1), "c/Site/old/logo.png")
    media.image("c/Site/photo.jpg", seed=2)
    for relative in ("c/Site/logo.svg", "c/Site/old/logo.svg"):
        (locations.data_dir / relative).write_bytes(_LOGO)
    runtime = make_runtime(locations, _WEB)
    findings = AuditService(runtime, NullProgress()).run()
    assert "Only analysed: web (png, svg)." in output_of(runtime)
    assert "Not photos or videos: .svg." in output_of(runtime)
    kinds = {decision.keeper.kind for decision in findings.plan.decisions}
    assert kinds == {MediaKind.IMAGE, MediaKind.OTHER}
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode(delete=True))
    plan = replace(findings.plan, delete_copies=True)
    run_id, outcome = service.execute(service.feasible(plan))
    assert outcome.quarantined == 1
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    assert {entry.action for entry in entries} == {
        ActionKind.QUARANTINE_DUPLICATE,
        ActionKind.DELETE_DUPLICATE,
    }


def test_czkawka_gets_the_extensions_of_the_categories(locations: Locations) -> None:
    """`-x` takes extensions only: categories are replaced by theirs."""
    runtime = make_runtime(locations, {"scan": {"extensions": ["video", "web"]}})
    assert "-x 3g2,3gp,avi," in czkawka_command(runtime).render()
    with_web = make_runtime(locations, _WEB)
    assert "-x png,svg " in czkawka_command(with_web).render()


def test_config_lists_every_category(cli: CliRunner, locations: Locations) -> None:
    """Built-in categories and the user's ones, with their extensions and origin."""
    locations.config_file.write_text('[scan.categories]\ndocuments = ["pdf"]\n')
    output = run(cli, "config").output
    assert "Extension categories (--ext)" in output
    assert "built-in" in output
    assert "documents" in output
    assert "pdf" in output
