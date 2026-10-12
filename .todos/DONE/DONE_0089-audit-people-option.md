# 0089 — `audit --people`: find the faces after the audit, once the user agreed to the time

- **Priority**: Medium — asked by the maintainer (review of 0058, 2026-10-11)
- **Batch**: people
- **Depends**: 0058
- **Files**: `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/people_flow.py`, `src/media_hygiene/services/people.py`, `src/media_hygiene/services/people_find.py`, `src/media_hygiene/console/people_view.py`, `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/audit.md`, `documentation/fr/commands/audit.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `tests/integration/people/`

## Context

`people` finds the faces on its own, so an audit is never slowed (0058). The maintainer
would like a single run to do both, on request: `audit --people`. It must say that the run
gets slower, and ask before it starts.

Measured on the maintainer's PC (2026-10-11, image with 0058): about 0.2 s per photo per
worker, decoding included (0.22 s on 2023, 0.17 s on 2022). Half the CPUs work (`workers()`).
That makes about 45 minutes for 50,000 photos with 4 workers, and only once: the next runs
analyse the new photos only.

## Goal

`audit --people` (and `[people] with_audit = false` in `config.toml`, for those who always want
it) runs the audit as today, then, before any face is looked for:

1. **Count**: the healthy photos of the audited folders with no faces in the index yet. The
   count is exact: the audit just listed them (no estimate needed). Nothing to do: one line,
   no question.
2. **Measure on this PC**: analyse a small random sample (`people --sample` logic, about 10
   photos or 5 seconds, whichever comes first). Those faces are kept, nothing is wasted.
3. **Say and ask**: one line with the count and the estimate, then the question.
   > 12,345 photos have not been looked at for faces yet: about 25 minutes on this PC
   > (measured on 10 photos). The audit is done; look for the faces now? [y/N]
   Ctrl+C stops between two photos, the faces found are kept, and the next run goes on
   (say so in the same lines).
4. **Yes**: the `people` analysis with its progress bar, then the summary of the groups. No
   page opens (the audit is not a page command); the last line points at `people` to see them.
   **No**: one line saying that `people` (or the next `audit --people`) does it later.

Confirmation like `sort` and `clean`: `--yes` skips it. Without a terminal (`docker run`
without `-it`, a script), never wait for an answer: say that `--yes` is needed, and finish
the audit without faces.

The models download (first use) happens after the yes, never before.

## Acceptance

- `audit` alone never finds faces and is not slower.
- `audit --people` counts, measures, asks; no, Ctrl+C and no terminal leave a finished audit.
- `--yes` runs without asking; the faces land in the index (`status` shows them).
- Docs (en + fr): `commands/audit.md`, `reference-people.md`, `reference-commands.md`, help
  capture; French translations.
