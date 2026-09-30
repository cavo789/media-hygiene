# 0043 — Skip folders by name, wherever they are (`--exclude-name Thumbnails`)

- **Priority**: Medium — the built-in list misses some trash folders (see Context)
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/filters.py`, `src/media_hygiene/constants.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/services/policy.py`, `src/media_hygiene/services/data_checks.py`, `src/media_hygiene/cli/options.py`, `src/media_hygiene/cli/context.py`, `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/cli/cmd_crosscheck.py`, `src/media_hygiene/cli/cmd_config.py`, `src/media_hygiene/crosscheck/czkawka.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/05-choose-the-kept-copy.md`, `documentation/fr/05-choose-the-kept-copy.md`, `documentation/en/07-configuration-file.md`, `documentation/fr/07-configuration-file.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `tests/unit/test_scan_basics.py`, `tests/unit/test_config.py`, `tests/unit/test_crosscheck_compare.py`

## Context

Two ways to leave folders out today:

- `[folders] excluded` / `--exclude`: **host paths** (`D:\backup`), one precise folder each;
- `EXCLUDED_DIR_NAMES` (system folders: `$recycle.bin`, `system volume information`, `@eadir`,
  `#recycle`, `.trash`) and `APP_DIR_NAMES` (software folders, other file types only): **names**
  skipped wherever they are, built in, not configurable, matched exactly.

[sorta](https://github.com/shinKatana0/sorta/blob/main/config.example.yaml#L62) has a
configurable `skip_dirs` name list. Here, a folder that comes back on every disk
(`Thumbnails`, `Lightroom Previews`, a NAS's own recycle bin) must be listed path by path.

The built-in list also has gaps, to verify one by one before adding them: `.Trash-1000`
(Linux trash on an external disk; `.trash` only matches that exact name), `.Trashes` (macOS),
`@Recycle` (QNAP), `.@__thumb` (QNAP thumbnails), `.thumbnails` (Linux thumbnail cache, in
sorta's list). A trash folder is not only noise: its copy may be the one kept
(`KeepPolicy` does not know it is a trash), then the user empties the trash and the photo is
gone.

## Proposal

- `[scan] excluded_names = []` and `--exclude-name` (repeatable, comma-separated like `--ext`),
  env `MEDIA_HYGIENE_SCAN__EXCLUDED_NAMES` (JSON array, already supported).
  Same meaning as `excluded`: not analysed, neither deleted nor used as the kept copy.
- **Patterns are globs** (`fnmatch`), whole folder name, case ignored: `Thumbnails`,
  `.Trash-*`, `*.lrdata`. Not regular expressions like `[keep]`: `$RECYCLE.BIN` as a regex never
  matches (`$` is an anchor), and folder names are typed by people who know `*`, not `\d+`.
  The comment in `config.toml.j2` says why the two sections differ.
- **The user list adds to the built-in one**, it never replaces it: skipping a system folder has
  no downside, analysing it has one. The built-in names become globs too (`.trash-*`).
  `media-hygiene config` shows the built-in names, like it shows `generated_names`.
- Validation: a value holding `/` or `\` is refused with *"that is a path: use --exclude"*;
  empty values dropped.
- `ScanFilters.skips_dir` checks the patterns; the walker, the crosscheck comparison
  (`crosscheck/compare.py`) and the index pruning (`index/pruning.py`) already call it.
- The audit's scope warning (`data_checks.py`) lists the names asked for.
- Czkawka command: `-E "*/Thumbnails/*"` per name (its `--excluded-items` takes wildcards), so
  it does not hash files that the comparison would set aside anyway.
- Size limits: `constants.py` is at 200 lines, `settings.py` at 193 and `options.py` at 187:
  the folder name lists may move to `scan/skipped_dirs.py`; if 0042 is done first,
  `ScanSettings` may already live in its own module.

## Acceptance

- [ ] `--exclude-name Thumbnails` and `excluded_names = [".Trash-*"]` skip those folders on
  every disk, whatever their case; `--exclude` (paths) is unchanged.
- [ ] Each new built-in name is checked against a real system (or its documentation) before it
  is added; an audit of a tree holding `.Trash-1000/files/IMG_1.jpg` next to
  `Photos/IMG_1.jpg` reports no duplicate.
- [ ] A path given to `--exclude-name` is refused with a message pointing to `--exclude`.
- [ ] The crosscheck command and comparison agree with the audit on skipped folders.
- [ ] `config.toml` template, `--exclude-name` help, `media-hygiene config`, scope warning;
  strings translated (`i18n_update`).
- [ ] Steps 5 and 7 and the command reference updated in `documentation/en` and
  `documentation/fr`.
