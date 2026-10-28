# `search`: find a photo by its words

[Documentation](../README.md) › [Commands](../reference-commands.md) › `search` · 🇫🇷 [Français](../../fr/commands/search.md)

## In short

**Find a photo by what you remember of it: a word, a place, a year, a person.**

`search` finds photos by the words [`tags`](tags.md) gave them and the names given in
[`people`](people.md), in a page of your browser: one field, a grid of the photos found, best
first, each with its folder, date and words. With words after the command, it prints the first
matches as a table instead. Photos you pick on the page can be **set aside**: the next
[`clean --decisions`](clean.md) moves them to the quarantine, journaled and undoable.

**When**: after [`tags`](tags.md) (and [`people`](people.md) for the names); again after the new
photos are tagged.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Nothing moves without your GO: *I checked: sort these N files* moves the files of a rule checked on the page, journaled; `undo` puts them back. `mh search` mounts them writable, with `/journal`; mounted `:ro`, the page stays read-only and the GO is refused. |
| Needs | `/cache` (the words of `tags`), your folders (to show the photos), and `-p 127.0.0.1:8088:8088` for the page; `/reports` to set photos aside. |
| Writes | The small previews of the grid, in the cache; the photos you set aside, in `decisions.json` of the reports; your albums, in `albums.json` next to it. |
| Undo | Nothing to undo on the page: [`clean --decisions`](clean.md) moves the photos set aside, [`undo`](undo.md) brings them back. |
| With `mh` | `mh search`, `mh search durbuy ours`. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

Open <http://127.0.0.1:8088/>. The page looks and works like [`browse`](browse.md): the search
field and its filters (a period, a part of the path, the words of one source only) in the left
column, the ⌨ keys under them, one bar above the grid, then the photos found. **🔎 Words** comes
first, **📁 Folders** second: it opens `browse`, the same server. Ctrl+C, or closing its tab,
stops the page.

**Path contains** takes a part of the path, case-insensitive. `*` stands for any characters and
`?` for one: `*.mov` finds every `.mov` file (`.MOV` too). Between two slashes it is a regular
expression: `/\.(mov|mp4)$/`. Anything else is read as typed, so `Vacances (2019)` or `a+b` need
no escaping. A regular expression that does not compile is told under the field.

- **⚖ Heaviest files** (above the folders): every folder, no word, the videos first unless
  **Show** says otherwise, the largest first — or **Sort by: bit rate**, the videos worst
  compressed for their length (the best to lighten with [`shrink`](shrink.md)). A video's tile
  says its length, bit rate and codec. **Show more**, under the grid, adds as many files again.
- **In a folder**: under the form, the tree of your folders, as on the folder view (opened on
  demand). A click narrows the search to that folder and below, **without typing any word**:
  empty words list the whole folder; ✕ next to its name searches every folder again.

- **Search**: type the words, then Enter; the keys then go to the grid, `/` comes back to the
  field. *How to write a search* recalls the phrases ("bord de mer"), the starts of words
  (anniv\*) and the words of one source (place:durbuy).
