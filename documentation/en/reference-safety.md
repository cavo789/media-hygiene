# How your photos stay safe

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-safety.md)

Before touching family photos, everyone asks the same question: *can I lose one?* This page
answers it plainly: which commands never touch your photos, which ones act and how they stay
reversible, and the only command that erases anything.

## Our promise: these commands never change your photos

We guarantee it: when you run one of these commands, your photos and videos are **never
modified, moved nor deleted**.

| Command | What it writes, and where |
|---|---|
| `audit`, `crosscheck` | The HTML report (`/reports`) and the cache (`/cache`). |
| `classify` | The proposal and its workbook (`/reports`), the cache. |
| `review`, `review-sort` | Your choices, in a small `.json` file next to the report (`/reports`). |
| `places` | The places you name, in `config.toml` (`/config`). |
| `inventory` | The workbook (`/reports`), read from the cache alone. |
| `history`, `reports`, `config` | Nothing in your folders (`reports --prune` deletes old reports only). |

All of them work with your photo folders mounted **read-only**: add `:ro` to their `-v`
(`-v "C:\Photos:/data/c/Photos:ro"`). Then it is not only our promise: the operating system
itself refuses any change. Their `--help` starts with *Read-only*, and those reading your photos say so
with 🔒 when they start.

## Nothing is erased unless you run `purge`

The commands that act on your files never erase anything, and every one of them can be undone:

- **`sort`** moves the files where the workbook says. On one disk, a move is a simple rename:
  nothing is copied, no space is used.
- **`album`** only adds second names (hard links); no photo is copied, moved nor deleted.
- **`clean`** moves the extra copies to the quarantine, each one compared byte for byte with
  the copy kept just before. Their space is freed by `purge`, once you have checked.
- **`undo`** puts the files of a run back where they were.

**`purge` is the only command that erases**: it empties the quarantine, for good, after
telling you how many files and how much space, and asking you. Until then, `undo` brings
everything back.

Need the space at once? `clean --delete` deletes the extra copies instead of moving them, after
the same byte comparison. The copy kept stays, so nothing is lost: `undo` rebuilds each deleted
copy from it. Empty files (0 bytes) are deleted too: they hold nothing.

## The safety nets, always on, at no cost in space

- **Read-only commands**, and `:ro`, enforced by the operating system.
- **Never over another file.** A move, a copy or an undo never replaces a file: if a file
  appeared at the destination meanwhile, the action is refused, and both files stay as they are.
- **Checked twice.** A copy is compared with the copy kept right before it is set aside; a move
  across disks is copied, proven identical (SHA-256), and only then removed from where it was.
- **The journal.** Every action is written down *before* and *after* it happens: an
  interruption never loses track, and `undo` reverses any run.
- **The quarantine.** What `clean` sets aside waits there, whole, until you `purge` it.
- **The tool's folders stay out of your photos.** A quarantine, journal, cache or reports
  folder placed inside a photo folder (or around one) is refused, with how to mount it instead.

## Good habits

- **Start small.** Audit one subfolder, look at the report, then widen.
- **Read the report before `clean`**: the folder pairs first, then a few groups.
- **Pause cloud synchronisation** (OneDrive, Google Drive, Dropbox, iCloud) while cleaning or
  sorting: otherwise every change is copied to the cloud and to your other devices.
- **Keep the journal folder**: `undo` needs it. Run `purge` only once you have checked.

If you can, a **backup on an external disk** is the extra net against what no software can
prevent: a failing disk, a mistake made outside the tool. It is welcome, not required.

## What counts as a duplicate

Only **byte-for-byte identical** files. The tool first compares sizes, then a SHA-256
fingerprint of the first and last 64 KB, then a SHA-256 fingerprint of the whole content. In
practice, two different files never share a SHA-256: the odds are far lower than those of a disk
error.

- **The name and the date do not matter.** `IMG_1234.jpg` and `Marie et Paul.jpg` with the same
  bytes are duplicates. Two `IMG_0001.jpg` with different content are not.
