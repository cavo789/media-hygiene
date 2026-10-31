# 0550 — Tidy config.toml: remove the entries that point at nothing any more

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/config/, src/media_hygiene/places/ (tomlkit writer), src/media_hygiene/classify/, src/media_hygiene/cli/, src/media_hygiene/cli/menu_catalog_*.py, documentation/en|fr/commands/
- **Needs maintainer**: the questions below, asked when the TODO runs

## Context

The maintainer's `config.toml` (2026-10-31) keeps growing with entries that no longer
match anything, e.g. a `[[places.folders]]` whose folder
`C:\Photos\2010\Juillet 2010\Bretagne\13 Juillet\Quimper` was renamed or sorted away, or a
`[[classify.rules]]` with `match = "path"` and `pattern = '(?i)week-end dinant'` that no
indexed path matches any more (the photos were sorted into
`Vacances et sorties/Week-end à Dinant 2020`). Goal: keep the file short and readable,
without ever losing an entry that is still useful.

## Wanted

A check that lists the stale entries, with the reason for each, then removes the ones the
user ticks: **shown before it acts** (memory: seeing first), on a page (memory: visible in
web or nonexistent), plus a CLI verb if it is useful in the console.

Stale entries to detect (each checked against the disk and the index, never guessed):

| Entry | Stale when |
|---|---|
| `[[places.folders]]` | its `folder` does not exist |
| `[[classify.rules]]` `match = "path"` | its `pattern` matches no path of the index |
| `[[classify.rules]]` `match = "camera"` | its `pattern` matches no camera of the index |
| `[[classify.rules]]` `date_range` | no indexed photo falls in its dates (to show, untick by default: a rule written before importing) |
| `[[classify.clocks]]` | no photo of that camera within its dates |
| `[[classify.place_photos]]`, **line by line** in `photos` (maintainer's example 2026-10-31: 15 lines `C:\Photos\I Phone\IMG_00xx` under `place = "Maison"`) | its `path` does not exist: if its `sha256` (+ `size`) is found elsewhere in the index (moved by `sort`, renamed), **update the path** instead (workflow.md move rules); else remove the line. The whole block goes when its last line goes |
| `[folders] preferred / protected / excluded / backup` | a folder that does not exist |
| Town renames | the GeoNames name is unknown (a typo) |
| `people` | a `/config/people/<name>.toml` linked but missing, or a file in `/config/people/` linked by nobody |
| Duplicates | two identical entries (same folder, same rule) |

Never proposed for removal: `[[classify.places]]` and `[[places.ignored]]` (drawn by hand,
still valid for future photos) — at most shown as "no photo yet".

Safety:

- **A folder on a drive that is not mounted is unknown, not missing** (the maintainer's USB
  stick): such entries are skipped and said so. Same when the index is empty or partial
  (an audit of only one folder must not make every other rule look stale): only judge a
  pattern against the roots the index covers.
- Writes with tomlkit like `places` (comments and order kept, atomic save), a dated copy
  `config.toml.bak-<date>` next to it first (inside `/config`, which only holds the config:
  check it fits the mounts rule, else `/cache`), then **read the file back and show what
  was removed** (product rule: a save is proven from disk).
- One-line undo: restore the copy.

## Questions for the maintainer (ask at run time)

- A page only, or also a verb (`mh config tidy`?) that lists with 🔒 and removes with a
  flag?
- `date_range` rules with no photo: proposed (unticked) or never?
- Run the check at the end of `sort` (it is `sort` that makes path rules and
  `places.folders` stale) and print one 💡 line "N entries of config.toml point at nothing:
  mh config tidy"?

## Acceptance

- [ ] Every kind of the table detected, with tests (folder renamed, moved by `sort`, drive
      not mounted, partial index)
- [ ] Nothing removed without being shown and ticked; backup copy; result read back
- [ ] Comments and order of `config.toml` kept (test on the default template)
- [ ] Menu catalog, both languages of the docs, `i18n_update`; `docs_screenshots` flagged stale
