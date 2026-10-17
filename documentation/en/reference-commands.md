# Commands and options

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-commands.md)

Every command, every option. The [user guide](README.md#start-here) introduces
them one at a time; this page gathers them. The commands whose help starts with *Read-only* never change your photos
([how your photos stay safe](reference-safety.md)).

## Which command?

| I want to… | Command |
|---|---|
| know, without any risk, how many copies my folders hold and how much space they take | [`audit`](commands/audit.md) |
| know in a second where I stand after a few days, and the next step | [`status`](commands/status.md) |
| not remember any command: see every step, run the next one with Enter | [`menu`](commands/menu.md) (`mh` alone) |
| free the space my duplicate photos take, safely: set aside, never erased | [`clean`](commands/clean.md) |
| keep only the best shots of my bursts, decide the near duplicates | [`review`](commands/review.md), then `clean --decisions` |
| see what each run did | [`history`](commands/history.md) |
| put back every file of a run, exactly where it was | [`undo`](commands/undo.md) |
| get the space back for good, once I checked the quarantine | [`purge`](commands/purge.md) |
| be sure of the duplicates before deleting family photos | [`crosscheck`](commands/crosscheck.md) |
| find every report again, delete the old ones | [`reports`](commands/reports.md) |
| get a tidy tree proposed, by year, event, place or person, and correct it first | [`classify`](commands/classify.md) |
| name my events while looking at their photos | [`review-sort`](commands/review-sort.md) |
| move my photos into the tree I approved, undoable | [`sort`](commands/sort.md) |
| put one photo in several albums, without a copy | [`album`](commands/album.md) |
| name my places on a map, to sort by place and by trip | [`places`](commands/places.md), then `classify` |
| find the photos of someone by name, sort them by who is on them | [`people`](commands/people.md), then `search` or `classify` |
| give my photos and videos words to search for | [`tags`](commands/tags.md) |
| find a photo by a word, a place, a year, a person | [`search`](commands/search.md) |
| look through my folders and remove photos, without Explorer, undoably | [`browse`](commands/browse.md), then `clean --decisions` |
| see my words in digiKam, darktable, Lightroom or Immich | [`xmp`](commands/xmp.md) |
| answer my own questions about my photos in Excel | [`inventory`](commands/inventory.md) |
| type `mh audit` instead of a long `docker run` | [`launcher`](commands/launcher.md) |
| check every setting and every folder before the tool acts | [`config`](commands/config.md) |

## Commands

Each command has its own page. It starts with **In short**: what the command gives you, when to
use it and the command to try; then the folders it needs, its options, examples and its `--help`.

**🔒 Analyse: read-only, never changes your photos**

| Command | What it does | Guide |
|---|---|---|
| [`audit`](commands/audit.md) | Find exact duplicates and broken files. Never writes to your folders. | [1](start/01-first-audit.md) |
| [`status`](commands/status.md) | Where am I? The last audit, the quarantine, the runs still undoable, the reviews not applied, the last proposal not sorted; then one next step as a full command. Reads the tool's folders only, no scan. | [Cleaning, 9](clean/09-undo-history-purge.md#where-am-i-status) |
| [`menu`](commands/menu.md) | What `mh` alone shows: every step of the three guides with its full `mh` command, the one `status` would give proposed; Enter runs it through `mh`, a number runs another. Reads the tool's folders only, no scan. | [Clean in short](clean/quick-guide.md) |
| [`review`](commands/review.md) | Audit, then sort the burst series in your browser, one at a time, with the keyboard; `--near`: decide the near duplicates group by group. Never writes to your folders. | [Cleaning, 10](clean/10-review-bursts.md), [11](clean/11-near-duplicates.md#decide-in-your-browser-review---near) |
| [`history`](commands/history.md) | List the runs: their command, files deleted, space freed, quarantine, restores. | [Cleaning, 9](clean/09-undo-history-purge.md) |
| [`reports`](commands/reports.md) | List the reports and refresh `index.html`; `--prune N` keeps the N most recent. | [Cleaning, 4](clean/04-html-report.md) |
| [`crosscheck`](commands/crosscheck.md) | Audit again, run Czkawka, an independent duplicate finder, then compare both. | [Cleaning, 13](clean/13-second-opinion.md) |
| [`config`](commands/config.md) | Show every setting, where it comes from, and the state of each mount point; creates a commented `config.toml` the first time. | [Cleaning, 7](clean/07-configuration-file.md) |
| [`launcher`](commands/launcher.md) | Print the script of `mh`, a short command holding the folders of this run: `mh audit`, `mh clean`… with the right mounts for each command. Redirect it to a file (`> mh.ps1`), without `-it`. | [3](start/01-first-audit.md#write-mh-once) |
| [`classify`](commands/classify.md) | Propose where every photo and video should go: year, event, category. Never writes to your folders; writes a workbook to edit and a report to `/reports`. | [Sorting, 4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md), [8](sort/08-subjects-from-a-local-model.md), [10](sort/10-sort-by-person.md) |
| [`review-sort`](commands/review-sort.md) | Show the events of the `classify` proposal one at a time in your browser, with their photos, and name them with the keyboard; saved next to `plan.json`, applied by `sort`. Never writes to your folders nor to the workbook. | [Sorting, 11](sort/11-name-events-in-the-browser.md) |
| [`places`](commands/places.md) | Show where the photos were taken on a map in your browser, and name your places; saved into `config.toml`. Never writes to your folders. | [Sorting, 9](sort/09-places-from-gps.md) |
| [`inventory`](commands/inventory.md) | Export every photo and video with what the audits learnt to an Excel workbook (or a CSV file), from the cache alone: no file is read. | [Reference](reference-inventory.md) |
| [`tags`](commands/tags.md) | Give every photo and video words to find it by: the meaningful words of its folders and of its file name, its date (year, month, season, holidays), its place, and what a local vision model sees (optional; a video by its middle frame). Kept in the cache, never written into the photos. | [Reference](reference-tags.md) |
| [`search`](commands/search.md) | Find photos by their words (those of `tags`) and the names given in `people` (`person:"…"`) in your browser, with filters and previews; with words, print the first matches as a table. Photos picked can be set aside for `clean --decisions`. Never writes to your folders. | [Reference](reference-tags.md#find-a-photo-by-its-words-search) |
| [`browse`](commands/browse.md) | Walk through your folders in your browser, as in Explorer: the tree with its counts, the photos and videos of a folder, large with ←/→; set the ones picked aside for `clean --decisions`. Never writes to your folders. | [Find in short](find/quick-guide.md) |
| [`people`](commands/people.md) | Find the faces in the photos, group those that look alike, and name them in your browser (the names go into `config.toml`; `search` finds them). The faces stay in the cache, never sent anywhere; `--forget` deletes them all. Never writes to your folders. | [Reference](reference-people.md), [Sorting, 10](sort/10-sort-by-person.md) |

**Act: moves, writes or deletes files** (journaled, undoable)

| Command | What it does | Guide |
|---|---|---|
| [`clean`](commands/clean.md) | Audit, confirm, then move duplicate copies, unreadable files and orphan sidecars to the quarantine, and delete empty files; `--delete` deletes the copies instead. | [Cleaning, 8](clean/08-clean.md) |
| [`undo [RUN]`](commands/undo.md) | Restore every file of a run (the latest by default); for an album, remove its links; for `xmp`, its sidecars. | [Cleaning, 9](clean/09-undo-history-purge.md) |
| [`purge [RUN]`](commands/purge.md) | Erase the quarantine of a run for good (of every run by default): the only command that erases content, with `clean --delete`. | [Cleaning, 9](clean/09-undo-history-purge.md) |
| [`sort [WORKBOOK]`](commands/sort.md) | Check the edited workbook of `classify`, confirm, then move the files where it says; journaled, undoable, proven. | [Sorting, 7](sort/07-sort.md) |
| [`album NAME`](commands/album.md) | Gather a selection of the `classify` plan (a category, an event, a rule, the stars) into a folder of hard links: nothing copied nor moved, no space used. Shows the selection; `--apply` makes the links. | [Sorting, 12](sort/12-albums.md) |
| [`xmp`](commands/xmp.md) | Write the words of `tags` into `.xmp` sidecars next to the photos, for digiKam, darktable, Lightroom or Immich; never into a photo. Shows what it would write; `--apply` writes. | [Reference](reference-tags.md#carry-the-words-with-the-photos-xmp) |

## Options

Global options go **before** the command: `cavo789/media-hygiene --locale fr audit`. The others go
**after** it: `cavo789/media-hygiene audit --prefer "C:\Photos\Family"`.

| Option | Commands | Meaning |
|---|---|---|
| `--locale en\|fr` | global | Interface language (English by default); numbers and sizes follow it: `67,947` and `44.3 GB`, or `67.947` and `44,3 Go`. |
| `--verbosity error\|warning\|info\|verbose\|debug` | global | How much to log. `verbose`: `info`, plus every tip of a command (not only the two most useful) and the inventory after an audit. |
| `--color auto\|always\|never` | global | ANSI colours (`NO_COLOR` is honoured). |
| `--version` | global | Show the version. |
| `--prefer PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder whose copies are kept first; repeatable, ordered. [Cleaning, step 5](clean/05-choose-the-kept-copy.md#prefer-a-folder) |
| `--protect PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder never modified; its files are the copies kept. [Cleaning, step 5](clean/05-choose-the-kept-copy.md#protect-a-folder) |
| `--exclude PATH` | `audit`, `review`, `clean`, `crosscheck` | Folder never analysed. [Cleaning, step 5](clean/05-choose-the-kept-copy.md#exclude-a-folder) |
| `--exclude-name NAME` | `audit`, `clean`, `crosscheck` | Folder name never analysed, wherever it is (case ignored, `*` and `?` allowed: `--exclude-name Thumbnails,.Trash-*`); adds to the system and trash folders always skipped. [Cleaning, step 5](clean/05-choose-the-kept-copy.md#skip-a-folder-name-on-every-disk) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | Only analyse these categories or extensions (`--ext photo,video`, `--ext png,webp`); built-in categories `photo`, `raw`, `video`, `media`, plus those of `[scan.categories]`; `media` (every photo, RAW and video) by default. Other types too (`--ext pdf,docx`). [Cleaning, step 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge`, `classify`, `tags`, `audit` | Do not ask for confirmation (`undo` asks only before undoing several runs of one sort; `classify` and `tags`, before describing many photos with a local model; `audit`, before looking for faces with `--people`). |
| `--people` | `audit` | Then look for faces in the photos not looked at yet, after saying how long it takes and asking. [People](reference-people.md#during-the-audit-audit---people) |
| `--tier exact\|near\|near-all` | `clean` | `exact` (default): byte-for-byte copies only. `near`: also move the sure near duplicates, and those decided with `review --near`, to the quarantine. `near-all`: every near duplicate. [Cleaning, step 11](clean/11-near-duplicates.md#sure-groups-and-groups-to-check) |
| `--near` | `review` | Decide the near duplicates group by group (as planned, keep the other version, leave alone) instead of sorting the burst series. [Cleaning, step 11](clean/11-near-duplicates.md#decide-in-your-browser-review---near) |
| `--delete` | `clean` | Delete the exact copies for good, after a byte comparison, instead of moving them to the quarantine; `undo` rebuilds them from the kept copy. [Cleaning, step 8](clean/08-clean.md#need-the-space-at-once---delete) |
| `--decisions FILE` | `clean`, `review` | `clean`: apply the folder-pair decisions of a report, the burst shots set aside with `review` and the near-duplicate groups decided with `review --near` (with `--tier near`). `review`: the file the choices are saved in, `decisions.json` by default. A relative path is read from `/reports`. Once applied by `clean`, the file is renamed `decisions.applied-<run>.json`. [Cleaning, step 10](clean/10-review-bursts.md), [cleaning, step 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review`, `review-sort`, `places`, `search`, `browse`, `people` | Port of the page, `8088` by default; publish the same one: `-p 127.0.0.1:8088:8088`. |
| `--prune N` | `reports` | Keep the N most recent reports, delete the others. |
| `--photos "C:\Photos"` | `launcher` | A folder of photos and videos, as Explorer shows it; repeat it for several folders. No `-v` needed. [Clean in short, 0](clean/quick-guide.md#0-once-write-the-mh-command) |
| `--quarantine "D:\quarantine"` | `launcher` | Where the copies set aside go; best on the photos' disk. Default: `$HOME\media-hygiene\quarantine`. |
| `--shell powershell\|bash` | `launcher` | The shell of the `mh` script; guessed from the mounted folders by default (a Windows folder: PowerShell). [Step 3](start/01-first-audit.md#write-mh-once) |
| `--year YEAR[-YEAR]` | `classify` | Only the files of this year or these years. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--layout LAYOUT` | `classify` | Where sure files go, e.g. `{year}/{month}`. [Sorting, step 4](sort/04-classify.md#your-own-structure) |
| `--target PATH` | `classify` | Folder receiving the tree; each mounted folder, in place, by default. |
| `--leave PATH` | `classify` | Folder never sorted; still analysed and cleaned. |
| `--carry-over PATH` | `classify` | Workbook whose edits are carried over; the latest `classify` run's by default. [Sorting, step 5](sort/05-review-the-proposal.md#improve-the-proposal-without-losing-your-work) |
| `--no-carry-over` | `classify` | Start fresh: carry no edit of a previous workbook over. |
| `--sample N` | `classify` | Describe N random photos with the local model, print the time per photo and the estimate of a full run, and stop. [Sorting, step 8](sort/08-subjects-from-a-local-model.md#measure-first---sample) |
| `--no-describe` | `classify` | Ask the local model nothing new: the `subject` rules read the descriptions already in the cache. [Sorting, step 8](sort/08-subjects-from-a-local-model.md#the-long-run-never-in-the-way) |
| `--sample N` | `tags` | Describe N random photos with the local model, print their words, the time per photo and the estimate of a full run, and stop. [Tags](reference-tags.md#measure-first---sample) |
| `--no-describe` | `tags` | Ask the local model nothing new: the words of the folders, names, dates and places, and the descriptions already in the cache. [Tags](reference-tags.md#the-words-of-a-local-vision-model) |
| `--path PATH` | `tags`, `xmp`, `people` | Only the photos below this folder (host path); repeat it for several. [Tags](reference-tags.md#one-folder-first---path) |
| `--sample N` | `people` | Analyse N random photos, print the time per photo and the estimate of a full run, and stop. [People](reference-people.md#measure-first---sample) |
| `--forget` | `people` | Delete every face from the cache, then show that none is left; asks before deleting the names of `config.toml` too. [People](reference-people.md#your-privacy) |
| `--limit N` | `search` | With words: list at most N files (20 by default). [Tags](reference-tags.md#find-a-photo-by-its-words-search) |
| `--format xlsx\|csv` | `inventory` | `xlsx` (default): a workbook with the Files and Summary sheets. `csv`: the Files sheet only, like `plan.csv`. [Inventory](reference-inventory.md#a-csv-file-instead) |
| `--keep-empty-folders` | `sort` | Keep the source folders the sort leaves empty. [Sorting, step 7](sort/07-sort.md#folders-left-empty) |
| `--category NAME` | `album` | The files of this category, as the edited workbook says (an event named in the workbook gives its name). [Sorting, step 12](sort/12-albums.md#choose-what-the-album-gathers) |
| `--event EVENT` | `album` | The files of this event: its id (Events sheet) or its name. |
| `--rule NAME` | `album` | The files the `[[classify.rules]]` entry of this name decided. |
| `--rating N` | `album` | The files given at least N stars (1 to 5) in Windows, as the audit read them (needs `/cache`). |
| `--workbook PATH` | `album` | The `classify` workbook to read; the latest `classify` run's by default. |
| `--apply` | `album`, `xmp` | Make the links, write the sidecars; without it, `album` and `xmp` only show what they would do. |

Most options have a `config.toml` counterpart ([cleaning, step 7](clean/07-configuration-file.md)); the command
line wins. The rules of `classify` (`[[classify.rules]]`) have no option: they are written in
`config.toml` only ([sorting, step 6](sort/06-write-down-what-you-know.md)).

## The built-in help

`cavo789/media-hygiene --help` and `cavo789/media-hygiene <command> --help` document everything, in
both languages (`--locale fr --help`). A command with more than four options lists those of daily
use first, under **Options** (`clean --tier`, `review --near`, `classify --year`…); the others come
after, under **Advanced options** and, for the folders and the scan,
under **Advanced: folders** and **Advanced: scan** (they override `config.toml`). The page of each
command shows its own `--help`; here is the list of the commands:

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
│ --locale           <en|fr>                      Interface language.          │
│ --verbosity        <error|warning|info|verbose  How much to log.             │
│                    |debug>                                                   │
│ --color            <auto|always|never>          When to use colours          │
│                                                 (NO_COLOR is honoured too).  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🔒 Analyse: read-only, never changes your photos ───────────────────────────╮
│ audit        Find exact duplicates and broken files.                         │
│ classify     Propose where every photo and video should go: year, event,     │
│              category, and what lone photos show with an optional local AI   │
│              🤖                                                              │
│ config       Show every setting, where it comes from, and the mount points.  │
│ crosscheck   Run Czkawka, an independent duplicate finder, then compare its  │
│              groups with a fresh audit: a second opinion.                    │
│ history      List the runs and what they did.                                │
│ inventory    Export every photo and video with what the audits learnt to     │
│              Excel, from the cache alone: no file is read.                   │
│ launcher     Write 'mh', a short command holding your folders: mh audit, mh  │
│              clean.                                                          │
│ menu         Every step of the guides with its command, the next one first:  │
│              what 'mh' alone shows, Enter runs it.                           │
│ people       Find the faces in the photos, group those alike and name them   │
│              in your browser. Faces kept in the cache, never sent anywhere.  │
│ places       Name your places on a map of where the photos were taken; saved │
│              into config.toml for the 'place' and 'trip' rules.              │
│ reports      List the HTML reports of previous audits and cleans.            │
│ review       Set burst shots aside, one series at a time, with the keyboard  │
│              in your browser; 'clean --decisions' then moves them.           │
│ review-sort  Name the events of the classify proposal one by one in your     │
│              browser.                                                        │
│ search       Find photos by their words in your browser (or as a table): the │
│              words 'tags' gave them.                                         │
│ status       Where am I? The last audit, the quarantine, what is left: no    │
│              scan.                                                           │
│ tags         Give every photo words to find it by, kept in the cache, never  │
│              in the photos: its folders, name, date and place, and what it   │
│              shows with an optional local AI 🤖                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Act: moves, writes or deletes files ────────────────────────────────────────╮
│ album        Gather a selection of the classify plan into a folder of hard   │
│              links: nothing is copied nor moved (journaled, undoable).       │
│ clean        Audit, confirm, then move the duplicate copies to the           │
│              quarantine, after a byte comparison (journaled, undoable);      │
│              --delete deletes them for good.                                 │
│ purge        Erase the quarantine of a run for good: with 'clean --delete',  │
│              the only way the tool removes content.                          │
│ sort         Move the photos and videos as the edited classify workbook says │
│              (journaled, undoable).                                          │
│ undo         Restore every file of a run, from the kept copy, the quarantine │
│              or where it was moved; remove the links of an album.            │
│ xmp          Write the words of 'tags' into .xmp sidecars next to the        │
│              photos, for digiKam, darktable, Lightroom or Immich; never into │
│              a photo (journaled, undoable).                                  │
╰──────────────────────────────────────────────────────────────────────────────╯


 A Windows folder (PowerShell):
   docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" media-hygiene audit
 The current folder (PowerShell, or bash on WSL, Linux, macOS):
   docker run --rm -it -v "${PWD}:/data/current:ro" media-hygiene audit

 Step-by-step guide and every command: https://cavo789.github.io/media-hygiene/
```

</details>
