# 0041 — Albums: gather a selection into a folder of hard links, without moving anything

- **Priority**: Low — additive: nothing in 0026–0036 has to change for it
- **Batch**: albums
- **Depends**: 0028, 0035
- **Files**: `src/media_hygiene/cli/cmd_album.py` (new), `src/media_hygiene/services/album.py` (new), `src/media_hygiene/actions/album.py` (new), `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/undo.py`, `documentation/en/sort/`, `documentation/fr/sort/`

## Context

A folder tree gives each photo **one** place: `2016/Fêtes/Noël` or `2016/Grand-mère`, never
both. People still want "every Christmas since 2003", "my favourite photos", "everything with
grandma" in one folder, without breaking the tree `sort` built.

[sorta](https://github.com/shinKatana0/sorta) (compared on 2026-09-29) answers it with one
**canonical** layout, where files move, plus as many **albums** as wanted, gathered as
**hard links**: a second name for the same bytes, almost no disk space, made and dropped
freely.

## Proposal

**Feasibility first**, measured before any code:
- Does `os.link` work through a Docker Desktop bind mount of an NTFS folder (WSL 2 backend),
  and through a WSL path? Is the link a true NTFS hard link that Windows Explorer shows as a
  normal file?
- What does the user see: Explorer counts the size twice in folder properties; deleting the
  album copy leaves the original. The docs must say both.
- Close as unneeded if hard links do not survive the Docker path; copying would double the
  disk space of each album.

**If feasible**:
- `media-hygiene album <name> --category Noël`, `--rating 4` (the Windows stars of 0025),
  `--event <id>`, `--rule <name>` (0035): the selection comes from the latest classify plan
  and the index. It is written under `[album] root` (default `<target>/Albums/<name>`).
- Dry run by default, like `classify`: prints the selection, `--apply` makes the links.
- Journaled (`Phase.ALBUM` / `ActionKind.LINK`, next to 0024's kinds); `undo` removes the links,
  never the originals.
- The album folder is excluded from the scan of `audit` and `classify` automatically:
  otherwise every linked photo would look like an exact duplicate of its original, and
  `clean` would offer to delete one of them.

## Acceptance

- [ ] Feasibility measured on Docker Desktop (Windows) and WSL; result noted here.
- [ ] If built: an album of a category and one by rating; `undo` removes the links, the
      originals stay byte-identical; `audit` does not see the album as duplicates.
- [ ] Sort guide en + fr; `.po` translated.

## Status — PARTIAL (2026-10-02)

### Done
- Feasibility measured where this run could: `os.link` on the WSL ext4 workspace and inside an
  alpine container (overlay) gives one inode, `st_nlink` 2.
- `media-hygiene album NAME` (`cli/cmd_album.py`, `services/album*.py`, `actions/album*.py`,
  `classify/album_rows.py`, `console/album_view.py`): `--category` (as `sort` decides it, edits
  of the workbook and the review page included), `--event` (id or name), `--rule`, `--rating N`
  (Windows stars from the index), `--workbook`; dry run by default, `--apply` makes the links.
  Files found where the plan saw them or where a `sort` of the plan moved them (sort journals).
- `[album] root` (default `Albums` in `[classify] target`); refused when not mounted, read-only,
  protected, or not a valid folder name. Files on another mount (EXDEV: two `-v` mounts are two
  mounts even on one drive) predicted from the mount table and set aside; a disk refusing links
  stops the run at the first refusal, with the reason.
- Journaled as `Phase.ALBUM` (`ActionKind.LINK`, `ActionKind.MARK_ALBUM`, `CREATE_FOLDER`);
  `undo` removes a link only while the file keeps another name (`st_nlink >= 2`), then the
  marker and the folders created; links count no bytes in `undo` nor `history` (column Linked).
- Album folders hold `.media-hygiene-album`; the walker skips any folder holding it: `audit`,
  `classify` and `clean` never see album links as duplicates (tested: 0 groups).
- Tests: an album of a category and one by rating, `undo` leaves the originals byte-identical,
  the audit sees no duplicate, an album after a sort and the undo of that sort, the last name of
  a file kept by `undo`, refusals. Docs en + fr (`sort/11-albums.md`, commands, safety, mount
  points), `.po` translated.

### Not done
- Feasibility on Docker Desktop (Windows, NTFS bind mount, WSL 2 backend) and through a WSL
  `/mnt/c` path: does `link()` succeed, is the result a true NTFS hard link Explorer shows as a
  normal file, and do both names report the same `st_ino` (needed by the scan's alias check)?
  **Reason:** this run may not mount anything under `/mnt/c` nor a Windows folder; to measure
  by the maintainer on a synthetic folder, e.g. `C:\Temp\links`: create a photo, run `audit` then
  `classify --target C:\Temp\links` and `album Test --category … --apply` with
  `-v "C:\Temp\links:/data/c/Temp/links"`, then check in PowerShell
  `fsutil hardlink list C:\Temp\links\Albums\Test\<photo>`. If links fail there, the command
  already refuses cleanly; the TODO said to close as unneeded in that case (maintainer's call:
  keep the command for Linux/NAS users, or remove it).
- `docs_screenshots` (en, fr) and `e2e` were not run.
  **Reason:** `docker run` drops attached output written after ~1 s in this environment
  (`sleep 3; echo late-output` prints nothing). The help capture blocks touched (`help.txt`,
  `help-undo.txt`, new `help-album.txt`) were filled from the sources with the docs' own
  `tidy()` (it reproduces `help-sort.txt` byte for byte); `config.txt` still lacks
  `album.root` until `docs_screenshots` runs. The album page's console examples are
  hand-written.
