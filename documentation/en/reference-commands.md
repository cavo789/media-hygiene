# Commands and options

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-commands.md)

Every command, every option. The [user guide](README.md#start-here) introduces
them one at a time; this page gathers them.

## Commands

| Command | What it does | Guide |
|---|---|---|
| `audit` | Find exact duplicates and broken files. Never writes to your folders. | [1](start/01-first-audit.md) |
| `review` | Audit, then sort the burst series in your browser, one at a time, with the keyboard. Never writes to your folders. | [10](clean/10-review-bursts.md) |
| `clean` | Audit, confirm, then delete duplicate copies, delete empty files, quarantine unreadable ones and orphan sidecars. | [8](clean/08-clean.md) |
| `undo [RUN]` | Restore every file of a run (the latest by default). | [9](clean/09-undo-history-purge.md) |
| `history` | List the runs: their command, files deleted, space freed, quarantine, restores. | [9](clean/09-undo-history-purge.md) |
| `purge [RUN]` | Permanently delete the quarantine of a run (of every run by default). | [9](clean/09-undo-history-purge.md) |
| `reports [--prune N]` | List the reports and refresh `index.html`; `--prune N` keeps the N most recent. | [4](clean/04-html-report.md) |
| `crosscheck` | Audit again, then compare with the results of Czkawka, an independent duplicate finder. | [13](clean/13-second-opinion.md) |
| `classify` | Propose where every photo and video should go: year, event, category. Never writes to your folders; writes a workbook to edit and a report to `/reports`. | [4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md) |
| `sort [WORKBOOK]` | Check the edited workbook of `classify`, confirm, then move the files where it says; journaled, undoable, proven. | [7](sort/07-sort.md) |
| `config` | Show every setting, where it comes from, and the state of each mount point. | [7](clean/07-configuration-file.md) |

## Options

Global options go **before** the command: `cavo789/media-hygiene --locale fr audit`. The others go
**after** it: `cavo789/media-hygiene audit --prefer "C:\Photos\Family"`.

| Option | Commands | Meaning |
|---|---|---|
| `--locale en\|fr` | global | Interface language (English by default); numbers and sizes follow it: `67,947` and `44.3 GB`, or `67.947` and `44,3 Go`. |
| `--verbosity error\|warning\|info\|debug` | global | How much to log. |
| `--color auto\|always\|never` | global | ANSI colours (`NO_COLOR` is honoured). |
| `--version` | global | Show the version. |
| `--prefer PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder whose copies are kept first; repeatable, ordered. [Step 5](clean/05-choose-the-kept-copy.md#prefer-a-folder) |
| `--protect PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder never modified; its files are the copies kept. [Step 5](clean/05-choose-the-kept-copy.md#protect-a-folder) |
| `--exclude PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder never analysed. [Step 5](clean/05-choose-the-kept-copy.md#exclude-a-folder) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | Only analyse these categories or extensions (`--ext photo,video`, `--ext png,webp`); built-in categories `photo`, `raw`, `video`, `media`, plus those of `[scan.categories]`; `media` (every photo, RAW and video) by default. Other types too (`--ext pdf,docx`). [Step 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge` | Do not ask for confirmation (`undo` asks only before undoing several runs of one sort). |
| `--tier exact\|near` | `clean` | `exact` (default): byte-for-byte copies only. `near`: also move near duplicates to the quarantine. [Step 11](clean/11-near-duplicates.md) |
| `--decisions FILE` | `clean`, `review` | `clean`: apply the folder-pair decisions of a report and the burst shots set aside with `review`. `review`: the file the choices are saved in, `decisions.json` by default. A relative path is read from `/reports`. [Step 10](clean/10-review-bursts.md), [step 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review` | Port of the page inside the container, `8080` by default; publish it with `-p 127.0.0.1::8080`. |
| `--prune N` | `reports` | Keep the N most recent reports, delete the others. |
| `--year YEAR[-YEAR]` | `classify` | Only the files of this year or these years. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--layout LAYOUT` | `classify` | Where sure files go, e.g. `{year}/{month}`. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--target PATH` | `classify` | Folder receiving the tree; each mounted folder, in place, by default. |
| `--leave PATH` | `classify` | Folder never sorted; still analysed and cleaned. |
| `--carry-over PATH` | `classify` | Workbook whose edits are carried over; the latest `classify` run's by default. [Sorting, step 5](sort/05-review-the-proposal.md#improve-the-proposal-without-losing-your-work) |
| `--no-carry-over` | `classify` | Start fresh: carry no edit of a previous workbook over. |
| `--keep-empty-folders` | `sort` | Keep the source folders the sort leaves empty. [Sorting, step 7](sort/07-sort.md#folders-left-empty) |

Most options have a `config.toml` counterpart ([step 7](clean/07-configuration-file.md)); the command
line wins. The rules of `classify` (`[[classify.rules]]`) have no option: they are written in
`config.toml` only ([sorting, step 6](sort/06-write-down-what-you-know.md)).

## The built-in help

`cavo789/media-hygiene --help` and `cavo789/media-hygiene <command> --help` document everything, in
both languages (`--locale fr --help`). Here is what they print:

<details>
<summary><code>--help</code></summary>

<!-- capture: help.txt -->
```text
 Usage: media-hygiene [OPTIONS] COMMAND [ARGS]...

 Find and safely clean duplicate photos and videos across folders and disks.
 Start with 'audit' (read-only), then 'clean'.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --version            Show the version and exit.                              │
│ --help     -h        Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Output (override general.* of config.toml) ─────────────────────────────────╮
│ --locale           <en|fr>                     Interface language.           │
│ --verbosity        <error|warning|info|debug>  How much to log.              │
│ --color            <auto|always|never>         When to use colours (NO_COLOR │
│                                                is honoured too).             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Analyse ────────────────────────────────────────────────────────────────────╮
│ audit       Find exact duplicates and broken files. Read-only: mount folders │
│             with :ro.                                                        │
│ crosscheck  Compare a fresh audit with Czkawka's results: a second,          │
│             independent opinion.                                             │
│ classify    Propose where every photo and video should go: year, event,      │
│             category. Read-only.                                             │
│ history     List the runs and what they did.                                 │
│ reports     List the HTML reports of previous audits and cleans.             │
│ config      Show every setting, where it comes from, and the mount points.   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Act ────────────────────────────────────────────────────────────────────────╮
│ review      Set burst shots aside, one series at a time, with the keyboard   │
│             in your browser; 'clean --decisions' then moves them.            │
│ clean       Audit, confirm, then really delete duplicate copies (journaled,  │
│             undoable).                                                       │
│ sort        Move the photos and videos as the edited classify workbook says  │
│             (journaled, undoable).                                           │
│ undo        Restore every file of a run, from the kept copy, the quarantine  │
│             or where it was moved.                                           │
│ purge       Permanently delete the quarantined broken files of a run.        │
╰──────────────────────────────────────────────────────────────────────────────╯


 A Windows folder (PowerShell):
   docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" media-hygiene audit
 The current folder (PowerShell, or bash on WSL, Linux, macOS):
   docker run --rm -it -v "${PWD}:/data/current:ro" media-hygiene audit

 Full commands (reports, journal, WSL): see README.md.
```

</details>

<details>
<summary><code>audit --help</code></summary>

<!-- capture: help-audit.txt -->
```text
 Usage: media-hygiene audit [OPTIONS]

 Find exact duplicates and broken files. Read-only: mount folders with :ro.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Folders (override folders.* of config.toml) ────────────────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, e.g. a real backup to keep.   │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Scan (override scan.* of config.toml) ──────────────────────────────────────╮
│ --ext        <str>  Only analyse these categories or extensions, e.g. --ext  │
│                     photo,video or --ext png,webp (repeatable). Categories:  │
│                     photo, raw, video, media and those of scan.categories in │
│                     config.toml. Other types too, such as --ext pdf,docx:    │
│                     their copies are moved to the quarantine. Default: media │
│                     (every photo, RAW and video).                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>review --help</code></summary>

<!-- capture: help-review.txt -->
```text
 Usage: media-hygiene review [OPTIONS]

 Set burst shots aside, one series at a time, with the keyboard in your
 browser; 'clean --decisions' then moves them.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --decisions          <path>              File the decisions are saved in,    │
│                                          and resumed from. A relative path   │
│                                          lies in the folder mounted on       │
│                                          /reports. Default: decisions.json.  │
│ --port               <int range> [x>=0]  Port of the page inside the         │
│                                          container; publish it with -p       │
│                                          127.0.0.1::8080 so that Docker      │
│                                          chooses a free one on your          │
│                                          computer. Default: 8080.            │
│ --help       -h                          Show this message and exit.         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Folders (override folders.* of config.toml) ────────────────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, e.g. a real backup to keep.   │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>clean --help</code></summary>

<!-- capture: help-clean.txt -->
```text
 Usage: media-hygiene clean [OPTIONS]

 Audit, confirm, then really delete duplicate copies (journaled, undoable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes        -y                    Do not ask for confirmation (overrides    │
│                                    clean.confirm).                           │
│ --tier               <exact|near>  exact: delete byte-for-byte copies only.  │
│                                    near: also move near duplicates (resized  │
│                                    or recompressed copies) to the            │
│                                    quarantine; check them in the report      │
│                                    first. Default: exact.                    │
│ --decisions          <path>        decisions.json downloaded from an audit   │
│                                    report (swap or leave alone some folder   │
│                                    pairs) or written by 'review' (burst      │
│                                    shots set aside). A relative path is read │
│                                    from the folder mounted on /reports. The  │
│                                    file is refused if the folders, the pairs │
│                                    or the series changed.                    │
│ --help       -h                    Show this message and exit.               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Folders (override folders.* of config.toml) ────────────────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, e.g. a real backup to keep.   │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Scan (override scan.* of config.toml) ──────────────────────────────────────╮
│ --ext        <str>  Only analyse these categories or extensions, e.g. --ext  │
│                     photo,video or --ext png,webp (repeatable). Categories:  │
│                     photo, raw, video, media and those of scan.categories in │
│                     config.toml. Other types too, such as --ext pdf,docx:    │
│                     their copies are moved to the quarantine. Default: media │
│                     (every photo, RAW and video).                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Usage: media-hygiene undo [OPTIONS] [run_id]

 Restore every file of a run, from the kept copy, the quarantine or where it
 was moved.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Run to undo (see 'history'); the latest one by default. │
│                      For a sort, every run of the same workbook.             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Do not ask for confirmation before undoing several runs of │
│                   a sort (overrides sort.confirm).                           │
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>history --help</code></summary>

<!-- capture: help-history.txt -->
```text
 Usage: media-hygiene history [OPTIONS]

 List the runs and what they did.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>purge --help</code></summary>

<!-- capture: help-purge.txt -->
```text
 Usage: media-hygiene purge [OPTIONS] [run_id]

 Permanently delete the quarantined broken files of a run.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Run whose quarantine is deleted; every run by default.  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Do not ask for confirmation (overrides clean.confirm).     │
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>reports --help</code></summary>

<!-- capture: help-reports.txt -->
```text
 Usage: media-hygiene reports [OPTIONS]

 List the HTML reports of previous audits and cleans.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --prune          <int range> [x>=0]  Delete all reports but the N most       │
│                                      recent ones.                            │
│ --help   -h                          Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Usage: media-hygiene crosscheck [OPTIONS]

 Compare a fresh audit with Czkawka's results: a second, independent opinion.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Folders (override folders.* of config.toml) ────────────────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, e.g. a real backup to keep.   │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Scan (override scan.* of config.toml) ──────────────────────────────────────╮
│ --ext        <str>  Only analyse these categories or extensions, e.g. --ext  │
│                     photo,video or --ext png,webp (repeatable). Categories:  │
│                     photo, raw, video, media and those of scan.categories in │
│                     config.toml. Other types too, such as --ext pdf,docx:    │
│                     their copies are moved to the quarantine. Default: media │
│                     (every photo, RAW and video).                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>classify --help</code></summary>

<!-- capture: help-classify.txt -->
```text
 Usage: media-hygiene classify [OPTIONS]

 Propose where every photo and video should go: year, event, category.
 Read-only.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year                   <str>  Only the files of this year, or of these     │
│                                 years: 2016 or 2015-2017.                    │
│ --layout                 <str>  Where sure files go, e.g. '{year}/{month} -  │
│                                 {month_name}'.                               │
│ --target                 <str>  Host folder receiving the tree; in place by  │
│                                 default.                                     │
│ --leave                  <str>  Host folder never sorted (analysed and       │
│                                 cleaned as usual).                           │
│ --carry-over             <str>  Workbook whose edits are carried over; the   │
│                                 latest classify run's by default.            │
│ --no-carry-over                 Start fresh: carry no edit of a previous     │
│                                 workbook over.                               │
│ --help           -h             Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>sort --help</code></summary>

<!-- capture: help-sort.txt -->
```text
 Usage: media-hygiene sort [OPTIONS] [workbook]

 Move the photos and videos as the edited classify workbook says (journaled,
 undoable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  The classify workbook, edited; the latest classify    │
│                        run's by default.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes                 -y        Do not ask for confirmation (overrides       │
│                                 sort.confirm).                               │
│ --keep-empty-folders            Keep the source folders the sort leaves      │
│                                 empty.                                       │
│ --help                -h        Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Usage: media-hygiene config [OPTIONS]

 Show every setting, where it comes from, and the mount points.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
