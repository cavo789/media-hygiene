# `clean`: set the extra copies aside

[Documentation](../README.md) › [Commands](../reference-commands.md) › `clean` · 🇫🇷 [Français](../../fr/commands/clean.md)

## In short

**Free the space your duplicate photos take, safely: the extra copies are set aside, never
erased, and everything can be put back.**

`clean` audits again, shows you what it is about to do, **asks**, then moves the extra copies to
the [quarantine](../reference-glossary.md#quarantine), after comparing each one byte for byte with the copy kept. `undo` puts
everything back; the space is freed only when you `purge` the quarantine.

**When**: after an [`audit`](audit.md) whose folder pairs you have read and agree with.

**Try it**:

```powershell
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts: moves the extra copies, unreadable files and orphan sidecars to the quarantine; deletes the empty files (0 bytes) and the folders it leaves empty. |
| Needs | Your folders **without** `:ro`, `/journal` and `/quarantine` (folders of yours). |
| Recommended | `/cache`, `/reports`, `/config`. |
| Writes | The journal of the run, the quarantine, the clean report. |
| Undo | [`undo`](undo.md) restores every file of the run. |
| With `mh` | `mh clean`: your folders are mounted writable for this command only. |

## Run it

Create the journal and the quarantine once, then run the command of your audit without `:ro`,
with both folders and `clean` instead of `audit`:

```powershell
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean
```

It shows the summary and the folder pairs, then asks: *❓ Move 32 duplicate copies (14.0 MB) to
the quarantine and handle 3 broken files? [y/N]*. Anything but `y` stops
here, and nothing changes. With `y`, a line under the bar names each file and what happens to it;
the table at the end counts what was moved, skipped and failed.

## What happens to each file

| File | What `clean` does |
|---|---|
| Extra copy of a photo or video | **Moved** to the quarantine, right after a last byte comparison with the kept copy. Different in any way? Skipped. |
| Empty file (0 bytes) | Deleted: it holds nothing (`undo` recreates it). |
| Unreadable file | Moved to the quarantine. |
| Orphan [sidecar](../reference-sidecars.md) | Moved to the quarantine. |
| Near duplicates, burst shots | Untouched, unless you ask (`--tier`, `--decisions`). |
| Copy of a pair keeping both names (`--decisions`) | **Replaced by a hard link** to the kept file, after the same byte comparison: the name stays, the space is freed. Across disks: refused, said. [Cleaning, step 12](../clean/12-decide-pair-by-pair.md#keep-both-names-a-link) |
| A file you had set aside, back since (a phone backup) | Moved to the quarantine again, counted on a line of its own. [Cleaning, step 9](../clean/09-undo-history-purge.md#what-you-set-aside-stays-set-aside) |
| Files of a protected folder | Untouched, always. |

The quarantine keeps the original paths below one folder per run:
`quarantine\<run>\d\Old disk\2020\IMG_1203.jpg`.

**A folder left empty goes too.** Once its files are set aside, a folder holding nothing else
(or only `Thumbs.db`, `desktop.ini`, `.DS_Store`: `[sort] junk_files`, moved to the quarantine
first) is removed, then its parent if that one is empty in turn. Before asking, `clean` says how
many folders will go; the end of the run and [`history`](history.md) say how many went, and
`undo` recreates them before putting the files back. Never removed: the folders you mounted, a
protected, backup or excluded folder, a folder already empty before the run. With `--delete` and
no quarantine mounted, a folder holding only such system files stays. A run stopped with Ctrl+C
removes no folder.

## Options

| Option | What it does |
|---|---|
| `--tier exact` | The default: byte-for-byte copies only. |
| `--tier near` | Also the **sure** near duplicates and re-encoded videos, and the groups decided with `review --near`. [Cleaning, step 11](../clean/11-near-duplicates.md#sure-groups-and-groups-to-check) |
| `--tier near-all` | Every near duplicate, as the report shows them: look at them first. |
| `--decisions [FILE]` | Apply the choices made in the browser: folder pairs of a report ([cleaning, step 12](../clean/12-decide-pair-by-pair.md)), burst shots set aside and near duplicates decided with [`review`](review.md), photos set aside in [`search`](search.md#set-photos-aside). Alone, it reads `decisions.json` from `/reports`. |
| `--yes`, `-y` | Do not ask (needed without `-it`). |
| `--delete` | Delete the exact copies for good instead of moving them; `undo` rebuilds them from the kept copy. [Cleaning, step 8](../clean/08-clean.md#need-the-space-at-once---delete) |
| `--prefer`, `--protect`, `--exclude`, `--exclude-name`, `--ext` | As for [`audit`](audit.md#options): give `clean` the same ones as the audit you read. |

## Examples

```powershell
# The identical copies only (the default)
cavo789/media-hygiene clean

# Also the sure near duplicates, and the bursts and groups decided in review
cavo789/media-hygiene clean --tier near --decisions

# A script, a scheduled task: no question
cavo789/media-hygiene clean --yes
```

(each one with the same `docker run … -v …` part as above)

## Good to know

- **Start small**: one subfolder, check, then widen. Pause OneDrive, Google Drive or Dropbox
  while it runs.
- **Refusals that protect you**: `clean` stops before the analysis without `/journal` or
  `/quarantine`, with a `:ro` folder, with a folder it cannot write to, or with a tool folder
  placed inside a photo folder. The message says which one.
- **Interrupted?** Ctrl+C, a power cut: each action is written to the journal before and after it
  happens, so `undo` still restores what was done.
- **Once applied**, `decisions.json` is archived as `decisions.applied-<run>.json`: after an
  `undo`, `--decisions` with that name applies the same choices again.
- If [Czkawka](crosscheck.md) gave its opinion, `clean` recalls its verdict before asking.
- `confirm = false` in the `[clean]` section of `config.toml` is the same as `--yes`, every time.

## Go further

- [8. Clean](../clean/08-clean.md), [9. Undo, history, purge](../clean/09-undo-history-purge.md)
- [10. Burst series](../clean/10-review-bursts.md), [11. Near duplicates](../clean/11-near-duplicates.md),
  [12. Decide pair by pair](../clean/12-decide-pair-by-pair.md)
- [How your photos stay safe](../reference-safety.md): every check made before a file moves.
- Next: [`history`](history.md) lists the run, [`undo`](undo.md) reverts it, [`purge`](purge.md)
  frees the space.

## The built-in help

<details>
<summary><code>clean --help</code></summary>

<!-- capture: help-clean.txt -->
```text
 Usage: media-hygiene clean [OPTIONS]

 Audit, confirm, then move the duplicate copies to the quarantine, after a byte
 comparison (journaled, undoable); --delete deletes them for good.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --tier               <exact|near|near-all>  How far to clean. exact          │
│                                             (default): the byte-for-byte     │
│                                             copies only. near: also the      │
│                                             shrunk copies (sent by WhatsApp  │
│                                             or e-mail, resized,              │
│                                             recompressed) and the re-encoded │
│                                             videos that are sure; the groups │
│                                             to check are left alone.         │
│                                             near-all: every near duplicate;  │
│                                             check them in the report first.  │
│                                             Near duplicates go to the        │
│                                             quarantine, never deleted.       │
│ --decisions          <path>                 Apply the choices made in the    │
│                                             browser: decisions.json          │
│                                             downloaded from an audit report  │
│                                             (swap or leave alone some folder │
│                                             pairs) or written by 'review'    │
│                                             (burst shots set aside, near     │
│                                             duplicates decided). A relative  │
│                                             path is read from the folder     │
│                                             mounted on /reports. The file is │
│                                             refused if the folders, the      │
│                                             pairs or the series changed.     │
│                                             Alone, --decisions reads         │
│                                             decisions.json.                  │
│ --yes        -y                             Do not ask for confirmation      │
│                                             (overrides clean.confirm).       │
│ --help       -h                             Show this message and exit.      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --delete          Free the space at once: delete the exact copies for good,  │
│                   after a byte comparison with the kept copy, instead of     │
│                   moving them to the quarantine; 'undo' rebuilds them from   │
│                   the kept copy.                                             │
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
