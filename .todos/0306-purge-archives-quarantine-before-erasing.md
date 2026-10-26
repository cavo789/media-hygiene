# 0306 — `mh purge --to <folder>`: copy the quarantine elsewhere (NAS, disk, cloud), check the copy, then empty it

- **Priority**: Medium — asked by the maintainer on 2026-10-22 while cleaning: "empty the quarantine without erasing it, copy it to my NAS just in case"
- **Batch**: actions
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_purge.py`, `src/media_hygiene/cli/purge_archive.py` (new), `src/media_hygiene/actions/purge.py`, `src/media_hygiene/actions/purged.py`, `src/media_hygiene/actions/archive_check.py` (new), `src/media_hygiene/index/parked.py`, `src/media_hygiene/services/quarantine_ledger.py`, `src/media_hygiene/services/backup_reasons.py`, `src/media_hygiene/services/phone_known.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/purge_settings.py` (new), `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_purge.ps1.j2` (new), `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_purge_archive.py` (new), `tests/integration/test_purge_archive.py` (new), `documentation/en/commands/purge.md`, `documentation/fr/commands/purge.md`, `documentation/en/clean/` (the step that purges), `documentation/fr/clean/` (same)

## Context

Today `purge` has one outcome: `shutil.rmtree` of each run's quarantine folder
(`actions/purge.py`, `purge_run`), then `<run>.purged.json` (`actions/purged.py`) and
`forget_runs` in the index. The maintainer wants the space back on the PC **without ever
erasing anything**: the quarantine goes to another place first (a NAS share, an external disk, a
cloud's synced folder), and only once that copy is proven is the quarantine emptied.

Decided with the maintainer (chat of 2026-10-22):

1. A `--to <folder>` option on `purge`.
2. A `[purge] archive_to = "\\NAS\archives_quarantaine"` setting: when it is set, plain
   `mh purge` archives by default, so "I never delete anything" holds without typing the option.
3. Plain `mh purge` with neither `--to` nor `archive_to`, and without `--yes`, **shows the
   option before the confirmation question**, with examples for a NAS, a disk and a cloud, so the
   user learns it exists while there is still time to use it.

## What the user sees

Without `--to` and without `archive_to` (the question stays as today; a block is added above it):

```
⚠ 'purge' efface pour de bon : ces fichiers ne peuvent pas revenir, même avec 'undo'.

💾 Plutôt garder une copie ailleurs ? mh purge --to <dossier> copie d'abord la
   quarantaine, vérifie la copie, puis seulement vide la quarantaine. <dossier> peut être :
     • un NAS            \\NAS\archives_quarantaine
     • un disque externe F:\archives
     • un cloud          C:\Users\<vous>\OneDrive\archives  (le dossier synchronisé)
   Pour toujours archiver : [purge] archive_to dans config.toml.

