# 0386 — Photos from a person's folder join the user's folder of the same moment, else the trip's

- **Priority**: High
- **Batch**: classify
- **Depends**: 0385
- **Files**: `src/media_hygiene/classify/signals.py`, `src/media_hygiene/classify/events.py`, `src/media_hygiene/classify/engine.py`, `src/media_hygiene/classify/models.py`, `src/media_hygiene/classify/names.py`, `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/04-classify.md`, `documentation/fr/sort/04-classify.md`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Same case as 0385 (maintainer, 2026-10-25): the maintainer sorted a trip into
`2019/Montenegro/Budva`, `…/Cetinje`, `…/Parc national du Lovcen`; the daughters' photos of the
same days sit in `2019/Photos Chloé` and `Manon 2023/dcim`. Expected: "since I did the work,
my daughters' photos should go into my folders when the date matches".

Today (read in `signals.py`): `with_neighbours` lets the loose files of an event join its folder
**only when the event has exactly one** user-named folder; this event has five, so nothing joins.
`Photos Chloé` is not even seen as a person's folder: `_own_signal` returns `PERSON_FOLDER`
only for `<person>/<generic>` at the root (`Manon 2023/dcim`), so `2019/Photos Chloé` is an
`existing-folder`, as strong as `Budva`. And `Manon 2023/dcim` proposes `2019/Manon 2023`
(a 2023 name for 2019 photos).

## What (decided by the maintainer, 2026-10-25: "join, else the trip")

- Cut each event into its **sessions** (`session_gap_hours`, 6 h by default). Today
  `find_events` merges with `max(session_gap, merge_gap)` and never keeps the sessions
  (`events.py`, comment line 70): keep them on `Event`.
- A file from a person's folder (or loose) taken during a session where the user's named folders
  hold files goes to that folder; several such folders in the session → the one whose photo is
  nearest in time. Band **to check**, reason "Same moment as <folder>" (new `SortReason`, its
  `names.py` label, a `match` for the rule list in `config.toml` so the user can move or turn
  it off like `event_neighbour`).
- No session matches → the **trip's folder**: the deepest common parent of the user's named
  folders of the event (`2019/Montenegro` here), if it is meaningful (not a year, not generic);
  otherwise today's proposal.
- Never moves a file of a user-named folder (0385).

## How a person's folder is recognised (decided by the maintainer, 2026-10-25)

Folder names are free-form ("Photos Chloé", "Photos de Chloé", "Backup Manon", "iPhone Manon"):
a folder is a person's when **the name of a person is found in it**, as a word, case and accents
ignored. The names come from the people page (`/config/people/`), plus a
`[classify] person_folders = ["Chloé", "Manon"]` list in `config.toml` for people not named there.

## Tests

The trip case as a synthetic plan: three named folders over three days, a person's folder with
photos inside each session and one outside all → each joins its session's folder, the last one
the trip's folder; one named folder only → same as `event_neighbour` today; the rule turned off
(`score = 0`) → today's proposals. Run `classify` on the demo tree before/after: the counts of
the bands, measured, in the commit message.
