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
A phone over USB has no drive letter: [`mh import --phone`](#from-a-phone-mh-import---phone)
copies its new photos, Windows reading it itself.

**Try it**:

```powershell
mh import            # your backup folders (the NAS)
mh import E:\DCIM    # that folder only: read, never added to mh
mh import --phone    # a phone over USB, Windows only: below
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

## From a phone: `mh import --phone`

```powershell
mh import --phone                       # into <your first photo folder>\Phone\<the phone's name>
mh import --phone --to "D:\From phones" # elsewhere, then a folder per phone
mh import --phone --only Camera         # only the folder DCIM\Camera of the phone
mh import --phone --free                # then free the phone: below
```

Plug the phone in over USB, unlock it and choose *File transfer* (iPhone: *Trust this
computer*), and **keep it unlocked, screen on** until `mh` is done: asleep or locked, a phone
shows Windows no storage at all. Then `mh import --phone` says *answers but shows no storage: wake it up
and unlock it…* and waits for it, up to a minute. It finds the phone (several phones: it asks
which one), lists its `DCIM` folder
(about 30 seconds per 1,000 files), then copies **only** what your library does not hold yet:

- **already in your library**: a file of the same name (case ignored) and the same size that an
  audit has seen, on any of your disks, plugged in or not;
- **set aside on purpose before**: a burst shot, a near copy, a photo you chose to remove
  ([cleaning, step 9](../clean/09-undo-history-purge.md#what-you-set-aside-stays-set-aside)),
  whether its quarantine is still there or purged;
- **already copied** into that folder by an earlier `mh import --phone`.

It ends with what it read back from the folder: *New photos and videos copied: 212 (1.40 GB,
18.5 MB/s)*, then each count left out, and *👉 What next: `mh audit`*. 🔒 Without `--free`, the
phone is only read: nothing on it is deleted, moved or renamed.

- **Run `mh audit` once first**: the library is what the cache knows. Without an audit, every
  photo of the phone is new (it says so).
- **The phone only gives a name and a size**, not its content. A different photo that happens to
  have the name and size of one of yours stays on the phone, not copied; a photo copied twice
  under another name is found by the next audit as an identical copy, which `clean` handles.
- **Unplugged in the middle?** The file being copied is removed, the import stops and says how
  many were copied. Type `mh import --phone` again: what is already copied is skipped.
- **Never a Windows question**: each file is copied into an empty folder
  (`.mh-phone-<date>`), then moved to its place; a name already taken gets `_1`, said on screen.
  That folder is removed at the end.
- The phone's folders below `DCIM` are kept (`Camera`, `Screenshots`). Other folders of the phone
  (WhatsApp) are not read. With `--to` outside your photo folders, `mh folders add` it for the
  audits to see it.
- Windows only: from WSL, Linux or macOS, Docker and bash cannot reach a phone over USB.

### Free the phone: `mh import --phone --free`

After the import, a page opens in your browser with what the PC may hold, **grouped by the
phone's folders** (`Camera`, `WhatsApp`, a folder you made…, in the order of their names; only
the phone's `DCIM` is listed). A badge on each tile says why the PC holds it, explained at the top
of the left column:

- **📚 Already in your library** and **📥 Copied by `mh import --phone`** (now or before): ticked for you;
- **⚠️ Set aside before, on purpose**: never ticked for you. While its quarantine is there, the
  tile shows the photo itself (its copy in the quarantine, only read) and says *Set aside on
  <date>, still recoverable with `mh undo <run>` until `mh purge`*; once purged, *Purged on
  <date>: it is nowhere else. Deleted from the phone, it is lost for good* (a purge older than
  this version gives no date: *purged since*).

A ticked file carries a red *🗑️ leaves the phone* label. To change what is ticked, the page works
as [`browse`](browse.md):

- **Pick**: a click picks one file; the ☑ box of each thumbnail (or Ctrl+click) adds or removes
  one; Shift+click picks every file from the last one clicked; a rectangle dragged with the mouse
  over the grid picks what it touches, over several rows (with Ctrl, it adds to the picking);
  Ctrl+A every file of the page. **Invert the picking** (or I) picks the others. Then, in the bar,
  **🗑️ Tick: leaves the phone** or **Untick: stays on the phone**. A file set aside before is
  never ticked with others: the bar says *1 file set aside before was left unticked*; tick it
  alone, after reading its warning.
- **A whole folder**: the box beside its name ticks every file of it (not those set aside
  before), or unticks them all; ▣ when only some are ticked. ▾ folds a long folder (kept for the
  next visit in this browser); the list of the folders, on the left, leads to each one.
- **Large view**: a double click or Enter, ← → the previous or next one, **Space ticks or
  unticks the file shown**, F full screen, Esc closes. It shows the PC's copy; *Open the
  original* opens it untouched.
- There is no Delete key here: the only deletion is the red button. The keys are listed at the
  bottom left (⌨ **Keyboard**, then *More keys*).

Every tick is saved at once in `phone-decisions.json` (in your reports folder), read back from the
disk and shown. **Nothing leaves the phone before you press *Delete N files from the phone***;
*Leave everything on the phone* ends it with nothing deleted. Opened from the home page (*Make
room on the phone*), the page has **⌂ Back to the home page** at the top right, as every page:
it ends the page in the same way, nothing deleted, and the home page comes back in the same tab;
after *Delete*, the tab says to switch to the PowerShell window and counts the minutes gone by
against the estimate (*2 min gone by, of about 4*), then shows the home page by itself once `mh`
brings it back, even when `mh.ps1` was written by an older image; typed in a console, it says that
the PowerShell window tells when it is done. If the page stopped meanwhile (ended in another tab,
the window of `mh` closed), a tick says so plainly — *The page is not running any more* — and the red
button is refused: nothing more is saved there. Then, for each file ticked:

1. it is **copied again** from the phone into an empty folder (`.mh-phone-<date>`);
2. its **content is proven** (SHA-256) equal to a file of your library that is still there, to
   the import's own copy, or to what you set aside before; **otherwise it stays on the phone**,
   with its reason (*Not the same content as `2025\07\IMG_0001.jpg`*). A name and a size are
   never enough;
3. only then is it **moved off the phone** into a PC folder (`.mh-moved-<date>`), the phone's
   folder listed again to see it gone, and that moved copy dropped once equal to the proven one
   (one that differs is kept there, said on screen).

It says the time first (each file is read twice from the phone, about 24 MB/s: *about 6 min for
4.2 GB*), and ends with what it saw gone: *Phone freed: 4,980 files deleted (21.3 GB)*, then the
files kept on the phone and why. Each deletion is written in the journal before and after it
happens (a run of kind `phone` in `mh history`).

- ⚠️ **Deleted over USB, a file is gone for good from the phone**: the phone's gallery has no
  trash for it, and `undo` cannot put a file back on a phone (it says so). Its content is on the
  PC: that is what was proven.
- **Unplugged in the middle?** It stops and says what was deleted; the rest is still on the
  phone. Type `mh import --phone --free` again: it starts over from a fresh listing.

## Options

| Option | What it does |
|---|---|
| `FOLDER` | The folder to import from (host path), instead of your backup folders: an SD card, a USB disk. Only read for this run, never added to `mh`. |
| `--to PATH` | Folder receiving the copies (host path); default: `From <source>` in your first photo folder. |
| `--yes`, `-y` | Copy without asking first. |
| `--backup PATH` | The backup folder to import from, when not in `config.toml` (`mh` passes yours). |
| `--phone` | A phone over USB instead of a folder, Windows only: the `mh` of PowerShell copies its new photos itself ([above](#from-a-phone-mh-import---phone)); with it, `--only <folder of DCIM>` and `--free`. |

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
