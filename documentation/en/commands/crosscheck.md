# `crosscheck`: a second, independent opinion

[Documentation](../README.md) › [Commands](../reference-commands.md) › `crosscheck` · 🇫🇷 [Français](../../fr/commands/crosscheck.md)

Before deleting family photos, a second opinion is reassuring. `crosscheck` audits again, then
compares its duplicates, group by group, with those found by
[Czkawka](https://github.com/qarmin/czkawka), an open-source duplicate finder written
independently, with another hash function. When both agree, you can clean with confidence.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders, and `/reports`, where Czkawka wrote `czkawka.json`. |
| Recommended | `/cache` (the audit takes seconds), `/config`. |
| Writes | The cache, a crosscheck report in `/reports`. |
| Undo | Nothing to undo. |
| With `mh` | `mh crosscheck`. |

## When to use it

Optional, once, before a first large `clean`: `clean` never requires it.

## Run it, in three steps

1. **The Czkawka command.** As long as Czkawka has not run, `crosscheck` (and an audit run with
   `--verbosity verbose`) prints the exact command for your folders: the same `-v` options,
   extensions and excluded folders. It uses the community image `jlesage/czkawka` (about 500 MB).
2. **Run Czkawka.** Paste that command, with your reports folder where it says so. On tens of
   thousands of photos, allow several minutes. It writes `czkawka.json` in your reports folder.
3. **Compare**, with the same options as your audit:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene crosscheck
```

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

## Good to know

- Files media-hygiene deliberately leaves out (other file types, excluded or system folders,
  broken files) are counted apart, not reported as differences; the folders never analysed are
  named, the largest first.
- **Photos moved or deleted since Czkawka ran** (by a `clean`, say) make its results out of date:
  they are ignored, and the message gives the way out: run Czkawka again, or delete
  `czkawka.json` if you no longer want a second opinion.

## Go further

- [13. A second opinion](../clean/13-second-opinion.md)
- [How your photos stay safe: what counts as a duplicate](../reference-safety.md#what-counts-as-a-duplicate)

## The built-in help

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Usage: media-hygiene crosscheck [OPTIONS]

 🔒 Read-only: never changes your photos. Compare a fresh audit with Czkawka's
 results: a second, independent opinion.

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