- **Looking the same is not enough.** A resized, recompressed, rotated or re-tagged copy is a
  different file. The audit lists it as a [near duplicate](clean/11-near-duplicates.md), but `clean`
  leaves it alone unless you ask with `--tier near`, and then only moves it to the quarantine.
- **Only photos, RAW files and videos** are analysed, recognised by their extension. Other files
  only when you [ask for them](clean/06-file-types.md#other-file-types) with `--ext`, and then their
  copies are moved to the quarantine, never deleted.

## Every guarantee, step by step

| Step | Guarantee |
|---|---|
| `audit` and the other [read-only commands](#our-promise-these-commands-never-change-your-photos) | Mount your folders with `:ro` and the system itself forbids any write. |
| Which copy is kept | Deterministic: the [keep rules](clean/05-choose-the-kept-copy.md#how-the-tool-chooses) always give the same choice, and the report says which rule decided. Your [decisions in the report](clean/12-decide-pair-by-pair.md) come on top. |
| One file, two paths | A folder mounted twice is refused; a file reachable through two paths (hard link) is analysed once, never a duplicate of itself. |
| Before each copy is set aside | The kept copy must still exist, be another file (not the same file seen through two paths), and still be byte-for-byte identical; otherwise the copy is skipped. |
| Each action | Written to the journal *before* (`pending`) and *after* (`done`) it happens: an interruption never loses track. |
| Duplicates | Moved to the quarantine; `undo` puts them back, `purge` frees their space. With `clean --delete`, deleted at once; `undo` rebuilds them from the kept copy, date included, even across disks. |
| Unreadable files | Moved to the quarantine, never deleted outright; `purge` deletes them for good when you are sure. |
| Moves | Never over another file: an atomic rename that refuses an existing name, or, across disks, a copy into a new file, proven identical, before the original goes. |
| Near duplicates | Photos and [re-encoded videos](clean/11-near-duplicates.md#videos-too-re-encoded-copies). Never touched by default. With `--tier near`, moved to the quarantine (never deleted) once checked: the kept photo or video still exists, the copy is the very file the audit saw. `undo` puts them back. |
| Burst series | Never touched by default. The shots you [set aside with `review`](clean/10-review-bursts.md) are moved to the quarantine (never deleted) by `clean --decisions`, once checked: a shot you kept is still there, the shot set aside is the very file the review showed. `undo` puts them back. |
| Other file types | Only when asked for with `--ext`: their copies are moved to the quarantine (never deleted), and software folders (`.git`, `node_modules`, `AppData`, …) are skipped. |
| Sidecars | Never touched next to their photo. An orphan is moved to the quarantine (never deleted) once checked: unchanged since the audit, and no file of the same name next to it. `undo` puts it back. |
| Albums | [`album`](sort/11-albums.md) only adds hard links (second names) in its own folder, journaled, never over a file; every scan skips that folder. `undo` removes an album's name only when the original it names is still there and is the very same file; otherwise the name stays, and `undo` says why. |
| `sort` junk files | Only the names of `[sort] junk_files` (`Thumbs.db`, …) go to the quarantine with an emptied folder; a photo, video or sidecar name there is refused. |
| Protected folders | Never modified, whatever happens. |
| Every group | Always keeps at least one copy. |

## Check it yourself

The [HTML report](clean/04-html-report.md) is built for that:

- The **folder pairs** come first. A badge marks a folder that is *entirely a copy* of another
  one, and each pair has a page listing every copy.
- A **random sample** of photo groups comes with previews.
- **Check it yourself**, on every group, gives a PowerShell `Get-FileHash` command. Paste it:
  every copy shows the same SHA-256, computed by Windows, not by media-hygiene.
- **`plan.csv`** lists every file of the plan with its SHA-256, ready for Excel.
- **[A second opinion](clean/13-second-opinion.md)**: Czkawka, an independent tool, compares its
  results with media-hygiene's, group by group.

## Recommendations

- **Check which copy stays.** The kept file keeps its name and folder; the name of a copy set
  aside is lost once purged. Not the one you want?
  [Choose it](clean/05-choose-the-kept-copy.md), then audit again.
- Read the [troubleshooting page](reference-troubleshooting.md) too: a real backup must be
  excluded, and each folder must be mounted only once.