Effacer la quarantaine de 20261020-143012 (15 888 fichiers, 42 Go) ? [o/N] :
```

- Not shown with `--to`, with `archive_to` set, or with `--yes` (a script: nobody reads it).
- With `archive_to` set (or `--to`): "Copier la quarantaine de … (15 888 fichiers, 42 Go) vers
  \\NAS\archives_quarantaine, vérifier la copie, puis la vider ? [O/n]".
- `--no-archive` erases without a copy even when `archive_to` is set (asked as today).
- `--yes` with `archive_to` set **archives**: a setting that says "never erase" is never bypassed
  silently.
- Last line: what was copied where, read back from the target (product rule: a save is shown
  from disk, never from memory), and ONE 👉 line: how to get a run back (below).

## How

**The copy is made by Windows**, like `mh backup` (0264): SMB from Windows was measured
86–105.8 MB/s against 15.1 MB/s through a Docker CIFS volume (0264's context, step 21 of
`mh-measure.ps1`, DS216j, reads). Any path Windows can write works, which is how "a cloud" is
covered: its desktop client's synced folder, no cloud API.

1. `mh.ps1` sees `purge` with `--to` (or reads `archive_to` through the container, as `backup`
   reads its settings) and runs it in three steps, `mh_purge.ps1.j2` (new, modelled on
   `mh_backup.ps1.j2`):
   1. the container lists the runs to archive and their folders, per drive quarantine
      (`run_folders`), read-only, with the same refusals as today (drive quarantine not mounted:
      the run is kept, 0183);
   2. Windows copies each `X:\media-hygiene\quarantine\<run>` to `<target>\<run>` with
      `robocopy` (`/E /COPY:DAT`, never `/MOVE`, `/MIR` nor `/PURGE`); several drives' folders of
      one run merge into `<target>\<run>\` — **to decide**: keep a `<drive>` level
      (`<target>\<run>\E\…`) so a copy back knows which quarantine each file came from; likely
      needed;
   3. the container, with the target mounted **read-only**, checks every file of the run is
      there with the same size (`archive_check.py`), then erases the run as `purge` does. One
      file missing or different: that run is not erased, said with the file names.
2. Refusals: a target inside a photo folder, a `--backup` folder, the quarantine or another tool
   folder (reuse 0264's overlap check and `refuse_tool_folders_in_data`); `robocopy` exit code
   ≥ 8 (failure) stops before step 3.
3. The record: `<run>.archived.json` next to `<run>.purged.json`'s place (`version`, `run`,
   `archived` date, `target` as Windows writes it). `history` shows "archivé vers \\NAS\…".
   **Every reader of `purged` treats an archived run as purged** (`quarantine_ledger`,
   `backup_reasons`, `phone_known`, `phone_*`: they use it to know the user set those files aside
   on purpose, e.g. never to re-import them) — list every reader and test each.
4. Getting a run back: the user copies `<target>\<run>` back into the quarantine, then `undo
   <run>` works (it rebuilds from the quarantine). For that, an archived run **must keep** what
   `forget_runs` (`index/parked.py`) drops for a purged one, or `undo` must cope without it —
   check which, and test the round trip: clean → purge --to → copy back → undo. Whether `undo`
   should copy back by itself (`undo <run>` finds `.archived.json` and offers it) is a follow-up,
   not this TODO.
5. `mh.sh` (Linux/WSL launcher): same steps with `cp -a` or `rsync` if `mh_backup.sh.j2` already
   does so; otherwise state the gap.

## Decided (2026-10-23)

By the maintainer, at the start of `/todo:iterate`:

- **A `<drive>` level** in the target (`<target>\<run>\E\…`, step 1.2): yes, so a copy back
  plus `undo` puts each file back in its own drive's quarantine.
- **The target's free space is checked before copying**: a clear refusal at once ("12 GB
  missing on \\NAS\…"), nothing copied, nothing erased — instead of robocopy failing midway.

## Questions left open

- The `<drive>` level in the target (step 1.2): proposed yes.
- A cloud's synced folder proves the local copy only, not the upload: say so in the docs
  ("as safe as your sync"); OneDrive's Files On-Demand behaviour on a 42 GB copy is **to check**.
- Free space on the target is not checked beforehand: robocopy fails and step 3 refuses. Enough?
- Should `archive_to` also take a per-drive form (each drive's quarantine to its own target)?
  Not asked: no.

## Tests

- Unit: the hint block shown / not shown (no option, `--to`, `archive_to`, `--yes`); `--yes` +
  `archive_to` archives; `--no-archive`; the check refuses a missing file, a file of another size,
  and passes an identical copy; target overlap refusals.
- Integration (`tmp_path` as the target, the copy made by Python in place of robocopy): a run on
  two drive quarantines; a run kept because its drive is not mounted; the archived record read by
  every `purged` reader; the round trip clean → archive → copy back → undo.

## Documentation

`commands/purge.md` (EN + FR): the option, the setting, the three kinds of targets, how to get a
run back; the clean guide's step that purges mentions it; the `config.toml` template comments
`[purge] archive_to`. The console output of `purge` changes: `docs_screenshots` should run
afterwards (not unasked).

## Where the user gains

Before: emptying the quarantine erased it for good (only `undo` before the purge could help).
After: the PC's space comes back just the same (100 % of the quarantine freed, as today) and
0 file is erased while `archive_to` is set; a run stays recoverable by one folder copy + `undo`.

## Decided (2026-10-26)

By the maintainer, at the start of `/todo:iterate`:

- The target keeps a `<drive>` level (`<target>\C\…`, `<target>\D\…`): two quarantines never mix.
- Free space on the target is checked before the copy (quarantine size vs free space): refused
  early, with a clear message.
- The cloud note ("as safe as your sync") goes in the docs; OneDrive's Files On-Demand behaviour
  stays to check by the maintainer.
