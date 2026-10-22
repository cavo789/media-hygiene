# 0300 — The faces of each person in their own file, `/config/people/<name>.toml`, linked from `config.toml`

- **Priority**: Medium — `config.toml` stays readable at any collection size; one click rewrites one person, not the whole file
- **Batch**: people-page
- **Depends**: 0299
- **Files**: `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/layers.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/followed.py`, `src/media_hygiene/cli/people_forget.py`, `src/media_hygiene/paths/locations.py`, `src/media_hygiene/config/templates/config.toml.j2`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `CLAUDE.md`, `tests/unit/test_people_config_file.py`, `tests/integration/people/test_people_names.py`

## Why

`[[people.person]]` keeps every confirmed and rejected face id (`<photo path>#<n>`, about
60 bytes) inside `config.toml`, the file the user edits by hand. Measured 2026-10-22 in the
devcontainer (`save_people` + `read_people` on a generated file, 40 people, `nice -n 19`):

| Confirmed faces | Size | Lines | `read_people` | One naming (save + read back) |
|---|---|---|---|---|
| 2 000 | 0.12 MB | 2 200 | 5 ms | 0.05 s |
| 10 000 | 0.61 MB | 10 200 | 21 ms | 0.26 s |
| 40 000 | 2.44 MB | 40 200 | 82 ms | 1.98 s |

The maintainer has 50 000+ photos and wants **no limit** on the references (a cap per
person was proposed and rejected, 2026-10-22). Their design, approved:

```toml
# config.toml
[[people.person]]
name = "Frédérique"
file = "people/Frédérique.toml"   # faces = [...], rejected = [...]
```

`config.toml` still lists every person; the long lists live next to it.

## Decisions (maintainer, 2026-10-22)

- Folder: `/config/people/` — a stated exception to "/config holds config.toml only":
  these files are configuration the user wrote, never disposable data. Update the
  `Locations` docstring and `CLAUDE.md` (mount points).
- Migration: the old format (faces inline) is still read; the first save from the page
  moves the lists into `people/` and leaves only `file` in `config.toml`.
- The ignored faces (`[people] ignored`) go the same way: `people/ignored.toml`.

## Points to handle

- File name from the person's name: accents kept; Windows-forbidden characters
  (`<>:"/\|?*`, trailing dot/space, reserved names `CON`…) replaced; two names equal but
  for case (Windows file system) must not share or overwrite a file — refuse or suffix.
- Renaming a person renames the file; `people --forget` deletes the folder's files too
  (it asks already for the names).
- Write order: the person's file first (atomic, validated), then `config.toml`; a crash in
  between leaves an orphan file, never a lost face. An orphan or a missing linked file is
  said in one line, never a traceback.
- `follow_ids` (`people/followed.py`, photos moved by `sort`/`undo`) rewrites the person's
  file, not `config.toml`.
- Everything reading `PeopleSettings` (`naming.Known`, `search/people_words.py`,
  `classify/rules/people.py`, `services/classify_people.py`, `tags/`) gets the lists loaded
  from the files: resolve them where the settings are read, not in each consumer.
- `config.toml` written by hand without `file`: still valid (faces inline).

## Done when

- Tests: the link round trip; migration on first save; forbidden characters and case
  collisions; missing / orphan file; a sort move followed into the person's file.
- Measure again the table above with the files split: one naming at 40 000 faces over 40
  people should rewrite ~1 000 ids (**estimated** ~0.05 s from the 2 000 row).
- Both languages of `reference-people.md` updated.
