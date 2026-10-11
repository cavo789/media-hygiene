# `audit`: find the duplicates and the broken files

[Documentation](../README.md) › [Commands](../reference-commands.md) › `audit` · 🇫🇷 [Français](../../fr/commands/audit.md)

`audit` looks at every photo, RAW file and video of the folders you mount, and tells you what it
finds: identical copies, broken files, orphan sidecars, near duplicates and burst series. It is
the first command to run, and the one to run again whenever you want to know where you stand.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`, the system itself then forbids any change. |
| Needs | Your folders, one `-v` each (`/data/<drive>/<path>`). |
| Recommended | `/cache` (the next audits take seconds), `/reports` (the HTML report), `/config` (your `config.toml`). |
| Writes | The cache, and a report in `/reports/<date>-audit/` when `/reports` is mounted. |
| Undo | Nothing to undo: nothing changed. |
| With `mh` | `mh audit` ([`launcher`](launcher.md)). |

## When to use it

- **The very first time**: to see, without any risk, how many copies your folders hold and how
  much space they take.
- **Before every `clean`**, with the same options, to read the folder pairs and check which copy
  stays.
- **After adding photos** or a disk: with the cache, only the new files are read.

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene audit
```

It prints, in this order:

1. **Audit summary**: files scanned, groups of identical files, extra copies, space to free,
   broken files, near duplicates, burst series.
2. **Folders sharing identical files**: one sentence per pair of folders, the folder that keeps
   its copies first.
3. **What you can do**: at most three lines (identical copies, near duplicates, bursts), each
   with what it gains and what it costs you.
4. **👉 What next**: the next step, as a full command ready to paste, then one or two 💡 tips.

[Your first audit](../start/01-first-audit.md#read-the-result) explains each line.

## Options

| Option | What it does |
|---|---|
| `--prefer PATH` | Folder whose copies are kept first; repeat it, the order matters. [Step 5](../clean/05-choose-the-kept-copy.md#prefer-a-folder) |
| `--protect PATH` | Folder never modified; its files are the copies kept. [Step 5](../clean/05-choose-the-kept-copy.md#protect-a-folder) |
| `--exclude PATH` | Folder never analysed, such as a real backup. [Step 5](../clean/05-choose-the-kept-copy.md#exclude-a-folder) |
| `--exclude-name NAME` | Folder name never analysed, wherever it is (`--exclude-name Thumbnails,.Trash-*`). [Step 5](../clean/05-choose-the-kept-copy.md#skip-a-folder-name-on-every-disk) |
| `--ext EXT` | Only these categories or extensions (`--ext photo,video`, `--ext heic`); other file types too (`--ext pdf,docx`). [Step 6](../clean/06-file-types.md) |

Paths are written the Windows way (`C:\Photos\Family`), as you see them in the Explorer. Every
option has its line in `config.toml` ([step 7](../clean/07-configuration-file.md)): write it
once, the command line still wins.

## Examples

```powershell
# Keep the copies of the main phone folder first
cavo789/media-hygiene audit --prefer "C:\Photos\Phone"

# Leave a real backup out of the analysis
cavo789/media-hygiene audit --exclude "D:\Backup"

# Only the videos
cavo789/media-hygiene audit --ext video

# Everything the files say about themselves (dates, GPS, formats), after the summary
cavo789/media-hygiene --verbosity verbose audit
```

(each one with the same `docker run … -v …` part as above)

## Good to know

- **Ctrl+C** stops at any moment, without an error message: nothing has changed.
- **The first audit** of a large library can take a long while; with
  [the cache](../start/02-keep-the-cache.md), the next ones only read the new or changed files.
- **Mount each folder once**: `C:\Photos` already includes `C:\Photos\2019`. A folder mounted
  twice is refused, rather than taking a photo for a copy of itself.
- **A real backup** must stay a copy: leave it out, or `--exclude` it.
- The summary of a **near duplicate** or a **burst** is only a forecast: a plain `clean` never
  touches them.

## Go further

- [1. Your first audit](../start/01-first-audit.md), [2. Keep the cache](../start/02-keep-the-cache.md),
  [3. Several folders and disks](../start/03-several-folders.md)
- [4. The HTML report](../clean/04-html-report.md): the pictures, the folder pairs, the proof.
- Next: [`clean`](clean.md) sets the extra copies aside; [`review`](review.md) sorts the bursts.

## The built-in help

<details>
<summary><code>audit --help</code></summary>

<!-- capture: help-audit.txt -->
```text
 Usage: media-hygiene audit [OPTIONS]

 🔒 Read-only: never changes your photos. Find exact duplicates and broken
 files.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, e.g. a real backup to keep.   │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: scan (override scan.* of config.toml) ────────────────────────────╮
│ --ext                 <str>  Only analyse these categories or extensions,    │
│                              e.g. --ext photo,video or --ext png,webp        │
│                              (repeatable). Categories: photo, raw, video,    │
│                              media and those of scan.categories in           │
│                              config.toml. Other types too, such as --ext     │
│                              pdf,docx: their copies are moved to the         │
│                              quarantine. Default: media (every photo, RAW    │
│                              and video).                                     │
│ --exclude-name        <str>  Folder name never analysed, wherever it is,     │
│                              case ignored; * and ? allowed, e.g.             │
│                              --exclude-name Thumbnails,.Trash-*              │
│                              (repeatable). Adds to the system folders        │
│                              already skipped. For one precise folder, use    │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