- **Follow a word**: a click on a word under a photo (*Mechelen*, *2026*, a person's name)
  searches it as a phrase in every source, the filters emptied: from one photo to all the others
  with that word. It never picks the photo.
- **Pick**, as in `browse`: a click picks one file; the ☑ box (or Ctrl+click) adds or removes one;
  Shift+click picks every file from the last one clicked; a rectangle dragged with the mouse picks
  what it touches (with Ctrl, it adds); Ctrl+A every file shown, then **Pick all N files found**
  in the bar takes every file the search finds, not only the 240 shown; **Invert the picking**
  (or I) picks the others.
- **Look**: Enter or a double click shows the photo large (with a link to the original); ← → (on a
  phone, a swipe) the previous or next one, Delete sets it aside then shows the next one, F full screen, ? every key,
  Escape closes it. **👤 Set a person aside** finds every photo of someone on the one shown
  ([`people`](people.md#from-any-page-set-a-person-aside)).

- **A period**: *From* and *To* are calendars, a day each, both included; one alone is a period
  of one day. The day is the one the photo was taken, as `classify` dates it. *From* chosen,
  *To* takes the same day when it is empty or earlier. Under them, one click searches
  **📍 Today**, **🗓️ Month** (this month), **📆 Year** (this year); **✕** clears both.
- **Sort by** and **Show**, in the bar as on the [folder view](browse.md): *best match* (the
  default; the newest first without words), *name*, *date* (the oldest first) or *size* (the
  largest first); **Show** keeps the photos or the videos only. The search sorts and filters
  before it shows its first files: *Show: videos*, *Sort by: size* gives the largest videos found.
  Each tile says its date and size.
- **Which date**: `📷 2023-07-14` is the day the photo was **taken**, written in the photo
  itself (EXIF *DateTimeOriginal*; a video's recording date): what *From*, *To* and the years
  find. It is not the *Date modified* Windows Explorer shows by default: point at the date for
  both, with the time taken. Explorer shows the date taken in the file's **Properties ›
  Details › Date taken**, or as the *Date taken* column (right-click the column headers). A file
  that does not say it (a scan, a screenshot) reads *no date taken*: a search by date does not
  find it.
- **The photo's EXIF**: in the large view, **I** lists what the photo says of itself: when it was
  taken, the camera, the lens, the exposure, its size in pixels and its GPS position. Read only:
  the photo is never changed.
- **A video's length** is on its preview's corner, as on video sites: `▶ 1:45`. Under 3 seconds,
  the badge is red: a clip that short is rarely worth keeping (setting it aside stays your
  choice).
- **Sorted**: *every photo*, *not sorted yet* or *sorted (year, then year-month)*, read from the
  folders alone ([the convention](../sort/04-classify.md#the-convention-year-month-event)): a
  photo in `2009\2009-11\…` is sorted, wherever that pair of folders lies and whoever put it
  there. *Not sorted yet*, then pick and **📂 Move to an event…**: the page becomes the way to sort
  what is left, folder after folder.

Without a browser (WSL, a script), give the words: `search durbuy ours` prints the first 20 files
as a table.

## The events of the latest classify

**🗂 Events of the latest classify**, under the folders in the left column, lists the events of
the latest [`classify`](classify.md) plan (it took in `review-sort`, which now only opens it):
the progress line (sorted, already in place, left) and the sort runs of the plan, each with its
undo line; the three filters (*Only the events to decide*, *Only the sure proposals*, *Only the
events not sorted yet*); ✓ on an event already sorted, ⚠ on one whose earlier choice the
workbook changed since. Click an event: its card shows above the list, its photos in the grid,
each tile saying where `sort` will put it (*C:\Photos → 2016\2016-07\Party*). The address
`/events` (and `mh review-sort`) opens the page with the list open.

Choose with the keyboard, as in the old page; every choice is **saved at once** in
`sort-decisions.json` next to the plan, read back from the disk, with what the workbook said
when you chose (a later edit of the same event in the workbook is a conflict, shown in red,
never settled silently). The workbook itself is never changed.

| Key | What it does |
|---|---|
| **F**, then **Enter** | type the event's folder, save it, then the next event to decide |
| **E** | change the event's name (by default, the last folder) |
| **N** / **P**, **U** | next or previous event, next one to decide |
| **O** / **S** | the picked photos: to another folder, or left where they are |
| **Shift+S** | leave the whole event where it is |
| **T** | take back the choice made here (of the picked photos, else of the event) |
| **V**, **Shift+Z** | accept every sure proposal at once, take that batch back |
| **R** | *Remember as a rule*: the event's days and folder written into `config.toml` |
| **M** | *Sort this event now*: where each file goes, then one GO; journaled, `undo` puts it back |
| **Delete**, **⌫** | set the picked photos aside, take them back out (as on every page of photos) |

**📌 Your rules** lists every rule of `config.toml` with the files it decided: remove the ones that
decide nothing, turn a folder-name rule into dates.

## Move photos to an event, without a rule

For a one-off event, a rule is not needed: search its days (or words), **pick** the photos (as
everywhere: click, Ctrl, Shift, a rectangle, Ctrl+A), then **📂 Move to an event…** in the bar.
Type the event's name, or pick one of your event folders the field lists (those already in the
month the photos go to, sub-folders written `France\Morzine`); `\` makes sub-folders of a new name too.
The line under it shows the folder made, as
Explorer will show it, under the year and month of the earliest photo picked
(*→ C:\Photos\2009\2009-11\Anniversaire de Tom*,
[the convention](../sort/04-classify.md#the-convention-year-month-event)). The name proposed is
that of **your folder holding most of the photos picked**: its photos go to the folder of the
same name under the convention, never to a second one beside it.

Before the move, the photos are listed **by source folder**, one tick box each, with their
count. A folder you named after **another** event (`Saint Nicolas 2009`: a name, one evening) is
**unticked**: its photos stay where they are, unless you tick it. A folder of dates, a family
member's folder, a phone's `DCIM` are ticked. **Move these N files now** moves exactly the ticked
ones, journaled, checked at their new place, said as read back (*'mh undo …' puts them back*).
No rule is written: the next `classify` finds them in place. Photos added since the
latest `classify` (a phone imported, then audited) move too: no new `classify` is needed.

## Make a period a rule

Once a period is searched, **📌 Make it a rule** opens, beside the grid, the dialog of
[`review-sort`](#the-events-of-the-latest-classify)'s *Remember as a rule*, filled with the period: type its name
and its folder (*keep my folders below it* is on). As you type, the grid shows **the photos the
rule would take, each with where it would go** (*→ 2017\Parties\Weddings\Hervé and Magda's
wedding*), computed by the `classify` engine with your rules and the one typed (nothing is
written, nothing moves); then the photos of those days it leaves to another rule (a screenshot,
a photo of another event), greyed, and said in words above the grid (*30 photos of these days
stay with the rule 'Anniversaire de Tom 2009'*). Seeing them, correct the days
(only 5 August) or the folder, then **Save the rule**: it is written into `config.toml`, above
*Existing folders*, read back from the disk and said. The next `classify` applies it.

**Update a rule…** in the same dialog lists the date rules of `config.toml`, the latest first:
one chosen fills the dialog, and saving replaces it in place (its place in the list, which
decides, is kept). Escape or *Cancel* closes the dialog and shows the search again.

A file the search does not know yet (no words at all: run `mh tags --no-describe` once) is
missing from the grid.

**Sort them now, little by little.** Once you checked them, **I checked: sort these N files**
moves exactly the photos the rule takes, each to the folder shown. To leave some out, pick them
and press **Leave the picked files where they are** (greyed, crossed out). When the photos come
from several folders, they are listed by source folder, one tick box each, a folder you named
after another event unticked. **Once a photo is left out, *Save the rule* is off**: a selection
with exceptions is a move, not a rule (saved, the rule would take them again at every
`classify`); the dialog says how many were left. It asks once (the
count, the folders, the undo line), then writes them as your choices of the latest `classify`
run (`sort-decisions.json`) and runs `sort` cut to those files: journaled, checked at their new
place, said as read back from the disk (*14 moved, 14 checked at their new place (run …):
'mh undo …' puts them back*); the tiles then show their new place. A photo the latest
`classify` run does not know (added since) is left where it is and counted: run `classify`
again. Nothing moves without that GO.

*These folders are mounted read-only*: your `mh` was written before the pages could sort (it
mounts them `:ro`). Type `mh update` once: it writes `mh` again, from your image, with the same
folders.

## Set photos aside

To remove every photo of someone, the [`people`](people.md#remove-every-photo-of-someone) page
does it from their group of faces. To remove those of an event, or any other choice: search them
(`person:"Ann"`, a year, a word), pick them (Ctrl+A, then **Pick all N files found**: every file
the search finds, not only the 240 shown), then Delete or **Set aside the picked files**.

- Nothing is deleted from the page. The choice is saved at once in `decisions.json` of your
  reports, read back from the disk and shown with its count and size: *37 files set aside
  (412 MB), saved in …: 'clean --decisions' moves them to the quarantine, and remembers them: if
  one comes back (a new copy from the phone), the audit proposes it again.* The photos set aside
  carry a red *marked to set aside* label.
- **Take out of the set aside**, shown once a picked file is set aside, takes the files picked
  back out of it.
- When you stop the page, `search` proposes the next step: `mh clean --decisions`. It asks first
  how many files and how many bytes go (apart from the duplicates), moves them to the
  quarantine, journaled; [`undo`](undo.md) brings them back, [`purge`](purge.md) frees the
  space.
- A file changed since you chose it (another size or date) is left where it is and listed in the
  clean report; a file of a protected folder refuses the whole file, as everywhere.
- The same `decisions.json` holds what [`review`](review.md) decided: both are kept, and one
  `clean --decisions` applies them all.

## A wrong name under a photo

A person's name under a photo has a **×**: click it when that person is not on the photo. The
faces of the photo that gave the name go into the person's `rejected` list (in their file under
`/config/people/`, linked from `config.toml`), exactly as the × of the [`people`](people.md) page
does; a face you had confirmed leaves their `faces` too. The file is read back and the bar says
what it holds now (*Saved in config.toml, read back: 1 face of this photo is not Chloé.*), with
**Put back** to undo it. The × never picks the photo, and the card stays where it is. The large
view shows the same names, with the same ×, under its facts (`I`).

`W` in the large view opens **Why this name?**: the face of the
photo cut out, how it got the name (*confirmed by you*, or *close to a face you confirmed*, with
that face, its file, and the score against `[people] similarity`), and the next person when they
come close too. **Yes, it is …** confirms that face, **Not …** takes the name off that face
only; both are saved, read back and said the same way. Esc closes the panel and leaves the large
view open. How to read the score: [People](../reference-people.md#find-them-search).

Only this photo loses the name in this search. Other photos named because they look like a face
you just took out keep theirs until you take it off them too; `classify`, the inventory and the
XMP sidecars read the names again at their next run. Without a writable `/config`, nothing is
saved and the bar says why.

## Put photos in an album

To show photos to others (on the TV with [`slideshow`](slideshow.md)), gather them in an
**album**: a named list, *Crete 2023*, of photos from any folders. Type its name in **Album** (the
albums already made are proposed), pick the photos (or **Pick all N files found**), then **➕ Add
to the album**.

- An album is a list of references, nothing else: no photo is copied, moved or changed. It is
  saved at once in `albums.json` of your reports, next to `decisions.json` (not in the cache:
  deleting the cache keeps your albums), read back from the disk and shown: *Crete 2023: 42
  files, saved in …. Only this file changed: no photo was copied or moved.*
- It is **not** the set aside: *Set aside* prepares a removal, *Add to the album* a share. Neither
  ever touches the other's list.
- **Take out of the album** takes the picked photos out of the album typed; an album left empty
  is removed.
- A photo moved since, by [`sort`](sort.md), by [`undo`](undo.md), or in a folder renamed in the
  Explorer (once an audit has seen it), is found again by its content: the album follows it. One
  found nowhere (deleted, or in the quarantine) stays in the album, listed as missing, until it
  comes back.
- **📺 Share on the TV** gives the command that shows the album typed, copied for you: stop the
  page, then `mh slideshow --album "Crete 2023" --lan` ([`slideshow`](slideshow.md)). To show
  photos once, no album is needed: **📺 On the TV** in the bar (search opened from the home page)
  shows the picked files, or every file found when nothing is picked (at most 3000), and opens
  the remote.
- **📨 Prepare for sending** gives the command that makes the album ready to send by mail:
  resized copies without the GPS position, a folder and a zip, `mh share --album "Crete 2023"`
  ([`share`](share.md)).
- At most 3,000 photos added at once: narrow a search that finds more.

An album can also become a folder of the Explorer: [`album "Crete 2023"`](album.md) makes it, as
second names (hard links), without a copy.

## What you can type

| You type | It finds |
|---|---|
| `Durbuy ours` | The photos with both words, whatever their source. |
| `noel`, `gateau` | `Noël`, `gâteau`: case and accents do not matter. |
| `bougies` | `bougie` too: the words are kept in the singular. |
| `anniv*` | Every word starting so. |
| `"bord de mer"` | The phrase, its words in that order. |
| `place:durbuy` | The word among the places only; also `vision`, `caption`, `folder`, `name` (the file name), `date`, `person`. |
| `anniversaire` | Also `Anniversaire Léa.mp4`: the words of a file name you chose count too (`IMG_1234` gives none). |
| `neige 2008` | The year is a word of the date: the snow of 2008. |
| `Papy dans le jardin` | A sentence: the little words go (`dans`, `le`, the stop words of `[tags]`, as in the index), and a name someone has on a photo is looked for among the people: read as `Papy (person) + jardin`, said under the search. A phrase in quotes is kept as typed. |
| `Chloé montagne` | The photos of Chloé with "montagne" from any source, once her group is named in [`people`](people.md). |
| `person:chloe`, `person:"Mamie Jeanne"` | The name among the people only. A name nobody has yet is said in one line. |
| `un chat sur un canapé` | After [`tags --meaning`](tags.md): the photos that show it first, even without any of these words ([search by meaning](../reference-tags.md#find-a-photo-by-what-it-shows---meaning)). |
| `Chloé cuisine` | After `tags --meaning`: the photos of Chloé only, the kitchens first. |

## Where each word comes from

The *Words of* menu narrows a search to one source; typing its prefix does the same
(`place:durbuy`). A source without any word yet says *— none yet* in the menu and in *How to
write a search*.

| Words of | Prefix | What it holds |
|---|---|---|
| every source | | Any of them (the default). |
| seen by the model | `vision:` | The words the vision model gave to what the photo shows (🤖 [`tags`](tags.md)). |
| the model's sentence | `caption:` | Its whole sentence: for a phrase in quotes. |
| folder | `folder:` | The meaningful words of the folders' names. |
| file name | `name:` | The words of a name someone chose (none for `IMG_1234`). |
| name of a removed copy | `former:` | The folders and name a duplicate had before [`clean`](clean.md) removed it, kept on the copy that stayed. |
| date | `date:` | The year, month, season and holidays of the date taken. |
| place | `place:` | The town and your own places where the photo was taken. |
| person | `person:` | The names given to the faces on the [`people`](people.md) page. |
| Google Photos description | `takeout:` | The description typed in Google Photos (a Takeout export). |

## Tips for finding a photo

While hardly any photo is described, a line under the field says it: *What the photos show is
not known yet: 0 of 44,488 files described…*, with the step that fills it (🤖 `tags`). Before
`tags`, a search finds the words of the folders, names, dates, places and people only.

| Searched | Finds nothing because | Try instead |
|---|---|---|
| `an old man` | **Every word must be found**: `an` and `old` and `man`; a small word counts too. | `man`, then fewer words. |
| `old man`, `grandmother`, `woman` | **The model never writes an age, a sex or a relationship**: for people it writes *adult*, *child*, *baby* or *group* only. | `person:` and the person's name (named on the [`people`](people.md) page), or `adult`. |
| `an old man in a garden` | **A whole sentence needs search by meaning** (`tags --meaning`); without it, words only. | `garden`; or run 🤖 `tags --meaning` once: then sentences work. |
| `beach` during a `tags` run | **The model's words reach the search at the end of the run** (or after one Ctrl+C, which writes those of the photos described so far). | Wait for the end of `tags`, or Ctrl+C once. |

Nothing found? Fewer words, the start of a word (`anniv*`), another source in *Words of*, or
search by meaning. The page keeps these tips short, in *How to write a search*.

## Options

| Option | What it does |
|---|---|
| `WORDS` | Words to find, printed as a table instead of opening the page. |
| `--limit N` | With words: how many files the table lists at most (20 by default). |
| `--folder FOLDER` | Without words: the page opens on this folder, as *Path contains* takes it (a folder `status` lists as left to sort). |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- **During a `tags` run**, a photo described a moment ago shows at a search about 20 seconds later
  (the page reads the new words at most that often while the model writes; a move made from the
  page itself shows at once).
- **Opened from the home page** (`mh` alone): the page opens at once, in the same tab, served by
  the home page itself: no other container starts, the index stays open for the session.
  *⌂ Back to the home page* is a plain link (the browser's Back works too). Typed alone
  (`mh search`), it still starts its own page.
- Without `/reports` (or with a folder the tool cannot write to), **Set aside the picked files** says why and
  saves nothing; the search itself works.
- The search reads the cache only: run [`audit`](audit.md) then [`tags`](tags.md) again to find
  the new photos.
- Without `/cache`, or with a cache no audit has filled yet, it stops and says why.
- **By meaning**: once [`tags --meaning`](tags.md) gave the photos their vectors, the search
  ranks them by what they show too, and says so at start (*Search by meaning: 52,318 photos can
  be found by what they show.*). The model is read from the cache, never downloaded by `search`.
- The names of the people come from the faces of the cache and the names of `config.toml`, at
  each start: mount `/config` too to find them. Nothing else to run after naming a group.

## Go further

- [Find in short](../find/quick-guide.md)
- [Tags: find a photo by its words](../reference-tags.md#find-a-photo-by-its-words-search)

## The built-in help

<details>
<summary><code>search --help</code></summary>

<!-- capture: help-search.txt -->
```text
 Usage: media-hygiene search [OPTIONS] [words]...

 🔒 Read-only: never changes your photos. Find photos by their words in your
 browser (or as a table): the words 'tags' gave them.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   words      <str>  Words to find, printed as a table instead of opening the │
│                     page: "bord de mer" a phrase, anniv* a start of word,    │
│                     place:durbuy among the places only (also vision,         │
│                     caption, folder, name, date, person).                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --limit          <int range> [x>=1]  How many files the table lists at most. │
│                                      Default: 20.                            │
│ --port           <int range> [x>=1]  Port of the page. docker run publishes  │
│                                      it under the same number on your        │
│                                      computer: -p 127.0.0.1:9000:9000 for    │
│                                      --port 9000. Default:  port in          │
│                                      config.toml, 8088.                      │
│ --help   -h                          Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
