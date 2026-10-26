# 0382 — sort: rewrite every file that names photos by path, right after moving them

- **Priority**: High
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/services/sort.py`, `src/media_hygiene/services/sort_report.py`, `src/media_hygiene/people/person_files.py`, `src/media_hygiene/people/followed.py`, `src/media_hygiene/share/albums.py`, `src/media_hygiene/share/album_follow.py`, `src/media_hygiene/report/decisions.py`, `src/media_hygiene/shrink/try_choices.py`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`

## Why

Asked by the maintainer on 2026-10-25, before the first real reorganisation with `sort`:
"after a `sort`, everything must stay linked, with no loss, without the user having to
think about it". Today the index follows each move (`PATH_TABLES`, `index.moves`), but
several files **outside** the index still name photos by their old path. They are only
saved because readers follow `index.moves` when they read. If the cache volume is lost
before the next save (deleted, Docker Desktop reinstalled, `docker volume prune`), those
links are lost. For people's names, that is hand work.

`sort` must rewrite them itself at the end of its run, and `undo` of a sort must do the
same in reverse. It reads each file back from the disk and says so in one line, per the
product rule.

## Inventory (read in the code on 2026-10-25)

| File | Keyed by | Today after `sort` | To do |
|---|---|---|---|
| `/config/people/<name>.toml` (+ `ignored_file`) | `<path>#<n>` | Followed at read (`follow_ids`), rewritten at the next save in the `people` page | `sort` rewrites them (`save_people(follow_ids(...))`, the code tested in `test_people_files.py:143`). Comments of `config.toml` kept (tomlkit, atomic) |
| `/reports/albums.json` | host path + SHA-256 + size | Found again at read (`album_follow`: moves, then digest) | Rewrite the entries with the new paths (no content read: the moves are known) |
| `/reports/decisions.json` (`bursts`, `chosen`, `unwanted`, `gone`; `pairs` are folder pairs) | host paths (folders for `pairs`) | **Not followed**: no reader of `index.moves` there (checked by grep) | Rewrite (point 3) |
| `shrink-decisions.json` (drafts folder) | path + size + mtime | Skipped when moved (safe, but the choices are lost) | Rewrite the paths (size and mtime kept by the move) |
| `sort-decisions.json`, `plan.json` | plan rows | Read by `sort` itself | Nothing (used up by the run) |
| `phone-decisions.json` | phone paths | Not on the PC's disks | Nothing |
| `.xmp` sidecars | next to the photo | Moved with the photo by `sort` | Nothing; a test proves it |
| `config.toml`: `protected`, `preferred`, `excluded`, `[[places.folders]]` | **folders** | Unchanged | Not rewritten (a folder is not a photo). `sort` lists the ones whose folder is now empty or gone, one line each, with what to do |
| Reports (`summary.json`, HTML, `plan.csv`) | paths | Stale | Nothing: the next `audit` writes them again. `sort` already says to run it? To check |

To check while implementing: grep for any other store keyed by a photo path (`/reports`,
`/config`, drafts folders) added since, e.g. the slideshow and the home page.

## 3. An unapplied `decisions.json` — decided: rewrite (maintainer, 2026-10-25)

The burst and junk decisions name files; the pairs name folders that `sort` may have
emptied. Options:

`sort` rewrites the file paths (`bursts`, `chosen`, `unwanted`, `gone`; `size`/`mtime_ns`
kept), and drops the `pairs` whose folders are gone, saying how many: no review work lost.
`roots` are updated when `sort` moved files out of them. Rejected: refusing to sort until
`clean --decisions` (blocks the user), warning only (the decisions would be lost).

## Tests (`.claude/rules/workflow.md`: one per event)

- `sort` then each file above names the new paths, read back from the disk.
- `sort`, `undo`: the old paths are back.
- The cache volume deleted after a `sort`: the names, albums and decisions still find their
  photos (the whole point).
- Two identical copies moved together: each entry follows its own file (tie broken by name).
- A file of the list missing or unreadable: `sort` still completes, and says which file
  was not updated.

## Gain

**Estimated:** today, people's names and albums depend on the cache between a `sort` and
the next save, and burst decisions are lost. After this change, 0 links depend on the cache.
