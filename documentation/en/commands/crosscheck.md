# `crosscheck`: a second, independent opinion

[Documentation](../README.md) › [Commands](../reference-commands.md) › `crosscheck` · 🇫🇷 [Français](../../fr/commands/crosscheck.md)

## In short

**Be sure of your duplicates before deleting family photos: a second, independent tool checks
them, group by group.**

`crosscheck` audits again, runs [Czkawka](https://github.com/qarmin/czkawka), an open-source
duplicate finder written independently, with another hash function, then compares both, group by
group. Czkawka ships in the image: one command does it all. When both agree, you can clean with
confidence.

**When**: optional, before a first large `clean` (`clean` never requires it), and again after
cleaning if you like: with `/cache`, Czkawka only reads what changed.

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene crosscheck
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders, and `/reports`, where Czkawka's results (`czkawka.json`) are kept. |
| Recommended | `/cache`: the audit takes seconds, and Czkawka keeps its own cache there. `/config`. |
| Writes | The cache, `czkawka.json` and a crosscheck report in `/reports`. |
| Undo | Nothing to undo. |
| With `mh` | `mh crosscheck`. |

## Run it

With the same folders and options as your audit:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene crosscheck
```

1. **The audit**, quickly thanks to the cache.
2. **Czkawka** reads the same folders, the same extensions, without the excluded folders, every
   file size. It only reads: nothing is changed. On tens of thousands of photos, allow a few
   minutes the first time; with `/cache`, the next runs only read what changed. It writes
   `czkawka.json` in your reports folder.
3. **The comparison**, group by group, and its report.

## Read the verdict

- *Czkawka agrees: the same N extra copies in G groups*: both tools found exactly the same
  duplicates.
- *Czkawka disagrees on N groups*, followed by each group found by one tool only: look at them
  before cleaning.

The verdict shows at the top of the crosscheck report, in every later `clean` before its
question, and in the clean report.

## Options

The same folder and scan options as [`audit`](audit.md#options): `--prefer`, `--protect`,
`--exclude`, `--exclude-name`, `--ext`. Give the ones of your audit.

| Option | What it does |
|---|---|
| `--fresh` | Czkawka reads and hashes every file again, ignoring its cache: a second opinion that owes nothing to an earlier one. Slower. |
| `--print-command` | Czkawka is not run here: `crosscheck` prints the command that runs it in its own image (the community image `jlesage/czkawka`, about 500 MB), then compares the `czkawka.json` it wrote. For those who want to run Czkawka with their own eyes. |

## Good to know

- Files media-hygiene deliberately leaves out (other file types, excluded or system folders,
  broken files) are counted apart, not reported as differences; the folders never analysed are
  named, the largest first.
- **Photos moved or deleted since Czkawka ran** (by a `clean`, say) make its results out of date
  for the later `audit` and `clean`: they are ignored, and the message gives the way out: run
  `crosscheck` again, or delete `czkawka.json` if you no longer want a second opinion.
- Czkawka is the unmodified release binary of its project (MIT licence), pinned in the image.
  Only the packaging is shared: its code and its hash function stay its own.

## Go further

- [13. A second opinion](../clean/13-second-opinion.md)
- [How your photos stay safe: what counts as a duplicate](../reference-safety.md#what-counts-as-a-duplicate)

## The built-in help

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Usage: media-hygiene crosscheck [OPTIONS]

 🔒 Read-only: never changes your photos. Run Czkawka, an independent duplicate
 finder, then compare its groups with a fresh audit: a second opinion.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, not even read. Repeatable.    │
│ --backup         <str>  A backup or an old disk: compared, never changed.    │
│                         Says what it lacks and what only it holds.           │
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
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --fresh                  Czkawka reads and hashes every file again, ignoring │
│                          what its cache in /cache remembers from its         │
│                          previous run. Slower; for a second opinion that     │
│                          owes nothing to an earlier one.                     │
│ --print-command          Do not run Czkawka here: print the command that     │
│                          runs it in its own image, then compare the results  │
│                          it wrote in /reports (czkawka.json).                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
