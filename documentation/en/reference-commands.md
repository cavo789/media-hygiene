# Commands and options

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-commands.md)

Every command, every option. The [user guide](README.md#start-here) introduces
them one at a time; this page gathers them. The commands whose help starts with *Read-only* never change your photos
([how your photos stay safe](reference-safety.md)).

## Commands

| Command | What it does | Guide |
|---|---|---|
| `audit` | Find exact duplicates and broken files. Never writes to your folders. | [1](start/01-first-audit.md) |
| `review` | Audit, then sort the burst series in your browser, one at a time, with the keyboard. Never writes to your folders. | [10](clean/10-review-bursts.md) |
| `clean` | Audit, confirm, then move duplicate copies, unreadable files and orphan sidecars to the quarantine, and delete empty files; `--delete` deletes the copies instead. | [8](clean/08-clean.md) |
| `undo [RUN]` | Restore every file of a run (the latest by default); for an album, remove its links. | [9](clean/09-undo-history-purge.md) |
| `history` | List the runs: their command, files deleted, space freed, quarantine, restores. | [9](clean/09-undo-history-purge.md) |
| `purge [RUN]` | Erase the quarantine of a run for good (of every run by default): the only command that erases content, with `clean --delete`. | [9](clean/09-undo-history-purge.md) |
| `reports [--prune N]` | List the reports and refresh `index.html`; `--prune N` keeps the N most recent. | [4](clean/04-html-report.md) |
| `crosscheck` | Audit again, then compare with the results of Czkawka, an independent duplicate finder. | [13](clean/13-second-opinion.md) |
| `classify` | Propose where every photo and video should go: year, event, category. Never writes to your folders; writes a workbook to edit and a report to `/reports`. | [4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md), [8](sort/08-subjects-from-a-local-model.md) |
| `sort [WORKBOOK]` | Check the edited workbook of `classify`, confirm, then move the files where it says; journaled, undoable, proven. | [7](sort/07-sort.md) |
| `album NAME` | Gather a selection of the `classify` plan (a category, an event, a rule, the stars) into a folder of hard links: nothing copied nor moved, no space used. Shows the selection; `--apply` makes the links, journaled and undoable. | [Sorting, step 11](sort/11-albums.md) |
| `inventory [--format xlsx\|csv]` | Export every photo and video with what the audits learnt to an Excel workbook (or a CSV file), from the cache alone: no file is read. | [Reference](reference-inventory.md) |
| `config` | Show every setting, where it comes from, and the state of each mount point. | [7](clean/07-configuration-file.md) |
| `review-sort [WORKBOOK]` | Show the events of the `classify` proposal one at a time in your browser, with their photos, and name them with the keyboard; saved next to `plan.json`, applied by `sort`. Never writes to your folders nor to the workbook. | [Sorting, step 10](sort/10-name-events-in-the-browser.md) |
| `places` | Show where the photos were taken on a map in your browser, and name your places; saved into `config.toml`. Never writes to your folders. | [Sorting, step 9](sort/09-places-from-gps.md) |

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
| `--exclude-name NAME` | `audit`, `clean`, `crosscheck` | Folder name never analysed, wherever it is (case ignored, `*` and `?` allowed: `--exclude-name Thumbnails,.Trash-*`); adds to the system and trash folders always skipped. [Step 5](clean/05-choose-the-kept-copy.md#skip-a-folder-name-on-every-disk) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | Only analyse these categories or extensions (`--ext photo,video`, `--ext png,webp`); built-in categories `photo`, `raw`, `video`, `media`, plus those of `[scan.categories]`; `media` (every photo, RAW and video) by default. Other types too (`--ext pdf,docx`). [Step 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge`, `classify` | Do not ask for confirmation (`undo` asks only before undoing several runs of one sort; `classify`, before describing many photos with a local model). |
| `--tier exact\|near` | `clean` | `exact` (default): byte-for-byte copies only. `near`: also move near duplicates to the quarantine. [Step 11](clean/11-near-duplicates.md) |
| `--delete` | `clean` | Delete the exact copies for good, after a byte comparison, instead of moving them to the quarantine; `undo` rebuilds them from the kept copy. [Step 8](clean/08-clean.md#need-the-space-at-once---delete) |
| `--decisions FILE` | `clean`, `review` | `clean`: apply the folder-pair decisions of a report and the burst shots set aside with `review`. `review`: the file the choices are saved in, `decisions.json` by default. A relative path is read from `/reports`. [Step 10](clean/10-review-bursts.md), [step 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review`, `review-sort`, `places` | Port of the page inside the container, `8080` by default; publish it with `-p 127.0.0.1::8080`. |
| `--prune N` | `reports` | Keep the N most recent reports, delete the others. |
| `--year YEAR[-YEAR]` | `classify` | Only the files of this year or these years. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--layout LAYOUT` | `classify` | Where sure files go, e.g. `{year}/{month}`. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--target PATH` | `classify` | Folder receiving the tree; each mounted folder, in place, by default. |
| `--leave PATH` | `classify` | Folder never sorted; still analysed and cleaned. |
| `--carry-over PATH` | `classify` | Workbook whose edits are carried over; the latest `classify` run's by default. [Sorting, step 5](sort/05-review-the-proposal.md#improve-the-proposal-without-losing-your-work) |
| `--no-carry-over` | `classify` | Start fresh: carry no edit of a previous workbook over. |
| `--sample N` | `classify` | Describe N random photos with the local model, print the time per photo and the estimate of a full run, and stop. [Sorting, step 8](sort/08-subjects-from-a-local-model.md#measure-first---sample) |
| `--no-describe` | `classify` | Ask the local model nothing new: the `subject` rules read the descriptions already in the cache. [Sorting, step 8](sort/08-subjects-from-a-local-model.md#the-long-run-never-in-the-way) |
| `--format xlsx\|csv` | `inventory` | `xlsx` (default): a workbook with the Files and Summary sheets. `csv`: the Files sheet only, like `plan.csv`. [Inventory](reference-inventory.md#a-csv-file-instead) |
| `--keep-empty-folders` | `sort` | Keep the source folders the sort leaves empty. [Sorting, step 7](sort/07-sort.md#folders-left-empty) |
| `--category NAME` | `album` | The files of this category, as the edited workbook says (an event named in the workbook gives its name). [Sorting, step 11](sort/11-albums.md#choose-what-the-album-gathers) |
| `--event EVENT` | `album` | The files of this event: its id (Events sheet) or its name. |
| `--rule NAME` | `album` | The files the `[[classify.rules]]` entry of this name decided. |
| `--rating N` | `album` | The files given at least N stars (1 to 5) in Windows, as the audit read them (needs `/cache`). |
| `--workbook PATH` | `album` | The `classify` workbook to read; the latest `classify` run's by default. |
| `--apply` | `album` | Make the links; without it, `album` only shows what it would gather. |

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
│ audit        Read-only: never changes your photos. Find exact duplicates and │
│              broken files.                                                   │
│ crosscheck   Read-only: never changes your photos. Compare a fresh audit     │
│              with Czkawka's results: a second, independent opinion.          │
│ classify     Read-only: never changes your photos. Propose where every photo │
│              and video should go: year, event, category.                     │
│ review-sort  Read-only: never changes your photos. Name the events of the    │
│              classify proposal one by one in your browser.                   │
│ places       Read-only: never changes your photos. Name your places on a map │
│              of where the photos were taken; saved into config.toml for the  │
│              'place' and 'trip' rules.                                       │
│ inventory    Read-only: never changes your photos. Export every photo and    │
│              video with what the audits learnt to Excel, from the cache      │
│              alone: no file is read.                                         │
│ history      Read-only: never changes your photos. List the runs and what    │
│              they did.                                                       │
│ reports      Read-only: never changes your photos. List the HTML reports of  │
│              previous audits and cleans.                                     │
│ config       Read-only: never changes your photos. Show every setting, where │
│              it comes from, and the mount points.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Act ────────────────────────────────────────────────────────────────────────╮
│ review       Read-only: never changes your photos. Set burst shots aside,    │
│              one series at a time, with the keyboard in your browser; 'clean │
│              --decisions' then moves them.                                   │
│ clean        Audit, confirm, then move the duplicate copies to the           │
│              quarantine, after a byte comparison (journaled, undoable);      │
│              --delete deletes them for good.                                 │
│ sort         Move the photos and videos as the edited classify workbook says │
│              (journaled, undoable).                                          │
│ album        Gather a selection of the classify plan into a folder of hard   │
│              links: nothing is copied nor moved (journaled, undoable).       │
│ undo         Restore every file of a run, from the kept copy, the quarantine │
│              or where it was moved; remove the links of an album.            │
│ purge        Erase the quarantine of a run for good: with 'clean --delete',  │
│              the only way the tool removes content.                          │
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

 Read-only: never changes your photos. Find exact duplicates and broken files.

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

<details>
<summary><code>review --help</code></summary>

<!-- capture: help-review.txt -->
```text
 Usage: media-hygiene review [OPTIONS]

 Read-only: never changes your photos. Set burst shots aside, one series at a
 time, with the keyboard in your browser; 'clean --decisions' then moves them.

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

 Audit, confirm, then move the duplicate copies to the quarantine, after a byte
 comparison (journaled, undoable); --delete deletes them for good.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes        -y                    Do not ask for confirmation (overrides    │
│                                    clean.confirm).                           │
│ --tier               <exact|near>  exact: byte-for-byte copies only. near:   │
│                                    also near duplicates (resized or          │
│                                    recompressed copies, re-encoded videos);  │
│                                    check them in the report first. Both go   │
│                                    to the quarantine. Default: exact.        │
│ --decisions          <path>        decisions.json downloaded from an audit   │
│                                    report (swap or leave alone some folder   │
│                                    pairs) or written by 'review' (burst      │
│                                    shots set aside). A relative path is read │
│                                    from the folder mounted on /reports. The  │
│                                    file is refused if the folders, the pairs │
│                                    or the series changed.                    │
│ --delete                           Delete the exact copies for good, after a │
│                                    byte comparison with the kept copy,       │
│                                    instead of moving them to the quarantine: │
│                                    the space is freed at once; 'undo'        │
│                                    rebuilds them from the kept copy.         │
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

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Usage: media-hygiene undo [OPTIONS] [run_id]

 Restore every file of a run, from the kept copy, the quarantine or where it
 was moved; remove the links of an album.

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

 Read-only: never changes your photos. List the runs and what they did.

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

 Erase the quarantine of a run for good: with 'clean --delete', the only way
 the tool removes content.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Run whose quarantine is erased; every run by default.   │
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

 Read-only: never changes your photos. List the HTML reports of previous audits
 and cleans.

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

 Read-only: never changes your photos. Compare a fresh audit with Czkawka's
 results: a second, independent opinion.

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

<details>
<summary><code>classify --help</code></summary>

<!-- capture: help-classify.txt -->
```text
 Usage: media-hygiene classify [OPTIONS]

 Read-only: never changes your photos. Propose where every photo and video
 should go: year, event, category.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year                   <str>               Only the files of this year, or │
│                                              of these years: 2016 or         │
│                                              2015-2017.                      │
│ --layout                 <str>               Where sure files go, e.g.       │
│                                              '{year}/{month} -               │
│                                              {month_name}'.                  │
│ --target                 <str>               Host folder receiving the tree; │
│                                              in place by default.            │
│ --leave                  <str>               Host folder never sorted        │
│                                              (analysed and cleaned as        │
│                                              usual).                         │
│ --carry-over             <str>               Workbook whose edits are        │
│                                              carried over; the latest        │
│                                              classify run's by default.      │
│ --no-carry-over                              Start fresh: carry no edit of a │
│                                              previous workbook over.         │
│ --sample                 <int range> [x>=0]  Describe this many random       │
│                                              photos with the local model,    │
│                                              print the time per photo and    │
│                                              the estimate of a full run, and │
│                                              stop.                           │
│ --no-describe                                Ask the local model nothing     │
│                                              new: the subject rules read the │
│                                              descriptions already in the     │
│                                              cache.                          │
│ --yes            -y                          Describe the photos without     │
│                                              asking, however many.           │
│ --help           -h                          Show this message and exit.     │
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
<summary><code>album --help</code></summary>

<!-- capture: help-album.txt -->
```text
 Usage: media-hygiene album [OPTIONS] {name}

 Gather a selection of the classify plan into a folder of hard links: nothing
 is copied nor moved (journaled, undoable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    name      <str>  The album's name: the folder holding its links.        │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --category          <str>                  The files of this category, as    │
│                                            the edited workbook says.         │
│ --event             <str>                  The files of this event: its id   │
│                                            or its name.                      │
│ --rule              <str>                  The files the classify rule of    │
│                                            this name decided.                │
│ --rating            <int range> [1<=x<=5]  The files given at least these    │
│                                            stars in Windows (1 to 5).        │
│ --workbook          <str>                  The classify workbook to read;    │
│                                            the latest classify run's by      │
│                                            default.                          │
│ --apply                                    Make the links; without it, only  │
│                                            show what the album gathers.      │
│ --help      -h                             Show this message and exit.       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>inventory --help</code></summary>

<!-- capture: help-inventory.txt -->
```text
 Usage: media-hygiene inventory [OPTIONS]

 Read-only: never changes your photos. Export every photo and video with what
 the audits learnt to Excel, from the cache alone: no file is read.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --format          <xlsx|csv>  xlsx: an Excel workbook (Files and Summary     │
│                               sheets). csv: the Files sheet only, like       │
│                               plan.csv. Default: xlsx.                       │
│ --help    -h                  Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Usage: media-hygiene config [OPTIONS]

 Read-only: never changes your photos. Show every setting, where it comes from,
 and the mount points.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>places --help</code></summary>

<!-- capture: help-places.txt -->
```text
 Usage: media-hygiene places [OPTIONS]

 Read-only: never changes your photos. Name your places on a map of where the
 photos were taken; saved into config.toml for the 'place' and 'trip' rules.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=0]  Port of the page inside the container;   │
│                                     publish it with -p 127.0.0.1::8080 so    │
│                                     that Docker chooses a free one on your   │
│                                     computer. Default: 8080.                 │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
