# 0376 — `mh pull`: put the photo folders back as the last `mh push` left them, after a crash

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0375
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_pull.ps1.j2`, `src/media_hygiene/cli/cmd_pull.py`, `src/media_hygiene/services/launcher_pull.py`, `src/media_hygiene/services/pull_plan.py`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/support/docs/scenario.py`, `tests/measure/mh-measure.ps1`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/pull.md`, `documentation/fr/commands/pull.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`
- **Needs maintainer**: a crash rehearsal on Windows (a test folder pushed, emptied, pulled back), step of `mh-measure.ps1`

## Why

The maintainer, 2026-10-25: "`mh import` would not take me back to the situation before a
crash". Right: `import` (0245) reads only the *compared backups* (`folders add --backup`), never
the target of `mh push`; it copies what they alone hold into `From NAS`, not to the files' own
places, and leaves out what the user set aside. It tops up a library, it does not restore one.

`mh push` (0375, formerly `mh backup`, 0264) keeps every photo folder under its own path in the
target (`C:\Photos\2019\Été\a.jpg` in `\\NAS\backup_photos\C\Photos\2019\Été\a.jpg`,
`backup_place.py`), the previous copy of an edited file and the files gone from the PC in
`.removed\<run>` (erased after `[backup] keep_removed_days`, 90 days). So the target holds what is
needed to rebuild each folder at its place: `pull` is the restore of `push`.

## What to do

1. **`mh pull [--from <folder>] [--folder <photo folder>]… [--anyway]`**, a host command of
   `mh.ps1` like `push` (Windows copies with `robocopy`, the container plans: same reasons, about
   7 times faster than through Docker, step 21 of `mh-measure.ps1`, *measured* 2026-10-20 for
   writing; reading back from the NAS *to measure*).
   - `--from` by default: `push-target.txt`. After a crash of `C:` that file is gone with
     `$HOME\media-hygiene`: then `--from` is required and the error line says so.
   - Which folders: each folder of the target (`C\Photos` → `C:\Photos`), `mh` folders known or
     not (after a crash `mh.ps1` may be new: the list comes from the target); `--folder` limits
     to some. A drive letter that does not exist now (a disk replaced by another letter): refused,
     with the line to type (`--folder` and a mapping, *to design*).
2. **What is copied**: each file of the target missing at its place on the PC. Never `.removed`
   (the files deleted on purpose stay deleted: say how many, and where they are, in one 💡 line).
   A file present on the PC with another size or date: left alone, listed (the PC's copy is
   newer than the last push or the file was edited: never overwritten); `--anyway` is not for
   that, it is `push`'s meaning (to check the flag name, maybe none needed).
   - `robocopy` without `/MIR` nor `/PURGE`, and **without** overwriting (`/XC /XN /XO`: to check
     the flags on Windows): nothing on the PC is deleted or replaced; nothing on the NAS is
     written.
   - The dates kept (`robocopy /COPY:DAT`, default *to check*): the index is keyed by
     (path, size, mtime), so a file back at its path with its size and date is the same row; the
     audit after a pull is incremental, and the `tags`, `descriptions`, `faces` rows restored by
     `mh restore` (0352) apply again. Test it.
3. **Proven, journaled, undoable**: a plan shown and asked once; a journal (`Phase.PULL`) of the
   files copied; each copy checked (size, then SHA-256 against the target's file, like
   `import`'s `CopyInExecutor`); `mh pull --undo <run>` (or `undo <run>`, whichever `push`
   uses) removes the copies not modified since. The result read back from the disk: files
   copied, size, files left alone.
4. **Moves** (`.claude/rules/workflow.md`): a photo moved on the PC after the last push (by
   `sort`, `clean`, the user): it is at its new place on the PC, at the old one in the target; a
   pull would put a second copy back at the old place. Plan it from the index: a file whose
   content (SHA-256 known to the index) is already in the folders is not copied back, said
   apart. Test with the demo tree's copies (same content, several names).
5. The crash guide: a page section "After a crash" (en + fr) in `commands/pull.md`, linked from
   `push.md` and from 0352's page: install Docker, `mh launcher`, `mh restore --from …` (0352),
   `mh pull --from \\NAS\backup_photos`, then `mh audit` (incremental).
6. CLI as every verb: `--help`, `reference-commands.md`, `COMMANDS_TOO`, `menu_catalog_*`, mkdocs
   `nav`, `i18n_update` + French; the bash `mh` refuses it like `push`.
7. `mh-measure.ps1`: a step that pushes a small test folder, empties it, pulls it back, compares
   the hashes and times the read from the NAS.

## Acceptance

- Push a folder, delete it from the PC, `mh pull`: every file back at its path, same SHA-256,
  same modified date; the next `mh audit` hashes nothing again.
- A file deleted on purpose before the push (in `.removed`) is not back; a file edited on the PC
  since is not overwritten; a file moved by `sort` since is not copied a second time.
- Nothing written on the NAS during a pull (its target listed before and after: identical).

## Gain

Today a dead disk means rebuilding the photo folders by hand from `\\NAS\backup_photos\C\…`
(robocopy typed by the user, no check, the files moved since doubled). With `pull`: one command,
each copy proven, the index valid again, no `mh tags` to run again (with 0352). Duration: the
read from the NAS (*to measure*, step of point 7).
