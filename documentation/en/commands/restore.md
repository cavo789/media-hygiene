# `restore`: a backup of the index put back

[Documentation](../README.md) › [Commands](../reference-commands.md) › `restore` · 🇫🇷 [Français](../../fr/commands/restore.md)

## In short

**The cache lost (Docker reset, volume removed): the index back in seconds, not the audits
again.**

`restore` puts back an archive written by [`backup`](backup.md): the most recent one of
`$HOME\media-hygiene\backups`, or the one you name. The next `mh audit` then reads again only
what changed since the backup.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Not read, never changed. |
| Needs | `/backups` (the archives), `/cache` (the index replaced), `/config` with `--config`. |
| Writes | The index in `/cache`; with `--config`, the settings in `/config`; a backup of the index replaced, in `/backups`. |
| With `mh` | `mh restore`: `mh` mounts `$HOME\media-hygiene\backups` for `backup` and `restore` only. |

## Run it

```powershell
mh restore
mh restore mh-backup-20261027-101500.zip
```

Nothing is overwritten before the archive is proven whole: every file against its SHA-256, the
index checked; an archive made by a newer version is refused (`mh update` first). Then the
index in place is **backed up first**, and the window ends on the line that puts it back:
`mh restore <that archive>`. The rows of each table are shown, read back from the restored index.

## Options

| Option | What it does |
|---|---|
| `archive` | The archive's name in `$HOME\media-hygiene\backups`; the most recent by default. |
| `--config` | Restore the settings too (`config.toml`, `people\*.toml`); the index alone by default, since you may have edited them since. A file written since the backup and absent from it stays. |

## Good to know

- A file moved, renamed or deleted since the backup: the index knows it by its path, so the
  next audit forgets the paths gone and reads the new ones; the words of `tags` of a moved file
  are computed again by the next `mh tags`.
- The `mh` script itself is never restored: `mh update` writes it again.

## Go further

- [`backup`: the index and the settings, kept outside Docker](backup.md)

## The built-in help

<details>
<summary><code>restore --help</code></summary>

<!-- capture: help-restore.txt -->
```text
 Usage: media-hygiene restore [OPTIONS] [archive]

 Put back a backup of the index (and the settings with --config), after backing
 up the current one.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   archive      <str>  The backup to restore, by its name; the most recent by │
│                       default.                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --config            Restore the settings (config.toml, people) too; the      │
│                     index alone by default.                                  │
│ --help    -h        Show this message and exit.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
