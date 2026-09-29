# How your photos stay safe

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-safety.md)

Before deleting family photos, everyone asks the same question: *are these really, really
duplicates?* This page explains what the tool calls a duplicate, what it checks before each
action, and how you can check it yourself.

## What counts as a duplicate

Only **byte-for-byte identical** files. The tool first compares sizes, then a SHA-256
fingerprint of the first and last 64 KB, then a SHA-256 fingerprint of the whole content. In
practice, two different files never share a SHA-256: the odds are far lower than those of a disk
error.

- **The name and the date do not matter.** `IMG_1234.jpg` and `Marie et Paul.jpg` with the same
  bytes are duplicates. Two `IMG_0001.jpg` with different content are not.
- **Looking the same is not enough.** A resized, recompressed, rotated or re-tagged copy is a
  different file. The audit lists it as a [near duplicate](11-near-duplicates.md), but `clean`
  leaves it alone unless you ask with `--tier near`, and then only moves it to the quarantine.
- **Only photos, RAW files and videos** are analysed, recognised by their extension. Other files
  only when you [ask for them](06-file-types.md#other-file-types) with `--ext`, and then their
  copies are moved to the quarantine, never deleted.

## Every guarantee, step by step

| Step | Guarantee |
|---|---|
| `audit` | Read-only: mount your folders with `:ro` and Docker itself forbids any write. |
| Which copy is kept | Deterministic: the [keep rules](05-choose-the-kept-copy.md#how-the-tool-chooses) always give the same choice, and the report says which rule decided. Your [decisions in the report](12-decide-pair-by-pair.md) come on top. |
| One file, two paths | A folder mounted twice is refused; a file reachable through two paths (hard link) is analysed once, never a duplicate of itself. |
| Before each deletion | The kept copy must still exist, be another file, and still be byte-for-byte identical; otherwise the file is skipped. |
| Each action | Written to the journal *before* (`pending`) and *after* (`done`) it happens: an interruption never loses track. |
| Duplicates | Really deleted (the space is freed immediately); `undo` rebuilds them from the kept copy, date included, even across disks. |
| Unreadable files | Moved to the quarantine, never deleted outright; `purge` deletes them for good when you are sure. |
| Near duplicates | Never touched by default. With `--tier near`, moved to the quarantine (never deleted) once checked: the kept photo still exists, the copy is the very file the audit saw. `undo` puts them back. |
| Burst series | Never touched by default. The shots you [set aside with `review`](10-review-bursts.md) are moved to the quarantine (never deleted) by `clean --decisions`, once checked: a shot you kept is still there, the shot set aside is the very file the review showed. `undo` puts them back. |
| Other file types | Only when asked for with `--ext`: their copies are moved to the quarantine (never deleted), and software folders (`.git`, `node_modules`, `AppData`, …) are skipped. |
| Sidecars | Never touched next to their photo. An orphan is moved to the quarantine (never deleted) once checked: unchanged since the audit, and no file of the same name next to it. `undo` puts it back. |
| Protected folders | Never modified, whatever happens. |
| Every group | Always keeps at least one copy. |

## Check it yourself

The [HTML report](04-html-report.md) is built for that:

- The **folder pairs** come first. A badge marks a folder that is *entirely a copy* of another
  one, and each pair has a page listing every copy.
- A **random sample** of photo groups comes with previews.
- **Check it yourself**, on every group, gives a PowerShell `Get-FileHash` command. Paste it:
  every copy shows the same SHA-256, computed by Windows, not by media-hygiene.
- **`plan.csv`** lists every file of the plan with its SHA-256, ready for Excel.
- **[A second opinion](13-second-opinion.md)**: Czkawka, an independent tool, compares its
  results with media-hygiene's, group by group.

## Recommendations

- **Audit first, then read the folder pairs.** Open a few pairs, and check a few groups yourself.
- **Check which copy stays.** The kept file keeps its name and folder; the name of a deleted copy
  is lost. Not the one you want? [Choose it](05-choose-the-kept-copy.md), then audit again.
- **Back up your photos before the first clean**, for example on an external disk: the tool keeps
  one copy of each photo, not two.
- **Pause cloud synchronisation** (OneDrive, Google Drive, Dropbox, iCloud) while cleaning.
  Otherwise deletions are copied to the cloud and to your other devices.
- **Keep the journal folder**: `undo` needs it. Run `purge` only when you are sure.
- Read the [troubleshooting page](reference-troubleshooting.md) too: a real backup must be
  excluded, and each folder must be mounted only once.
