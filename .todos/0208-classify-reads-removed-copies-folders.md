# 0208 — `classify` reads the folders of the copies `clean` removed, after the file's own

- **Priority**: Low
- **Batch**: former-names
- **Depends**: 0207
- **Files**: `src/media_hygiene/services/classify_inputs.py`, `src/media_hygiene/classify/models.py`, `src/media_hygiene/classify/folders.py`, `src/media_hygiene/classify/event_folders.py`, `src/media_hygiene/classify/folder_towns.py`, `src/media_hygiene/classify/signals.py`, `src/media_hygiene/report/classify_writer.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_classify_former_folders.py` (new), `documentation/en/sort/04-classify.md`, `documentation/fr/sort/04-classify.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F4, the `classify` part). 0207 keeps, in the
index, the folders and names of the copies `clean` removed, attached to the kept file. `classify`
gets most of its meaning from folder names (an existing folder someone named, a town in a folder
name: 0119, `folder_town`). A photo kept in a generic folder (`DCIM`, `Camera`) whose removed copy
lived in `Mariage Julie 2015` loses that hint today.

## What to do

- `services/classify_inputs.py` reads the former folders of each file (0207's table) into its
  `MediaInput`. `classify/models.py` is at 194/200: move a model out to a new module first if the
  new field does not fit.
- They count as hints after the file's own folders, never before: a file whose own folders already
  give an event, a place or a town keeps them; otherwise the former folders feed the same signals
  (`event_folders`, `folder_towns`, the place from a folder name of 0119), as if the file lay
  there.
- Former folders that disagree (two different events or towns): none is used — a guess never
  passes for a certainty — and the file goes to "to check".
- The workbook's "why" says where the hint came from: "(the folder of a removed copy: …)".

## Explicit non-goals

- Moving the file back to a former folder: `classify` only proposes, as always.
- The former file names (0207 makes them search words; `classify` reads folder names only).

## Acceptance

- Unit (`test_classify_former_folders.py`): a file in `DCIM` with one former folder naming an
  event gets that event, marked as such; its own folder wins when it names one; two disagreeing
  former folders give "to check"; a file without former folders is unchanged.
- Docs both languages: sorting step 4, one paragraph.

## Gain (estimated)

Photos left in generic folders after a clean get the event or the place their removed copies'
folders named, instead of a bare date.
