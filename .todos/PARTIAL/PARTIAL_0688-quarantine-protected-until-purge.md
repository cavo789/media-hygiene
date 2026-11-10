# 0688 — The quarantine is covered by the NAS copy, or `purge` says what has no other copy

- **Priority**: High
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/push_sources.py`, `src/media_hygiene/services/push_listing.py`, `src/media_hygiene/services/push_lines.py`, `src/media_hygiene/services/quarantine_ledger.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/services/disk_purge.py`, `documentation/en/commands/push.md`, `documentation/fr/commands/push.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Decided (2026-11-10, maintainer)

- **Option B: count, do not copy.** `push`, the quarantine page, the disk-space page and
  `purge` say how many files set aside have no other copy; `purge` shows those first and asks
  for them apart. Nothing of the quarantine is copied to the NAS (option A is not done).

## Context

The maintainer asks whether the quarantine is saved on the NAS. Read in `commands/push.md`
(2026-11-10; to confirm in `services/push_*.py`): `mh push` lists the photo folders "but
the system folders, the excluded ones **and the quarantine**". A file already pushed keeps
its NAS copy while it waits in the quarantine (it leaves the NAS only once purged). But:

- a file **never pushed before it was set aside** (imported, then cleaned the same day)
  exists in the quarantine only — one copy, on one disk, for as long as the user waits
  before purging (`purge_hint_days`);
- the quarantine does not hold only exact copies: **near duplicates** (`--tier near`),
  burst shots set aside, files judged junk or unreadable, intruders — photos with no twin
  anywhere. A disk failure during that wait loses them, and `undo` has nothing to bring back;
- at `purge`, nothing tells the user which of the files erased have no other copy at all.

## Options (to decide)

- **A. Push covers the quarantine**: `<target>\.quarantine\<run>\…`, the same mirror,
  removed from the NAS when the run is purged (through `.removed`, 90 days). Costs the
  quarantine's size on the NAS (the disk-space page knows it).
- **B. Count, do not copy**: `push` and the quarantine page say *N files set aside have no
  other copy (X GB): exact copies excluded*; `purge` shows those N first (*seeing first*)
  and asks for them apart.
- A + B is the safest; B alone costs nothing.

## Proposal

- B in any case: a file of the quarantine is *covered* when its content exists elsewhere —
  the kept copy of an exact duplicate (journal: `keeper`), or a NAS copy (push's listing).
  Everything else is *the only copy*; the figure is on the quarantine page, the disk-space
  page and in `purge`'s question.
- A if the maintainer accepts the space.

## Acceptance

- [ ] The count of only-copy files shown before a purge, proven on the demo tree (a near
      duplicate set aside = 1 only copy; an exact copy = 0)
- [ ] With A: a push after a clean copies the run's quarantine; after a purge it leaves
      through `.removed`; `undo` then push puts things back (test with the demo's copies —
      identical files paired by name)
- [ ] Docs EN + FR (`push.md`, `purge.md`, `reference-safety.md`)

## Where the user gains

Before: near duplicates and junk set aside wait with 1 copy, and `purge` erases them without
saying so. After: the user sees "37 files here exist nowhere else" before erasing — or they
are on the NAS too.

## Status — PARTIAL (2026-11-10)

### Done

- `services/only_copies.py`: a file of the quarantine is covered only when set aside as an
  exact copy (`quarantine-duplicate`, byte-compared with its `keeper` first) and that keeper is
  still on the disk with the same size. Deviation from the TODO: a near duplicate's journal
  entry names a `keeper` too (of other content, `clean_aside.py`): it is not a cover. A run
  whose journal is lost counts every file of its folder (safe side).
- `purge` (`cli/purge_only.py`): after the yes, lists the only copies (count, size, first 20
  paths) and asks for them apart; a no changes nothing.
- Tests on the demo tree (`tests/integration/test_only_copies.py`): exact copies covered,
  near duplicates counted, a keeper deleted uncovers its copy, a run without journal, purge's
  second question.
- Docs EN + FR: `purge.md`, `push.md`, `reference-safety.md`.

### Not done

- The figure on the quarantine page, the disk-space page and in `mh push`'s lines.
  **Reason:** page work (template, the `apply_now`/bar contract) left for a lot of its own.
- A NAS copy counted as cover.
  **Reason:** the container keeps no listing of the push target after a push (`push_listing`
  is built during the run only); counting it needs push to save its listing.
- The only copies are asked after the general purge question, not shown before it.
