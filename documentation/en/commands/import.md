# `import`: bring in what only a folder holds (NAS, USB disk, SD card)

[Documentation](../README.md) › [Commands](../reference-commands.md) › `import` · 🇫🇷 [Français](../../fr/commands/import.md)

## In short

**Copy into your photos the photos and videos only a folder has: your NAS, a USB disk, an SD
card, an old disk. Never the ones you set aside or deleted on purpose.**

Your NAS (or an old disk) is a [backup folder](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk):
the audit compares it with your photos and says what only it holds. `import` copies those
files into your photos, each one checked, so the NAS is never needed to keep them. Matched by
content (SHA-256), whatever their name or place.

**When**: once a backup folder is added (`mh folders add --backup \\NAS\Photos`), after an
[`audit`](audit.md) said *files are only in it, never in your photos*. Or at once, for a folder
you plug in now (an SD card, a friend's USB disk): name it on the command, nothing to add first.

**Try it**:

```powershell
mh import            # your backup folders (the NAS)
mh import E:\DCIM    # that folder only: read, never added to mh
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts: copies files **into** your photos (below `From NAS`, `From E`…), never changes one there. |
| The folder | Only read (mounted `:ro`): nothing on the NAS, the disk or the card is written, moved nor deleted. |
| Needs | A backup folder, or a folder named on the command; your photo folders **without** `:ro`; `/journal`; `/cache`. |
| Undo | [`undo <run>`](undo.md) removes the copies (a copy you edited since is kept). |
| With `mh` | `mh import`, `mh import E:\DCIM`, `mh import --yes`. |

## What is copied, what is not

`import` audits first, with the backup, then sorts what only the backup holds:

- **Copied**: the files whose content was never in your photos.
- **Not proposed, counted apart**: the ones you **set aside** before (a burst shot, a near copy,
  a photo chosen or unwanted, in the quarantine or purged since), and the ones you **deleted**
  in the Explorer, confirmed or still waiting for [`review --gone`](review.md). The audit says
  how many: *2 other files are ones you set aside or deleted before: not proposed.* A deletion by
  mistake? The file is still on the NAS: copy it by hand.
- **Listed apart**: a photo whose **near copy** is in your photos (another size or format, a
  HEIC on the NAS and its JPG on the PC): *probably in your photos already*, not copied.
- **Once**: two identical files of the backup (same size, same start and end) are copied once.

The copies go to **`From <source>`** in your first photo folder: `From NAS` for a network
share, `From E` for a folder of drive `E:`, its folders kept below it
(`C:\Photos\From NAS\2019\Été\IMG_0007.jpg`, `C:\Photos\From E\100CANON\IMG_0008.jpg`), or to
the folder of `--to`. A file already copied by an earlier import, wherever it is now, is in
your photos: never copied twice. Sort them later
with [`classify`](classify.md) and [`sort`](sort.md), as any folder.

## How a copy is made

Each file is journaled first, copied under a temporary name (the NAS is read once, hashed as it
is read), read back and compared with the source (SHA-256), then given its name and its
modification time. A name taken meanwhile is never replaced. The next audit sees the copies as
your photos: nothing is left to import.

## Speed

Over the network, only the list of the NAS's files is read for most of them (size, date: 253
files in 0.1 s, measured). Of a file of the same size as one of your photos, only its first and
last 64 KB are read: same size and same start and end, it is in your photos. The NAS is never
read whole, only the files really copied are. Through Docker Desktop a NAS is read at about
**15 MB/s** (measured on a Synology over Ethernet): 300 GB of photos of 5 MB, about 8 minutes for
a first comparison instead of 5 h 30 read whole (estimated from that rate); the next ones only
read what changed.

The trade-off: a NAS file whose start and end match one of your photos but whose middle differs
counts as in your photos. It stays on the NAS: nothing is lost.

## Options

| Option | What it does |
|---|---|
| `FOLDER` | The folder to import from (host path), instead of your backup folders: an SD card, a USB disk. Only read for this run, never added to `mh`. |
| `--to PATH` | Folder receiving the copies (host path); default: `From <source>` in your first photo folder. |
| `--yes`, `-y` | Copy without asking first. |
| `--backup PATH` | The backup folder to import from, when not in `config.toml` (`mh` passes yours). |

## Good to know

- **A NAS with an old SMB**: Docker Desktop reads a NAS through SMB 3 only. If `mh` says the NAS
  offers an older version, in DSM (Synology): *Control Panel → File Services → SMB → Advanced
  Settings → Maximum SMB protocol: SMB3*.
- **The NAS powered off**: `import` says so; the audit goes on without it.
- **Safe**: refused without a journal, or with your photo folders read-only, like every command
  that changes files.

## Go further

- [Compare a backup or an old disk](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk)
- [Several folders](../start/03-several-folders.md)

## The built-in help

<details>
<summary><code>import --help</code></summary>

<!-- capture: help-import.txt -->
```text
 Usage: media-hygiene import [OPTIONS]

 Copy into your photos what only a backup (a NAS) holds, never what you set
 aside or deleted before; each copy proven (journaled, undoable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --to            <str>  Folder receiving the copies (host path); default:     │
│                        'From NAS' in your first photo folder, the folders of │
│                        the backup kept below it.                             │
│ --yes   -y             Copy without asking first.                            │
│ --help  -h             Show this message and exit.                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --backup        <str>  A backup or an old disk: compared, never changed.     │
│                        Says what it lacks and what only it holds.            │
│                        Repeatable.                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
