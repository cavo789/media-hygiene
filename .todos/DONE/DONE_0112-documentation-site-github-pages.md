# 0112 — Publish the documentation on GitHub Pages: the links the tool prints open a web page

- **Priority**: Medium — every guide link printed by the CLI opens GitHub's code browser, and is too long for 80 columns
- **Batch**: docs
- **Depends**: —
- **Files**: `.github/workflows/docs.yml`, `mkdocs.yml`, `pyproject.toml`, `src/media_hygiene/constants.py`, `src/media_hygiene/services/missing_mount.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_documentation.py`, `README.md`, `README_FR.md`, `documentation/en/development.md`, `documentation/fr/development.md`

## Context

The CLI points beginners to the guide (`DOC_PAGES` in `constants.py` =
`https://github.com/cavo789/media-hygiene/blob/main`, plus a translated page path such as
`documentation/en/start/01-first-audit.md`). Two problems:

- The page opens in GitHub's repository interface (file tree, code toolbar), not as a
  documentation page: a beginner lands in a developer tool.
- The URL is ~110 characters: wider than a default terminal, so it wraps on screen (the 📖
  line of `Output.link` keeps it one logical line and an OSC 8 hyperlink, but it stays long).

A GitHub Pages site would read `https://cavo789.github.io/media-hygiene/en/start/01-first-audit/`
(~65 characters).

## Goal

- A workflow `.github/workflows/docs.yml` builds `documentation/` with MkDocs Material on every
  push to `main` touching `documentation/` (and on demand) and deploys it with
  `actions/deploy-pages` (pinned versions). `documentation/` keeps its files as they are: the
  Markdown stays readable on GitHub too.
- `mkdocs.yml`: `docs_dir: documentation`, English and French (language switch between the same
  file names of `en/` and `fr/`), navigation in the order of the guides (`start/`, `clean/`,
  `sort/`, `commands/`, references, developer page last), search, `images/` served. The
  `<!-- capture: … -->` blocks and screenshots render unchanged; `mkdocs build --strict` fails
  on a broken link or anchor.
- `DOC_PAGES` becomes the site root; the translated page paths of `_()` become site paths
  (`en/start/01-first-audit/`, `en/reference-safety/`) — both callers (`missing_mount.no_folder`,
  `safety.safety_doc`) and the French catalog follow (`i18n_update`).
- README / README_FR link the site next to the GitHub pages; Docker Hub's description (the
  README) gets the short links too.
- The developer page says how to preview the site locally (a helper in
  `.devcontainer/scripts/helpers/`, e.g. `docs_serve`, never a Makefile), the MkDocs dependencies
  in a dev dependency group of `pyproject.toml`, the build output in `/tmp`.

## Manual step (maintainer)

Repository settings → Pages → Source: **GitHub Actions**. Do not switch `DOC_PAGES` before the
first deployment is live: the CLI would print links to missing pages.

## Acceptance

- `mkdocs build --strict` passes locally and in the workflow.
- A unit test checks that every documentation URL the CLI can print (`DOC_PAGES` + each
  translated page path, both languages) maps to an existing file of `documentation/`.
- `https://cavo789.github.io/media-hygiene/en/start/01-first-audit/` and its `fr/` twin open
  the guide; the ❌ "No folder to analyse" line prints that link.
