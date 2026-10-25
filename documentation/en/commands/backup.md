# `backup`: copy your photos to the NAS, only what it lacks

[Documentation](../README.md) › [Commands](../reference-commands.md) › `backup` · 🇫🇷 [Français](../../fr/commands/backup.md)

> **Windows only.** Type it in **Windows PowerShell**: `mh backup --to \\<NAS>\backup_photos`.
> Windows writes to the NAS about 7 times faster than a copy through Docker (86 to 105.8 MB/s
> against 15.1 MB/s, measured on a Synology over Ethernet); the `mh` of WSL or Linux refuses it
> and says this same command.

## In short

**Copy every photo folder `mh` knows into a folder of their own on the NAS: only what it lacks;
a photo moved on the PC is renamed there, never sent again; a photo deleted by mistake is never
deleted from the NAS.**

The container decides (it knows your audits, what you moved, set aside or purged), Windows
copies: renames with `Move-Item`, copies with `robocopy`. Your photos are only read.

**When**: after an import, a clean or a sort; as often as you like, a run with nothing new only
lists both sides.

**Try it** (the first time, then `mh backup` alone):

```powershell
mh backup --to \\NAS\backup_photos
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Only read (mounted `:ro`). |
| The backup folder | ✋ Written by Windows: new files copied, renamed files renamed, files set aside in `.removed`. Never `robocopy /MIR` nor `/PURGE`. |
| Needs | Windows PowerShell; a shared folder of its own on the NAS (in DSM: *Control Panel → Shared Folder → Create*, e.g. `backup_photos`); `/journal`; `/cache`. |
| Undo | `mh backup --undo <run>` puts back what a run renamed or set aside (the copies stay). |
| With `mh` | `mh backup --to <folder>` once, then `mh backup`; `--anyway`; `--undo <run>`. |

## The backup folder

A folder **of its own**: never your NAS's `Photos` share (a [backup you compare](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk),
which no command changes), never a photo folder, never inside one: `mh` refuses such a folder
and names both. Each photo folder goes below it by its own path, the drive as a folder:
`C:\Photos` into `\\NAS\backup_photos\C\Photos`, so two folders of the same name never meet.
The folder given with `--to` is kept (`%USERPROFILE%\media-hygiene\backup-target.txt`), read back
and said; the NAS's password is the one `mh folders add --backup` kept, else asked once. When
Windows cannot open the share yet, it gets a free drive letter (`Z:` first) for the time of the
run, removed after.

## What a run does

1. **Lists** your photo folders and the backup (size, date): every file, not only photos (a PDF
   in `C:\Photos` is backed up too), but the system folders (`#recycle`, `@eaDir`…), the
   excluded ones and the quarantine.
2. **Plans**, and says it: what is already there, what is new, what moved (same size, date and
   first and last 64 KB: renamed on the NAS, nothing sent), what was edited (the NAS's copy set
   aside first), what is gone from the PC.
3. **Asks once**, journals each rename, then Windows renames and runs `robocopy` per folder:
   only the files new or changed by size and date are copied, an interrupted run goes on at
   the next one.
4. **Proves**: the backup is listed again, each copy found with its size and date (a file
   robocopy failed is named), the run recorded in [`history`](history.md).

A folder not plugged in (a USB disk) or not read whole leaves its part of the backup as it is.

## What leaves the backup

A file the PC no longer has is **set aside** in `\\NAS\backup_photos\.removed\<run>\…`, and
only when you removed it on purpose: **purged** from the quarantine (or deleted by `clean` as an
exact copy), or **confirmed** deleted in [`review --gone`](review.md). A file still in the
quarantine, a deletion not confirmed yet, or one the tool knows nothing of (a deletion by
mistake?) **stays**, counted by reason. The previous copy of an edited file goes to `.removed`
too. `.removed` is emptied after `keep_removed_days` (90 days).

A file the [audit](audit.md) found broken never replaces its copy in the backup.

**The safety stop**: when the files set aside and replaced exceed `stop_above_percent` (20 %)
of the backup, nothing is applied: a drive missing? many files changed at once? Look, then
`mh backup --anyway`.

## Speed

A first backup of 240.9 GB: about 40 minutes at Windows's 100 MB/s, against 4 h 28 through
Docker at 15 MB/s (estimated from the reads measured; the NAS's write speed is measured by step
27 of `mh-measure.ps1`). The next runs list both sides (about 21 s for 52,094 files, estimated)
and copy only the new files; after a sort that moves the whole library, renames only.

## Settings (`config.toml`)

| Setting | Default | What it does |
|---|---|---|
| `[backup] keep_removed_days` | `90` | Days a file waits in `.removed` before `mh backup` erases it. |
| `[backup] stop_above_percent` | `20` | The safety stop. |
| `[backup] threads` | `8` | Files robocopy copies at once (`/MT`). |

## Options

| Option | What it does |
|---|---|
| `--to FOLDER` | The backup folder (`\\NAS\backup_photos`, or a drive's folder); kept for the next runs. |
| `--anyway` | Go past the safety stop. |
| `--undo RUN` | Put back what that run renamed or set aside (`mh` only). |
| `--backup PATH` | A backup compared, which the folder must not overlap (`mh` passes yours). |

Run by hand (`docker run … media-hygiene backup --to …`), the command only shows the plan.

## Go further

- [Several folders: your NAS](../start/03-several-folders.md#your-nas-back-up-your-photos-to-it)
- [`import`](import.md): get back what only the NAS holds
- [The `mh` launcher](launcher.md)

## The built-in help

<details>
<summary><code>backup --help</code></summary>

<!-- capture: help-backup.txt -->
```text
 Usage: media-hygiene backup [OPTIONS]

 Windows only, as mh backup: copy your photo folders into a folder of their own
 on the NAS, only what it lacks; a photo moved is renamed there, a deletion by
 mistake never carried over. Run here, it shows the plan.
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
