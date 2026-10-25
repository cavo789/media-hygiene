# `classify`: propose a tidy tree

[Documentation](../README.md) › [Commands](../reference-commands.md) › `classify` · 🇫🇷 [Français](../../fr/commands/classify.md)

## In short

**Get a tidy tree proposed for all your photos, by year, event, place or person, and correct it
before anything moves.**

`classify` proposes a place for every photo and video, `year/year-month/event` by default:
`2019/2019-08/Seaside holidays` ([the convention](../sort/04-classify.md#the-convention-year-month-event)).
What is not decided stays where it is. It **only proposes**: nothing moves. You correct the
proposal in a [workbook](../reference-glossary.md#workbook), then [`sort`](sort.md) applies it.

**When**: after cleaning the duplicates (otherwise both copies are sorted); again after new
photos or a changed rule: your edits of the previous workbook are carried over.

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene classify
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders. |
| Recommended | `/cache` (dates, cameras and places come from it), `/reports` (the workbook and the report), `/config` (your layout and rules). |
| Writes | `/reports/<date>-classify/`: `classify.xlsx`, `report.html`, `plan.json`. Without `/reports`, the proposal stays on screen only. |
| Undo | Nothing to undo: nothing moved. |
| With `mh` | `mh classify`. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene classify
```

## Read the result

- **Already in place**: the files already where the proposal wants them.
- **Proposal**, by band: **sure** (a folder you named, a rule: `year/year-month/event`), **to
  check** (a guess: stays until you confirm it), **to sort** (nothing tells: stays, grouped by
  event for you to name), **undated** (stays), **left as they are** (protected and `--leave`
  folders, files directly in their `year/year-month` folder).
- A `config.toml` sorting otherwise than the convention, or a rule whose category has several
  folder levels, is said in one line.
- **Why**: the rule or reason of each proposal, then the categories found most.
- The end gives the path of the workbook and of the report.

## Options

| Option | What it does |
|---|---|
| `--path FOLDER` | Only the files below this folder (host path, as you mounted it), repeatable: `--path "C:\Photos\2015"`. Events stay whole: built from every file, only those below the folder get a proposal. With `--year`: both. |
| `--year YEAR[-YEAR]` | Only the files of this year or these years: `2016`, `2015-2017`. One evening at a time. Files only the disk dates (copies, downloads) are left out and counted: a run without `--year` proposes them. The rules written for other years are counted in one line, not named. |
| `--layout LAYOUT` | Where sure files go: `{year}/{year_month}/{category}` by default, `{year}/{month}`… Also `{year_month}` (`2009-11`; `1985-00` when only the year is known), `{quarter}`, `{month_name}`, `{day}`, `{event}`, `{event_start}`, `{place}`, `{country}`, `{region}`, `{city}`. |
| `--target PATH` | Host folder receiving the tree (it must be mounted); each mounted folder, in place, by default. |
| `--leave PATH` | Host folder never sorted, still analysed and cleaned. |
| `--carry-over WORKBOOK` | Carry over the edits of this workbook; the latest `classify` run's by default. |
| `--no-carry-over` | Start fresh. |
| 🤖 `--sample N` | **With a local AI only.** Describe N random photos with the local vision model, print the time per photo and the estimate of a full run, and stop. |
| 🤖 `--no-describe` | **With a local AI only.** Ask the local model nothing new: the `subject` rules read the descriptions already in the cache. |
| 🤖 `--yes`, `-y` | **With a local AI only.** Describe the photos with the local model without asking, however many. |

Every option has its line in the `[classify]` section of `config.toml`; the rules
(`[[classify.rules]]`) are written there only.

## Examples

```powershell
# One year, sorted by month without category
cavo789/media-hygiene classify --year 2016 --layout "{year}/{month}"

# Build the tree in another (mounted) folder, leave the albums alone
cavo789/media-hygiene classify --target "D:\Photos sorted" --leave "C:\Photos\Albums"

# How long would the local model take?
cavo789/media-hygiene classify --sample 20
```

## Good to know

- **Where the dates come from**, the first reliable source winning: the camera (EXIF), the video
  tags, the file name, the folder, and last the date on the disk.
- **Your edits are carried over** to the new workbook: a file by its content, an event by most of
  its files, a category by its name. Nothing is dropped silently: what cannot be carried is
  listed.
- If the latest workbook cannot be opened at all, `classify` stops before writing anything, so
  that your edits are not buried under a newer, empty workbook.
- The local vision model (optional) is set in `[classify.ai]`: the photos are sent to its `url`,
  and only there. The photos [`tags`](tags.md) already described with the same `model` are not
  sent again.
- A `person` rule sorts the events where the people named in [`people`](people.md) appear
  ([sorting, step 10](../sort/10-sort-by-person.md)).

## Go further

- Sorting, [step 4](../sort/04-classify.md), [step 5](../sort/05-review-the-proposal.md),
  [step 6: the rules](../sort/06-write-down-what-you-know.md),
  [step 8: a local model](../sort/08-subjects-from-a-local-model.md),
  [step 9: the GPS](../sort/09-places-from-gps.md), [step 10: by person](../sort/10-sort-by-person.md)
- [Sort in short](../sort/quick-guide.md)
- Next: [`review-sort`](review-sort.md) (optional), then [`sort`](sort.md).

## The built-in help

<details>
<summary><code>classify --help</code></summary>

<!-- capture: help-classify.txt -->
```text
 Usage: media-hygiene classify [OPTIONS]

 🔒 Read-only: never changes your photos. Propose where every photo and video
 should go: year, event, category, and what lone photos show with an optional
 local AI 🤖

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year            <str>  Only the files of this year, or of these years:     │
│                          2016 or 2015-2017.                                  │
│ --path            <str>  Only the files below this folder (host path, as you │
│                          mounted it); repeat it for several. The events stay │
│                          whole: they are built from every file, and only the │
│                          files below the folders get a proposal. With        │
│                          --year: the files of both.                          │
│ --layout          <str>  Where sure files go, e.g. '{year}/{month} -         │
│                          {month_name}'.                                      │
│ --target          <str>  Host folder receiving the tree; in place by         │
│                          default.                                            │
│ --help    -h             Show this message and exit.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --leave                <str>  Host folder never sorted (analysed and cleaned │
│                               as usual).                                     │
│ --carry-over           <str>  Workbook whose edits are carried over; the     │
│                               latest classify run's by default.              │
│ --no-carry-over               Start fresh: carry no edit of a previous       │
│                               workbook over.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🤖 Local AI (Ollama), optional: a model set in config.toml ─────────────────╮
│ --sample               <int range> [x>=0]  Estimate a full run first:        │
│                                            describe this many random photos  │
│                                            with the local model, print the   │
│                                            time per photo and the estimate   │
│                                            of a full run, and stop.          │
│ --no-describe                              Ask the local model nothing new:  │
│                                            the subject rules read the        │
│                                            descriptions already in the       │
│                                            cache.                            │
│ --yes          -y                          Describe the photos without       │
│                                            asking, however many.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
