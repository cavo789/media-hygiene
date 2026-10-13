# 6. Write down what you know: the rules

[Documentation](../README.md) › Sorting, step 6 · 🇫🇷 [Français](../../fr/sort/06-write-down-what-you-know.md)

The workbook ([step 5](05-review-the-proposal.md)) fixes one proposal. A **rule** fixes every
future one: "we were in Italy from 1 to 15 July 2023", "Grandma's birthday is on 12 March",
"the drone's pictures go to Drone". You write it once in `config.toml`, and `classify` applies it
at every run, to next year's photos too.

## Where the rules live

In `config.toml` ([step 7 of the clean guide](../clean/07-configuration-file.md)), after the
`[classify]` settings, one `[[classify.rules]]` block per rule. The file created on the first
run already holds an example list, written in your language: edit it, reorder it, remove what
you do not need.

```toml
[[classify.rules]]
name = "Italy 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Holidays and outings/Italy 2023"

[[classify.rules]]
name = "Existing folders"
match = "existing_folder"

[[classify.rules]]
name = "Christmas"
match = "calendar"
dates = "12-24..12-26"
category = "Parties/Christmas"
```

- `name`: shown as the reason of the files the rule decides, in the summary and the workbook.
- `match`: what the rule reads (the table below).
- `category`: where the files go, through the `{category}` of the layout. Without a category,
  the files the rule matches **stay where they are**.
- `score` (optional): how sure the rule is, from 0 to 100 (below).

> 💡 The rules are read from `config.toml` only: unlike the other settings, no
> `MEDIA_HYGIENE_*` environment variable overrides them.

## What a rule can match

| `match` | Reads | Example |
|---|---|---|
| `existing_folder` | A folder name you chose (`2019/Seaside holidays`, `Mars 2005 - Travaux maison`). | — |
| `event_neighbour` | The loose files of an event join the one folder you named for it. | — |
| `calendar` | Days that come back every year, `dates = "MM-DD..MM-DD"`. | `dates = "12-24..12-26"` |
| `date_range` | Days that happen once, `dates = "YYYY-MM-DD..YYYY-MM-DD"`. | `dates = "2023-07-01..2023-07-15"` |
| `kind` | A kind of file, `kind = "screenshot"`, `"received"` or `"download"`. | `kind = "screenshot"` |
| `path` | A regular expression searched in the path on your computer, folders and name. | `pattern = '(?i)kermesse'` |
| `camera` | A regular expression searched in the make and model. | `pattern = '(?i)dji'` |
| `subject` | What a local vision model sees, for the photos no other rule decided ([step 8](08-subjects-from-a-local-model.md)). | `categories = ["School", "Animals"]` |
| `person` | Someone you named on the [`people`](../reference-people.md) page shows in the event (below). | `names = ["Chloé"]` |
| `place` | The GPS position lies in one of your places ([step 9](09-places-from-gps.md)). | — |
| `trip` | An event far from home, named after its country and town, offline ([step 9](09-places-from-gps.md)). | — |
| `other_category` | The files no rule above it matched. | `category = "Other"` |

`existing_folder` and `event_neighbour` give the folder's own name as the category: they take
no `category`. A rule left out of the list is not applied: an empty list, `rules = []`, sorts by
dates only.

### Dates

A single day is written alone: `dates = "03-12"` for a birthday. `12-31..01-01` crosses New
Year. A day that does not exist, such as `02-30`, is refused when the file is read.

