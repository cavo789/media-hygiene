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
| Your photos | 🔒 Never changed: mount them `:ro`. |
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
column, the ⌨ keys under them, one bar above the grid, then the photos found. **📁 Folders**
opens `browse`, the same server. Ctrl+C, or closing its tab, stops the page.

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
- **Look**: Enter or a double click shows the photo large (with a link to the original); ← → the
  previous or next one, Delete sets it aside then shows the next one, F full screen, ? every key,
  Escape closes it. **👤 Set a person aside** finds every photo of someone on the one shown
  ([`people`](people.md#from-any-page-set-a-person-aside)).

- **A period**: *From* and *To* are calendars, a day each, both included; one alone is a period
  of one day. The day is the one the photo was taken, as `classify` dates it.

Without a browser (WSL, a script), give the words: `search durbuy ours` prints the first 20 files
as a table.

## Make a period a rule

Once a period is searched, **📌 Make it a rule** opens, beside the grid, the dialog of
[`review-sort`](review-sort.md)'s *Remember as a rule*, filled with the period: type its name
and its folder (*keep my folders below it* is on). As you type, the grid shows **the photos the
rule would take, each with where it would go** (*→ 2017\Parties\Weddings\Hervé and Magda's
wedding*), computed by the `classify` engine with your rules and the one typed (nothing is
written, nothing moves); then the photos of those days it leaves to another rule (a screenshot,
a photo of another event), greyed, with the rule that keeps them. Seeing them, correct the days
(only 5 August) or the folder, then **Save the rule**: it is written into `config.toml`, above
*Existing folders*, read back from the disk and said. The next `classify` applies it.

**Update a rule…** in the same dialog lists the date rules of `config.toml`, the latest first:
one chosen fills the dialog, and saving replaces it in place (its place in the list, which
decides, is kept). Escape or *Cancel* closes the dialog and shows the search again.

A file the search does not know yet (no words at all: run `mh tags --no-describe` once) is
missing from the grid.

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
  page, then `mh slideshow --album "Crete 2023" --lan` ([`slideshow`](slideshow.md)).
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
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

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
