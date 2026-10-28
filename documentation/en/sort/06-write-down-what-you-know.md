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
- `keep_folders = true` (optional): the folders you named stay below the category (below).

> 💡 The rules are read from `config.toml` only: unlike the other settings, no
> `MEDIA_HYGIENE_*` environment variable overrides them.

## What a rule can match

| `match` | Reads | Example |
|---|---|---|
| `existing_folder` | A folder name you chose (`2019/Seaside holidays`, `Mars 2005 - Travaux maison`). | — |
| `event_neighbour` | The loose files of an event join the one folder you named for it. | — |
| `same_moment` | The photos of a person's folder, or loose, join your folder of the same moment (below). | — |
| `calendar` | Days that come back every year, `dates = "MM-DD..MM-DD"`. | `dates = "12-24..12-26"` |
| `date_range` | Days that happen once, `dates = "YYYY-MM-DD..YYYY-MM-DD"`. | `dates = "2023-07-01..2023-07-15"` |
| `kind` | A kind of file, `kind = "screenshot"`, `"received"` or `"download"`. | `kind = "screenshot"` |
| `path` | A regular expression searched in the path on your computer, folders and name. | `pattern = '(?i)kermesse'` |
| `camera` | A regular expression searched in the make and model. | `pattern = '(?i)dji'` |
| `subject` | What a local vision model sees, for the photos no other rule decided ([step 8](08-subjects-from-a-local-model.md)). | `categories = ["School", "Animals"]` |
| `person` | Someone you named on the [`people`](../reference-people.md) page shows in the event (below). | `names = ["Chloé"]` |
| `place` | The GPS position lies in one of your places ([step 9](09-places-from-gps.md)), or the photo was given that place on the map of [`places`](../commands/places.md) (its GPS being wrong). | — |
| `trip` | An event far from home, named after its country and town, offline ([step 9](09-places-from-gps.md)). | — |
| `other_category` | The files no rule above it matched. | `category = "Other"` |

`existing_folder`, `event_neighbour` and `same_moment` give the folder's own name as the
category: they take no `category`. A rule left out of the list is not applied: an empty list, `rules = []`, sorts by
dates only.

### Dates

A single day is written alone: `dates = "03-12"` for a birthday. `12-31..01-01` crosses New
Year. A day that does not exist, such as `02-30`, is refused when the file is read.

