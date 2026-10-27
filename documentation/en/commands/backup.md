# `backup`: the index and the settings, kept outside Docker

[Documentation](../README.md) › [Commands](../reference-commands.md) › `backup` · 🇫🇷 [Français](../../fr/commands/backup.md)

## In short

**What the audits and `mh tags` learnt, kept safe from a Docker reset.**

The [cache](../reference-glossary.md#cache) (`/cache`) is a Docker volume, `media-hygiene-cache`:
a `docker volume prune`, a reset of Docker Desktop or a new WSL erases it. It holds the index:
the fingerprints of every file, what the audits read, and the words of `tags`, the descriptions,
the faces — hours of work to redo. `backup` writes the index and your settings (`config.toml`,
`people\*.toml`) into one zip, `mh-backup-YYYYMMDD-HHMMSS.zip`, in
`$HOME\media-hygiene\backups`; [`restore`](restore.md) puts it back.

Not to confuse with `--backup` (a folder [compared](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk)) nor with
[`push`](push.md) (your photos copied to the NAS): `backup` keeps the tool's own memory, never
a photo.

**When**: after a long `mh tags` or `mh people`, before a Docker Desktop update or reset.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Not read, never changed. |
| Needs | `/cache` (the index), `/config`, `/backups` (where the archive goes). |
| Writes | In `/backups` only: the archive; the 3 most recent are kept, older ones removed. |
| With `mh` | `mh backup`: `mh` mounts `$HOME\media-hygiene\backups` for `backup` and `restore` only. |

## Run it

In Windows PowerShell:

```powershell
mh backup
```

The index is copied with SQLite's own backup (consistent even while another window reads it),
then the archive is **read back from the disk**: every file checked against its SHA-256 in
`manifest.json`, the index checked whole (`PRAGMA integrity_check`). The window then shows the
archive, its size and the rows of each table read back (`files`, `tags`, `descriptions`,
`meanings`, `faces`).

The archive is on `C:`, like Docker's own disk: it protects from a wrong move, not from a disk
failure. Copy it to a USB stick or the NAS too.

With `docker run`, mount the folder of the archives yourself:

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\backups:/backups" `
  cavo789/media-hygiene backup
```

## Good to know

- Not in the archive: the previews (rebuilt by the reports), the models (downloaded again), the
  journal (it is already outside the volume, in `$HOME\media-hygiene\journal`), the NAS
  passwords (readable by your Windows account on this PC only).
- The 3 most recent archives are kept in `$HOME\media-hygiene\backups`; a fourth removes the
  oldest, said in one line.

## Go further

- [`restore`: put a backup back](restore.md)

## The built-in help

<details>
<summary><code>backup --help</code></summary>

<!-- capture: help-backup.txt -->
```text
 Usage: media-hygiene backup [OPTIONS]

 🔒 Read-only: never changes your photos. Back up the index and the settings
 into one archive outside Docker's cache volume, read back.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
