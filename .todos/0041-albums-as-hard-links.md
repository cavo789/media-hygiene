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
