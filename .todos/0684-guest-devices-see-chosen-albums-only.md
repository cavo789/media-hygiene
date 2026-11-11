# 0684 — Guest devices: a tablet or TV at relatives' sees the chosen albums only, never the whole library

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/lan_phones.py`, `src/media_hygiene/review/report_files.py`, `src/media_hygiene/share/album_link_door.py`, `src/media_hygiene/share/album_links.py`, `tests/unit/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).


## Decided (2026-11-11)

By the maintainer: the proposed roles. **Family** = the whole library and the
reports (as the phone today); **guest** = the chosen albums only, never the reports, 404
everywhere else.

## Context

The maintainer's case: showing photos at the in-laws', or to visitors at home. Today a
device is either **unpaired** (nothing, or one album by a link valid 24 h — 0462) or
**paired** — and then it reads everything `lan_paths.READ_PREFIXES` lists (read 2026-11-10):
the whole library by search, the previews, the videos, **the reports** (`/reports/…`: every
path of the PC, the duplicates, the quarantine's content, and the tool's own state files
such as `.mh-step.json`), the originals when the setting allows. There is no middle role:
pairing grandma's tablet gives it the family's whole archive, for 400 days.

## Proposal

- A **role** per paired device, chosen on the PC when the code is shown (*Family* /
  *Guest*), stored in `phones.json`: a guest's requests are answered as an album link's
  are — the albums the user ticked for guests (a list on the albums page), their pictures
  and films, the slideshow of those albums; nothing else, whatever the path (the allow-list
  is the album door's, not a filter over the family's).
- A guest pairing may last (a relative's tablet) or end with the visit (*until tonight*).
- For every role, the reports' hidden files (`.mh-*`) are never served; decide whether a
  *family* phone needs the reports at all (proposed: yes, they are read on the phone today).
- The 24 h link stays for a one-off.

## Acceptance

- [ ] A guest device gets 404 on every route but its albums' (a table-driven test over
      every route the servers know, both doors — reuse the phone read-only guard test)
- [ ] An album taken off the guests' list disappears at the next request
- [ ] Docs EN + FR: "showing photos to visitors"

## Where the user gains

Before: 2 levels (nothing / everything). After: a third one — the relatives see the 3
albums chosen for them, the rest of the library stays private.
