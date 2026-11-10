# 0691 — Settings, people, events and albums files keep their previous versions: a page's save can be undone

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/review/config_saving.py`, `src/media_hygiene/text_files.py`, `src/media_hygiene/share/album_store.py`, `src/media_hygiene/services/page_undo.py`, `src/media_hygiene/review/templates/undo_toast.html.j2`, `tests/unit/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Decided (2026-11-10, maintainer)

- The previous versions live in **`/config/.history/`** (saved by `mh backup` with the rest of
  `/config`). The mounts rule ("`/config`: config.toml only, plus `people/` and `events/`")
  gets this documented exception, in `CLAUDE.md` and `reference-mount-points.md` (EN + FR).

## Context

Undo covers the **files** (journal). The pages also write the user's own work as small
files, saved atomically and read back — but **over the previous version**: `config.toml`
(places, rules, roles, settings), `/config/people/<name>.toml` (faces named one by one),
`/config/events/<year>.toml`, the albums' list, hand-typed tags and landmarks in the index.
No earlier version is kept (`grep` for `.bak` / versions in `review/config_saving.py` and
`config/`, 2026-11-10: nothing). A wrong click — *Remove all rules*, a person merged into
another, an album emptied — is final unless a `mh backup` is recent.

## Proposal

- One helper for every such save (where the atomic write already lives): before replacing,
  the current file is copied to `<folder>/.history/<name>.<timestamp>` — the last 20
  versions or 30 days, trimmed at save time (constants). `/config` may hold them: they are
  configuration (check against the mounts rule: "never store other data under `/config`" —
  propose `/config/.history/`, or the backups folder if the maintainer prefers; **ask**).
- The Undo toast after a save restores the previous version (read back, shown), on every
  page that saves settings; Ctrl+Z where the page has no other meaning for it.
- A *Versions* link on the settings index: date, what changed (a short diff of keys),
  *Restore this one*.
- Index-only data (tags typed by hand, landmarks): covered by `mh backup`; the tag pages
  already offer their own undo (0622, 0650) — list what is left.

## Acceptance

- [ ] Every save path of the pages goes through the helper (a test lists the writers of
      `/config` and of the albums' file)
- [ ] Save → Undo → the file is byte-identical to before (test per file kind)
- [ ] The history never grows past its bound; restored and moved folders handled (tested)
- [ ] Docs EN + FR

## Questions for the maintainer

- Where the versions live: `/config/.history/` (proposed) or elsewhere?

## Where the user gains

Before: the photos' moves can be undone, the user's hours of naming and rules cannot.
After: the last 20 saves of each file can be brought back from the page.
