# `audit`: find the duplicates and the broken files

[Documentation](../README.md) › [Commands](../reference-commands.md) › `audit` · 🇫🇷 [Français](../../fr/commands/audit.md)

## In short

**Know, without any risk, how many copies your folders hold and how much space they take.**

`audit` looks at every photo, RAW file and video of the folders you mount, and tells you what it
finds: identical copies, broken files, [orphan sidecars](../reference-glossary.md#orphan-sidecar), near duplicates and [burst series](../reference-glossary.md#burst-series). It
changes nothing.

**When**: the very first time; then before every `clean` (with the same options, to check which
copy stays), and after adding photos or a disk.

**Try it**:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene audit
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`, the system itself then forbids any change. |
| Needs | Your folders, one `-v` each (`/data/<drive>/<path>`). |
| Recommended | `/cache` (the next audits take seconds), `/reports` (the HTML report), `/config` (your `config.toml`). |
| Writes | The cache, and a report in `/reports/<date>-audit/` when `/reports` is mounted. |
| Undo | Nothing to undo: nothing changed. |
| With `mh` | `mh audit` ([`launcher`](launcher.md)). |

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
| `--prefer PATH` | Folder whose copies are kept first; repeat it, the order matters. [Cleaning, step 5](../clean/05-choose-the-kept-copy.md#prefer-a-folder) |
| `--protect PATH` | Folder never modified; its files are the copies kept. [Cleaning, step 5](../clean/05-choose-the-kept-copy.md#protect-a-folder) |
| `--exclude PATH` | Folder never analysed, not even read. [Cleaning, step 5](../clean/05-choose-the-kept-copy.md#exclude-a-folder) |
| `--backup PATH` | A backup or an old disk: compared, never changed. Says what it lacks and what only it holds (`backup-missing.csv`, `backup-only.csv`). [Cleaning, step 5](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk) |
| `--exclude-name NAME` | Folder name never analysed, wherever it is (`--exclude-name Thumbnails,.Trash-*`). [Cleaning, step 5](../clean/05-choose-the-kept-copy.md#skip-a-folder-name-on-every-disk) |
| `--full` | Read every folder again, even those unchanged since the last audit (taken from the cache otherwise): for a photo changed in place by another program. [Step 2](../start/02-keep-the-cache.md#what-changes) |
| `--ext EXT` | Only these categories or extensions (`--ext photo,video`, `--ext heic`); photo, RAW and video extensions only. [Cleaning, step 6](../clean/06-file-types.md) |
| `--people` | Then look for faces in the photos not looked at yet, after saying how long it takes and asking ([People](../reference-people.md#during-the-audit-audit---people)); `with_audit = true` in `[people]` does it at every audit. |
| `--reread` | Only read again in full the files read longest ago, up to `reread_gb` of `[routine]` (20 GB by default), to find a file a disk damaged without changing its size or date; then list the damaged files and where a good copy is (a duplicate, a backup, the quarantine). Changes nothing 🔒; `clean --repair` restores them. [Safety](../reference-safety.md#a-file-damaged-by-the-disk) |
| `--yes`, `-y` | With `--people`: do not ask. Without a terminal (no `-it`), `--people` needs it: nothing waits for an answer. |

Paths are written the Windows way (`C:\Photos\Family`), as you see them in the Explorer. Every
option has its line in `config.toml` ([cleaning, step 7](../clean/07-configuration-file.md)): write it
once, the command line still wins.

## Examples

```powershell
# Keep the copies of the main phone folder first
cavo789/media-hygiene audit --prefer "C:\Photos\Phone"

# Is the backup complete? Can the old disk be wiped? Compared, never changed
cavo789/media-hygiene audit --backup "D:\Backup"

# Only the videos
cavo789/media-hygiene audit --ext video

# Everything the files say about themselves (dates, GPS, formats), after the summary,
# and how long each step took (listing, checks, fingerprints, near duplicates…)
cavo789/media-hygiene --verbosity verbose audit

# Then the faces, once you agreed to the time it takes (needs /cache)
cavo789/media-hygiene audit --people
```

(each one with the same `docker run … -v …` part as above)

## Good to know

- **Ctrl+C** stops at any moment, without an error message: nothing has changed.
- **The first audit** of a large library can take a long while; with
  [the cache](../start/02-keep-the-cache.md), the next ones only read the new or changed files.
- **Thumbnails, last step**: with the cache, the audit then makes the thumbnails the library
  shows, so it opens at once. The report is already written: **Ctrl+C** skips this step, and
  the photos left get their thumbnail when a page first shows them.
- **Mount each folder once**: `C:\Photos` already includes `C:\Photos\2019`. A folder mounted
  twice is refused, rather than taking a photo for a copy of itself.
- **A backup or an old disk**: `--backup` compares it without changing it, and says what it
  lacks and what only it holds.
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
│ --help  -h      <bool>  Show this message and exit.                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --prefer         <list[str]>  Folder whose copies are kept first. Repeat it; │
│                               the order matters.                             │
│ --protect        <list[str]>  Folder never modified; its files are the       │
│                               copies kept. Repeatable.                       │
│ --exclude        <list[str]>  Folder never analysed, not even read.          │
│                               Repeatable.                                    │
│ --backup         <list[str]>  A backup or an old disk: compared, never       │
│                               changed. Says what it lacks and what only it   │
│                               holds. Repeatable.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: scan (override scan.* of config.toml) ────────────────────────────╮
│ --ext                 <list[str]>  Only analyse these categories or          │
│                                    extensions, e.g. --ext photo,video or     │
│                                    --ext png,webp (repeatable). Categories:  │
│                                    photo, raw, video, media and those of     │
│                                    scan.categories in config.toml. Photo,    │
│                                    RAW and video extensions only. Default:   │
│                                    media (every photo, RAW and video).       │
│ --exclude-name        <list[str]>  Folder name never analysed, wherever it   │
│                                    is, case ignored; * and ? allowed, e.g.   │
│                                    --exclude-name Thumbnails,.Trash-*        │
│                                    (repeatable). Adds to the system folders  │
│                                    already skipped. For one precise folder,  │
│                                    use --exclude.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --full            <bool>  Read every folder again, even those that did not   │
│                           change since the last audit: for a photo changed   │
│                           in place by another program.                       │
│ --people          <bool>  Then look for faces in the photos not looked at    │
│                           yet (as 'people' does), after saying how long it   │
│                           takes and asking.                                  │
│ --yes     -y      <bool>  With --people: do not ask, go on.                  │
│ --reread          <bool>  Only read again in full the files read longest     │
│                           ago, up to  reread_gb, to find a file a disk       │
│                           damaged without changing its size or date; then    │
│                           list the damaged files and where a good copy is.   │
│                           Changes nothing.                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