A date rule takes **whole events** (photos taken close together, [step 4](04-classify.md#read-the-result)):
an event goes to the rule when at least half of its photos fall on its days. A New Year's Eve
party that ends at 3 in the morning stays whole; a week of skiing that holds a birthday stays a
week of skiing. Two `date_range` rules sharing a day are a warning: on those days, the first
one listed wins.

**Written from the browser.** On the page of the events, *📌 Remember as a rule* writes such a
rule for the event shown, after saying what it would take
([step 11](11-name-events-in-the-browser.md#remember-an-event-as-a-rule)).

**Seen before it is written.** On the search page, two calendars give a period to the day;
*📌 Make it a rule* then shows the photos the rule would take, each with where it would go, and
those of the same days it leaves to another rule: correct the days or the folder while seeing
them, then save ([`search`](../commands/search.md#make-a-period-a-rule)). *Update a rule…* does
the same for a date rule already written.

**A trip you already sorted into folders.** A date rule above *Existing folders* takes every
photo of its days, those of your own folders too: written alone, it would put
`2019/Montenegro/Budva` and `2019/Montenegro/Cetinje` flat in its category. With
`keep_folders = true`, the category becomes their parent and your folders stay below it:

```toml
[[classify.rules]]
name = "Montenegro"
match = "date_range"
dates = "2019-07-12..2019-07-19"
category = "Holidays and outings/Montenegro"
keep_folders = true
```

gives `2019/Holidays and outings/Montenegro/Budva` and `…/Montenegro/Cetinje`; the photos of a
person's folder taken the same days follow the folder of their moment
([below](#your-familys-folders)), the others go to `…/Montenegro`.

Only the event's **main folder** (the one holding most of its photos) and the folders sharing
a parent with it are kept: a wedding sorted into `2017/August 2017/Hervé and Magda's wedding`
becomes the category itself, never `…/Hervé and Magda's wedding/Hervé and Magda's wedding`; a
folder sharing nothing with it (`2017/Development Sep`) goes to the category flat, never below
it. A person's folder taken the same evening (`Manon\…`) is such an unrelated folder: list
the name in `person_folders` ([below](#your-familys-folders)) and its photos join the wedding
by their moment.

**A date rule never takes a screenshot.** The files a `kind` rule recognises (screenshots,
received pictures, downloads) are not memories of the day, wherever that rule is listed: they
keep the rule they would have without the date rule.

### Folder and file names

A `path` rule searches its pattern in the whole path, as Windows writes it
(`C:\Photos\Chris & Fred\foto020601214749_957.jpg`): a folder name, a file name, or both.
`(?i)` ignores case. An old camera named its photos `foto` + date + time
(`foto020601214749_957`: 1 June 2002, 21:47:49); all those of that day start with
`foto020601`:

```toml
[[classify.rules]]
name = "Chris and Fred's wedding"
match = "path"
pattern = '(?i)chris ?& ?fred|\bfoto020601'
category = "Parties/Weddings/Chris and Fred's wedding 2002"
```

`|` means "or": the folder `Chris & Fred` or a name starting with `foto020601`. `\b` marks
the start of a word, so `myfoto020601…` does not match. Write the pattern between single
quotes: a backslash then stays as typed.

### Kinds of files

Told from the name and the metadata only:

- `screenshot`: a screenshot name (`Screenshot_…`, `Capture d'écran …`), or, without any camera
  make, model or position, a PNG or an image smaller than 400 pixels. A PNG named like a
  camera (`IMG_20190123_202218.png`) is taken for an edited photo, not a screenshot.
- `received`: a picture received through a messaging app (`IMG-20200105-WA0003`,
  `received_…`), which lost its camera date on the way.
- `download`: a video whose name holds a season, a resolution or a codec (`S01E05`, `1080p`,
  `x264`): a downloaded film or series. They are not memories: the example list gives them no
  category, so they stay where they are.

### Your family's folders

You sorted a trip yourself, `2019/Montenegro/Budva`, `…/Cetinje`; your daughters' photos of the
same days sit in `2019/Photos Chloé` and `Manon 2023/dcim`. A folder is **a person's** when the
name of someone is found in it, as a word, case and accents ignored (`Photos Chloé`, `Backup
Manon`, `iPhone Manon`; not `Chloéville`). The names are those of the
[`people`](../reference-people.md) page, plus a list for the people not named there:

```toml
[classify]
person_folders = ["Chloé", "Manon"]
```

With a `same_moment` rule (in the example list), each photo of a person's folder, and each loose
photo (`DCIM`), taken during a **session** (photos without a 6-hour break,
`session_gap_hours`) where your own folders hold photos joins your folder: `Photos Chloé` of the
12th would go to `2019/2019-07/Montenegro/Budva`, that of the 13th to `…/Cetinje`. Two of your
folders in the same session: the one whose photo is nearest in time. A photo of no such session
goes to the trip's folder, the common parent of your folders (`Montenegro`), unless they share
none (or only a year). They are **to check**: look at them in the report. A photo of a folder
you named yourself never moves. `score = 0` on the rule turns it off.

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
taken from the start of the event (the month is `00` when only the year is known): `category = "Parties/Christmas {year}"`; the GPS rules add
`{place}`, `{country}`, `{region}` and `{city}` ([step 9](09-places-from-gps.md#write-the-rules)).
Characters Windows refuses in a folder name are refused.

The example categories are occasions and activities: Parties, Holidays and outings, School,
Sport and leisure, At home, Animals, Nature and landscapes, Documents and screenshots,
Other. Replace them with yours. Avoid a "Family" or "Portraits" category: in a family
collection, it swallows most photos.

## A camera whose clock was wrong

On a trip abroad, the phone sets itself to the local time; the camera does not. Its photos
come out an hour behind the phone's, and an event photographed with both is cut or mixed up.
Write the shift once in `config.toml`, as a `[[classify.clocks]]` table, next to the rules:

```toml
[[classify.clocks]]
camera = '(?i)canon eos 550d'      # searched in the make and model, as the camera rule
dates = "2010-07-01..2010-07-15"   # the camera's own days, the wrong ones
shift = "+1h"                      # what to add: + or -, then days d, hours h, minutes m
```

`classify` and `tags` read the EXIF dates of that camera, on those days, an hour later: the
two devices' photos make one event, in the right order. Nothing is written into the photos.
The Files sheet of the workbook says it in the **Date from** column (`camera (EXIF), +1h:
rule (?i)canon eos 550d`). A shift combines units (`-1d`, `+1d2h30m`); a shift or a range
that cannot be read stops the run, naming the rule, and so do two rules of one camera that
share a day.

A date **after the day of the run** cannot be right: a clock set wrong. The file goes to
"to check" (**Date from** ends with `in the future: to check`), as a year its folder
contradicts does.

## Which rule wins

The rules are read **in order**, and the first one whose score reaches `sure` (80 by default)
decides. When none does, the best one found is a guess: the file stays where it is until you
confirm it. When no rule matches, the file stays too: "to sort" means "we do not know", while
`other_category` means "sure that nothing above matches".

Each `match` has a default score, which a rule may change with its own `score`; `score = 0`
turns a rule off:

| `match` | Score |
|---|---|
| `date_range` | 95: you wrote it, it is sure |
| `existing_folder` | 90 (85 for a person's folder, `Dad/2018/…`, `Photos Chloé`) |
| `path`, `camera` | 90 |
| `calendar`, `kind`, `other_category` | 85 |
| `subject` | 85 when the samples of the event agree; otherwise "to check" |
| `person` | 85 |
| `event_neighbour`, `same_moment` | 70: to check |

The scores of the `[classify] scores` table set these defaults for every rule of a kind. A
photo whose date is doubtful (its folder says another year) stays "to check" whatever its
rule.

## See what each rule did

The *Why* table of `classify` counts the files each rule decided, by its name:

<!-- capture: classify.txt|Why|Check their dates -->
```text
Why
┌───────────────────────────┬────┐
│ Existing folders          │ 76 │
│ No signal                 │  5 │
│ Undated                   │  4 │
│ Screenshots and documents │  1 │
└───────────────────────────┴────┘

Largest categories
┌──────────────────┬────┐
│ Seaside holidays │ 13 │
│ Photos 2019      │ 12 │
│ Mountain hike    │ 10 │
│ Birthday         │  8 │
│ Old phone        │  8 │
│ Christmas        │  6 │
│ Lake             │  6 │
│ Phone            │  6 │
│ Christmas 2020   │  4 │
│ WhatsApp         │  3 │
└──────────────────┴────┘

⚠️  Rules that decided nothing: Films and series, Event neighbours, Christmas,
New Year.
💡 Check their dates, their patterns and their order in config.toml.
```

The rules that decided nothing are named after the table: a typo in a regular expression, a
wrong year, or simply nothing of that kind in your folders.

**Keep the list alive: *Your rules*.** On the page of the events
([`review-sort`](../commands/search.md#the-events-of-the-latest-classify)), **📌 Your rules** lists every rule of
`config.toml`, with the files it decided at the `classify` run the page shows and, for a
folder-name rule, the days of the event holding most of its files. They are shown by kind
(*Dates*, *Folder and file names*, *Days of every year*… your own folders last), each kind
under its heading with its count, then by period, the latest first; a rule that decided
nothing comes last in its kind. A click on *Rule* or *Files* sorts by that column, a second
click reverses, a third goes back. `config.toml` keeps its own order, which decides: the
dialog never changes it.

- a rule that decided nothing is shown in red, with **Remove** (or *Remove the N rules that
  decided nothing*, after a question): it is removed from `config.toml`, your comments kept,
  and the list is read back from the disk;
- a folder-name rule (`path`) serves once: after `sort` moved its files into
  `Holidays and outings/Turin 2018`, the old folder name it looks for is gone. **Turn into
  dates** replaces it, in its place in the list, by a `date_range` rule with the days of that
  event and `keep_folders = true`; the dialog says what changes first ("450 files: 92 of this
  event, 358 of other folders on the same days. Elsewhere: Photos Chloé (358)", and the files
  the old rule decided that the new one would not take). One rule at a time: the days are those
  of the event holding most of its files, never its extreme dates (a pattern also catches
  badly dated photos).

The counts are those of the last `classify`: run it again to see the rules you changed at work. A rule that cannot work stops the
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
