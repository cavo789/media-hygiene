# 0009 — Evaluate Immich as the long-term family photo library

- **Priority**: Low
- **Batch**: decision
- **Depends**: —
- **Files**: TBD

## Context

Immich was part of the initial idea. It is a server (Postgres, ML, Redis) managing its *own*
library, reviewed in a web UI — a destination for the cleaned photos rather than a step of this
CLI. Decide whether the family library should move there once the disks are clean.

## Acceptance

- [ ] Decision recorded (adopt / not now), with the migration path if adopted.

## Evaluation (2026-10-03)

Desk research from primary sources only (Immich repository, its documentation sources under
`docs/docs/`, releases, issues and discussions), read on 2026-10-03. Immich was not installed.

### Immich today

- **Maturity**: first stable release `v2.0.0` on 2025-10-01
  ([release](https://github.com/immich-app/immich/releases/tag/v2.0.0)); `v3.0.0` on 2026-07-02
  with breaking API changes and release candidates
  ([release](https://github.com/immich-app/immich/releases/tag/v3.0.0)); latest stable `v3.2.4`
  on 2026-09-28, `v3.3.0-rc.2` on 2026-10-02. AGPL-3.0, ~115k stars, pushed daily.
- **Footprint** ([requirements](https://github.com/immich-app/immich/blob/main/docs/docs/install/requirements.md)):
  server, machine learning, Postgres, Redis containers; 6 GB RAM minimum (8 recommended), 2 cores
  minimum (4 recommended); Linux strongly recommended, Docker Desktop / WSL 2 "strongly
  discouraged" but possible; Postgres must not live on NTFS nor a `/mnt` WSL bind mount (use a
  named volume); thumbnails and transcodes add 10–20 % to the library size.
- **Backups**: Immich asks for a 3-2-1 plan (README); its own nightly dumps hold the database only
  ([backup and restore](https://github.com/immich-app/immich/blob/main/docs/docs/administration/backup-and-restore.md)).

### External libraries: the only way to keep our tree

[External libraries](https://github.com/immich-app/immich/blob/main/docs/docs/features/libraries.md)
index folders Immich does not own; uploads (mobile app, `immich` CLI, immich-go) copy files into
Immich's own storage instead. What matters for media-hygiene:

- **Assets are keyed by path.** A file moved inside the library is a new asset on rescan: its
  albums, description and other Immich-only metadata are lost (documented caution, "will be fixed
  in a future release"). A file gone from disk goes to the Immich trash, purged after 30 days.
- **Mount read-only** (`:ro`) to keep media-hygiene the only writer: Immich then cannot delete
  anything, but cannot write XMP sidecars either, and edits to rating/description/tags
  **silently fail** ([XMP sidecars](https://github.com/immich-app/immich/blob/main/docs/docs/features/xmp-sidecars.md),
  issue [#10538](https://github.com/immich-app/immich/issues/10538)).
- **Exclusion patterns** (picomatch globs, case-insensitive) and a nightly rescan; the file
  watcher is experimental and does not work on network drives.
- **Folder view** (opt-in, per user) browses the tree as folders: a sorted tree stays visible.
- **No albums from folders**: the request ([discussion #8596](https://github.com/immich-app/immich/discussions/8596),
  2024) is answered by third-party tools, e.g.
  [immich-folder-album-creator](https://github.com/Salvoxia/immich-folder-album-creator) (API).
- **Hard links count as duplicates**: two paths are two assets, flagged by the duplicate utility
  ([discussion #28404](https://github.com/immich-app/immich/discussions/28404), 2026-05-13,
  v2.7.5). No deduplication between external and uploaded assets
  ([#23898](https://github.com/immich-app/immich/issues/23898), closed 2025-11-14).
- An external library belongs to one user; sharing goes through albums / partner sharing.

### How media-hygiene's outputs map onto it

| media-hygiene output | In Immich | Note |
|---|---|---|
| Cleaned disks (`clean`) | Fewer assets to index | Immich's own duplicate check is ML only, review by hand |
| Sorted tree (`classify` / `sort`) | Import paths + folder view | Sort **before** the first scan: a later `sort` resets Immich metadata of moved files |
| Albums as hard links (`album`) | Duplicate assets | Exclude the album root (`**/Albums/**`); rebuild albums in Immich through its API if wanted |
| Burst choices (`review`, `decisions.json`) | Stacks (manual) | Ours quarantine the set-aside shots, so only the chosen ones reach Immich |
| Near duplicates, re-encoded videos (`--tier near`) | Duplicates utility | Overlap; ours is offline, reversible and file-level |
| Places (`places`, `[[classify.places]]`) | Map + city-level reverse geocoding (GeoNames) | Named personal places only exist as our folder names; Immich has no named-place concept that we found |
| Subjects (`classify` + Ollama) | Faces, CLIP smart search, OCR | Immich is much stronger to *find*; ours *files* |
| XMP sidecars kept with their photo | Read; written back only with write access | |
| Journal / `undo` | Trash (30 days) | |

**Overlap**: viewing, map, near-duplicate review. **Immich only**: faces, smart search, mobile
backup, sharing, multi-user. **media-hygiene only**: byte-exact cleaning across disks, journaled
moves with undo, a user-chosen tree on disk that outlives any application.

### Options

1. **Not now** — finish cleaning and sorting the disks; revisit when no more `sort` is planned.
   Nothing to run, nothing to back up beyond the files.
2. **Immich as a read-only viewer** (external library `:ro` over the sorted tree, album root
   excluded, ML on). Files stay the source of truth, media-hygiene stays the only writer; Immich
   is disposable (deleting it loses only Immich-made albums, faces names, favourites).
   Migration path: (a) last `audit` + `clean` + `sort`; (b) install Immich on a Linux host or a
   machine able to run ML indexing for hours (Postgres on a named volume if WSL); (c) mount the
   tree `:ro`, one external library per family member owner, exclusion `**/Albums/**`; (d) scan,
   let faces/CLIP finish; (e) optionally rebuild albums from the album folders with the API;
   (f) back up the Immich database dumps if its own albums/faces are to survive.
3. **Immich as the master library** (upload into its storage template, mobile auto-backup).
   Immich owns files and layout; media-hygiene becomes a pre-import cleaner only. Gives up the
   user-guided tree that `classify`/`sort` exist for.

**Recommendation**: option 1 now, with option 2 as the target once the disks are clean, after a
short trial on a subset. Option 3 contradicts the user-guided sort. In any case media-hygiene
should not grow what Immich already does well (faces, smart search, sharing, mobile backup).

## Status — PARTIAL (2026-10-03)

### Done
- Evaluation from primary sources (above): maturity, footprint, external-library behaviour,
  mapping of media-hygiene outputs, overlaps, three options with a migration path, recommendation.

### Not done
- The decision itself (adopt / not now).
  **Reason:** it belongs to the maintainer; it depends on the host available (Linux box, NAS,
  or the Windows PC) and on whether family members want the mobile app and sharing.
- A hands-on trial (synthetic pictures, `docker compose up`, external library `:ro`, check that
  hard links show as duplicates and that a moved file loses its album).
  **Reason:** not required by the TODO; worth doing before adopting option 2.
