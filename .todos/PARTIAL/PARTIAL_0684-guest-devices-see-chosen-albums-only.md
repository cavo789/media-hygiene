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

- [x] A guest device gets 404 on every route but its albums' (a table-driven test over
      every route the servers know, both doors — reuse the phone read-only guard test)
- [x] An album taken off the guests' list disappears at the next request
- [x] Docs EN + FR: "showing photos to visitors"

## Where the user gains

Before: 2 levels (nothing / everything). After: a third one — the relatives see the 3
albums chosen for them, the rest of the library stays private.

## Status — PARTIAL (2026-11-11)

### Done
- Two codes on the PC's card, **👪 Family** / **🧳 Guest** (`review/lan_guest.py`): the role is the
  code typed, derived from the run's secret with its own label, renewed by *Open pairing again*.
  A guest gets its own run token, or under HTTPS a token for good kept in `phones.json` with
  `role = "guest"` (old files load as `family`); the card's device list says *Guest*.
- A guest's requests go to `share/album_guest_door.py` alone (an allow-list of its own): `/` →
  `/albums` (guest mode of the albums page: no header, no step chip, no way to the rest),
  `/api/album-list` (ticked albums only), `/api/album/<ticked>`, `/thumb|tv|film/<key of a ticked
  album>`, `/assets/`; everything else, every `POST`: 404, never passed on (the reports, `.mh-*`
  files included). `/api/stop` keeps its earlier 403 (the server's own loopback guard, before any
  door).
- The slideshow's door never takes a guest's cookie for a phone, and refuses the guests' code.
- **🧳 Show to guests** tick on an album's page (PC), saved in `albums.json` (schema 4, `guests`),
  read back; follows a rename. The list is read on each request: unticked → gone at the next one.
- `tests/unit/test_lan_guests.py`: 192 cases, every known route with both methods; docs EN + FR
  (`commands/home.md`, *Showing photos to visitors*).

### Not done
- A try on a real tablet at the maintainer's (the guests' QR code, the guest page).
  **Reason:** needs the maintainer's devices.
- *Until tonight* (a guest pairing ending with the visit): guests last like a family phone and are
  forgotten on the PC's card. **Reason:** kept out of this lot; a follow-up if wanted.
- The slideshow of the guests' albums on the TV from a guest device. **Reason:** the TV's remote
  is the family's (slideshow door); a guest looks on its own screen.
- The reports' hidden files (`.mh-*`) are still served to a family phone. **Reason:** decided
  family = as the phone today; that filter is left for a follow-up.
