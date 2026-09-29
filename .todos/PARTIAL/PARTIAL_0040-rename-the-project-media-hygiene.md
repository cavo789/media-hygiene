# 0040 — Rename the project to `media-hygiene`

- **Priority**: Critical — not a bug: first by decision (2026-09-29), since every session run before it adds files to rename and leaves stale paths in the TODOs
- **Batch**: rename
- **Depends**: —
- **Files**: `pyproject.toml`, `uv.lock`, `src/media_dedup/` (→ `src/media_hygiene/`), `tests/`, `Dockerfile`, `.github/workflows/ci.yml`, `.devcontainer/devcontainer.json`, `.devcontainer/scripts/`, `README.md`, `README_FR.md`, `documentation/en/`, `documentation/fr/`, `CLAUDE.md`, `.todos/`

## Context

Decided on 2026-09-29. The tool no longer only deduplicates: `classify` / `sort` (0026–0036)
and the inventory (0032) are coming. "Digital hygiene" / "hygiène numérique" covers the three
things it does: **clean** (duplicates, broken files), **tidy** (classify, sort), **protect**
(journal, quarantine, `undo`). The word is the same in French and English.

Checked on 2026-09-29: no photo tool is called `media-hygiene`. Taken, hence rejected:
`media-curator`, Photo Curator, PhotoSift, PhotoSort, Tidy, ImageRanger, medialibrarian,
Media Triage, Shoebox.

Measured: 256 tracked files, about 1,500 occurrences of `media_dedup` / `media-dedup` /
`MEDIA_DEDUP`.

## Proposal

| What | Before | After |
|---|---|---|
| Docker image | `cavo789/media-dedup` | `cavo789/media-hygiene` |
| Command (`ENTRYPOINT`, script) | `media-dedup` | `media-hygiene` |
| Python package | `media_dedup` | `media_hygiene` |
| Distribution (`pyproject.toml`) | `media-deduplication-pipeline` | `media-hygiene` |
| Environment prefix | `MEDIA_DEDUP_` | `MEDIA_HYGIENE_` |
| gettext catalog | `media_dedup.po` | `media_hygiene.po` |
| Volumes suggested in the docs | `media-dedup-cache`, `media-dedup-review` | `media-hygiene-cache`, `media-hygiene-review` |
| GitHub repository | `cavo789/media-deduplication-pipeline` | `cavo789/media-hygiene` |

**One mechanical commit first**: `git mv src/media_dedup src/media_hygiene`, then replace the
names, `check` green. Nothing else in it, so it reads as a rename in review. Compatibility and
docs follow in their own commits.

**Users of 0.2.x lose nothing**:
- `MEDIA_DEDUP_*` variables are still read for one minor version, with a warning naming the
  new variable; `MEDIA_HYGIENE_*` wins when both are set.
- `/cache`, `/journal`, `/quarantine`, `/reports` and `config.toml`: no file name holds the
  project name, so nothing to migrate. Check it (index, journals, report folders, decisions
  file), and test that the renamed tool reads a 0.2.0 index, journal and decisions file.
- The volume suggested in the docs changes name. An existing `media-dedup-cache` keeps working
  when the user keeps writing its name; the release note says so ("or let the next audit
  rebuild the cache").

**Publishing**:
- CI publishes `cavo789/media-hygiene` (`IMAGE` in `ci.yml`). Docker Hub cannot rename a
  repository: the description of `cavo789/media-dedup` gets a last edit pointing to the new
  image (manual step, listed in the release).
- Bump the minor version (0.3.0) and say it in the release.
- GitHub: rename the repository (GitHub redirects old URLs and remotes), update `origin`.

**Developer side**:
- The devcontainer's own volumes (`media-dedup-claude`, `-bashhistory`, `-config`) **keep their
  names**, with a comment in `devcontainer.json`: users never see them, and a new
  `media-hygiene-claude` would start without Claude Code's login and settings. Claude's memory
  is safe either way: it lives in `.claude/memory/`, relinked by `post-create.sh` from
  `WORKSPACE_DIR`.
- The `dedup` helper becomes `hygiene` (cheatsheet, `CLAUDE.md`).
- Documentation text and captures: `docs_screenshots` regenerates the terminal screenshots
  that show `media-dedup audit`.
- Open TODOs (`.todos/*.md`): paths and names updated; `DONE/` and `UNNEEDED/` stay as history.

## Acceptance

- [ ] `git grep -i "media.dedup"` finds only: the old-prefix compatibility code and its test,
      the release note, the devcontainer volume names, `.todos/DONE/` and `.todos/UNNEEDED/`.
- [ ] `check` and `e2e` green with the new image name.
- [ ] A 0.2.0 index, journal and decisions file are read by the renamed tool (test).
- [ ] `MEDIA_DEDUP_GENERAL__LOCALE=fr` still works, with a warning; `MEDIA_HYGIENE_…` wins.
- [ ] READMEs and documentation en + fr renamed, captures regenerated.

## Status — PARTIAL (2026-09-29)

### Done
- Mechanical rename (commit `d2b1921`): package, command, distribution, environment prefix,
  gettext catalogs, CI image name, the `dedup` helper now `hygiene`; nine lines grown past 88
  columns reworded.
- Compatibility (`61925c2`): `MEDIA_DEDUP_*` copied to the new names first thing in `main()`,
  one warning lists them (`config/legacy_env.py`, to delete in 0.4.0); `summary.json` writes
  `only_ours` and still reads 0.2's `only_media_dedup`; `tests/fixtures/0.2.0/` (index,
  journal, decisions, cross-checked summary written by the real 0.2.0) read by the renamed
  tool; "Coming from media-dedup" in both READMEs; configuration page; version 0.3.0.
- Captures regenerated en + fr with `docs_screenshots`, `CLAUDE.md`, comment on the
  devcontainer volumes (`3f05920`).
- `git grep -i "media.dedup"`: only the expected places, plus `.claude/settings.json` (below).
- Pre-commit gate green; targeted tests and `pytest -m e2e` (4 passed) on
  `media-hygiene:latest`.

### Not done
- Rename the GitHub repository to `cavo789/media-hygiene` (Settings → General, or
  `gh repo rename media-hygiene`), then `git remote set-url origin
  git@github.com:cavo789/media-hygiene.git`.
  **Reason:** outward-facing, on the maintainer's account; do it when this branch reaches
  `main`, so that the links of the documentation point to an existing repository.
- Publish 0.3.0: merge into `main`, push, run the full `check`, then `release` (tag `v0.3.0`):
  CI pushes `cavo789/media-hygiene:0.3.0` and `:latest`.
  **Reason:** a release is the maintainer's decision.
- Edit the Docker Hub description of `cavo789/media-dedup`: "Renamed: see
  cavo789/media-hygiene".
  **Reason:** manual step on hub.docker.com, with the maintainer's account.
- `.claude/settings.json` lists the paths of the current local folder
  (`/workspaces/media-deduplication-pipeline`): update them when the repository is cloned
  again under its new name.
  **Reason:** they must match the folder on disk, which only changes at the next clone.