A date rule takes **whole events** (photos taken close together, [step 4](04-classify.md#read-the-result)):
an event goes to the rule when at least half of its photos fall on its days. A New Year's Eve
party that ends at 3 in the morning stays whole; a week of skiing that holds a birthday stays a
week of skiing. Two `date_range` rules sharing a day are a warning: on those days, the first
one listed wins.

### Kinds of files

Told from the name and the metadata only:

- `screenshot`: a screenshot name (`Screenshot_…`, `Capture d'écran …`), or, without any camera
  make, model or position, a PNG or an image smaller than 400 pixels.
- `received`: a picture received through a messaging app (`IMG-20200105-WA0003`,
  `received_…`), which lost its camera date on the way.
- `download`: a video whose name holds a season, a resolution or a codec (`S01E05`, `1080p`,
  `x264`): a downloaded film or series. They are not memories: the example list gives them no
  category, so they stay where they are.

### People

A `person` rule reads the faces you named with [`people`](../reference-people.md): the faces
confirmed on the page, and those close enough to them, as `search` finds them. Run `people` and
name the groups first: [step 10](10-sort-by-person.md) shows the whole path.

```toml
[[classify.rules]]
name = "With Chloé"
match = "person"
names = ["Chloé"]
category = "People/Chloé"
```

- An event goes to the rule when at least `min_share` percent of its photos show the person:
  **10** by default, as the one taking the pictures is seldom on them. `min_share = 30` keeps
  the events where she is often seen; a photo outside any event goes when it shows her.
- `names = ["Chloé", "Manon"]`: the events with either of them. Add `all = true` for those
  where each one reaches the share.
- Case and accents do not matter. A name nobody has on the page stops `classify` before
  anything is read, and names the rule: a typo, or a group not named yet.

Put it **below** the rules you are surer of (dates, places): with 10 %, someone on most of
your events takes most of them, like a "Family" category would.

### Categories

A category may use `{year}`, `{month}`, `{month_name}`, `{day}`, `{event}` and `{event_start}`,
taken from the start of the event: `category = "Parties/Christmas {year}"`; the GPS rules add
`{place}`, `{country}`, `{region}` and `{city}` ([step 9](09-places-from-gps.md#write-the-rules)).
Characters Windows refuses in a folder name are refused.

The example categories are occasions and activities: Parties, Holidays and outings, School,
Sport and leisure, At home, Animals, Nature and landscapes, Documents and screenshots,
Other. Replace them with yours. Avoid a "Family" or "Portraits" category: in a family
collection, it swallows most photos.

## Which rule wins

The rules are read **in order**, and the first one whose score reaches `sure` (80 by default)
decides. When none does, the best one found is a guess, gathered in `year/To check/category`.
When no rule matches, the file goes to `year/To sort/<event>`: "to sort" means "we do not
know", while `other_category` means "sure that nothing above matches".

Each `match` has a default score, which a rule may change with its own `score`; `score = 0`
turns a rule off:

| `match` | Score |
|---|---|
| `date_range` | 95: you wrote it, it is sure |
| `existing_folder` | 90 (85 for a person's folder, `Dad/2018/…`) |
| `path`, `camera` | 90 |
| `calendar`, `kind`, `other_category` | 85 |
| `subject` | 85 when the samples of the event agree; otherwise "to check" |
| `person` | 85 |
| `event_neighbour` | 70: to check |

The scores of the `[classify] scores` table set these defaults for every rule of a kind. A
photo whose date is doubtful (its folder says another year) stays "to check" whatever its
rule.

## See what each rule did

The *Why* table of `classify` counts the files each rule decided, by its name:

<!-- capture: classify.txt|Why|Check their dates -->
```text
Why
┌────────────────────┬────┐
│ Existing folders   │ 76 │
│ no-signal          │  3 │
│ undated            │  3 │
│   Seaside holidays │ 13 │
│   Photos 2019      │ 12 │
│   Mountain hike    │ 10 │
│   Birthday         │  8 │
│   Old phone        │  8 │
│   Christmas        │  6 │
│   Lake             │  6 │
│   Phone            │  6 │
│   Christmas 2020   │  4 │
│   WhatsApp         │  3 │
└────────────────────┴────┘

⚠️  Rules that decided nothing: Films and series, Screenshots and documents,
Event neighbours, Christmas, New Year.
💡 Check their dates, their patterns and their order in config.toml.
```

The rules that decided nothing are named after the table: a typo in a regular expression, a
wrong year, or simply nothing of that kind in your folders. A rule that cannot work stops the
run before anything is read, and names itself (rules are counted from the top of the file):

```text
❌ [[classify.rules]] number 1 in config.toml: rule 'Birthday': '02-30' is not a day that exists.
💡 Correct it, then run the same command again.
```

A setting forgotten or mistyped is pointed at the same way, the rule's `name` next to its number:

```text
❌ 'match' in [[classify.rules]] number 3 ('Holidays') of config.toml: this setting is required.
💡 Correct it, then run the same command again.
```

The workbook shows the same names in the *Reason* column of its Files sheet, and counts them on
its Summary sheet.

Changed a rule after editing the workbook? Run `classify` again: your edits are carried over to
the new workbook ([step 5](05-review-the-proposal.md#improve-the-proposal-without-losing-your-work)).

---

← [5. Review the proposal](05-review-the-proposal.md) · [Documentation](../README.md) · Next: **[7. Sort](07-sort.md)** →
