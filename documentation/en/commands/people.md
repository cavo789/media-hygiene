# `people`: find the faces, group those alike, name them

[Documentation](../README.md) › [Commands](../reference-commands.md) › `people` · 🇫🇷 [Français](../../fr/commands/people.md)

## In short

**Find the photos of someone by their name, and file them by who is on them, without a single
face leaving your computer.**

`people` finds the **faces** in your photos, groups those that look alike (probably one person
per group), and shows the groups in your browser, largest first, where you **name** them. Then
`search Chloé` finds the photos of Chloé, and a `person` rule of [`classify`](classify.md) files
them. The faces stay in the [cache](../reference-glossary.md#cache), never sent anywhere; the names go into your `config.toml`.

**When**: after an audit run with the cache, or right after it with `audit --people`; again
after new photos: only those are analysed. From the home page, past the first run, the page
opens at once on the groups already known and analyses up to 1 000 new photos itself, with
their progress and a Stop button; the groups are kept in the cache and not recomputed.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders, `/cache` (writable: the faces are kept there), `/config` (writable, to save the names) and `-p 127.0.0.1:8088:8088`. |
| Writes | The faces and the two face models (39 MB, once), in the cache; the names, in `config.toml`; the photos you set aside, in `decisions.json` of `/reports`. |
| Undo | `people --forget` deletes every face from the cache, then asks whether the names go too. |
| With `mh` | `mh people`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people
```

With WSL or Linux:

```bash
docker run --rm -it -p 127.0.0.1:8088:8088 \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v media-hygiene-cache:/cache \
  -v "$HOME/media-hygiene/config:/config" \
  cavo789/media-hygiene people
```

The first run downloads the two face models into the cache, once. Each photo is analysed once;
the next runs analyse only the new ones. Then it prints the groups found, the people already
named, and the address of the page: a click on a face opens its photo. Ctrl+C, or closing its tab, stops it.

<!-- capture: people.txt|re:^✅| -->
```text
✅ 37 photos analysed: 12 faces, 0.04 s per photo.
✅ 17 faces in 47 photos: 3 groups of faces alike, the largest 7, 5, 4; 1 seen
once.
✅ Faces ready, open http://127.0.0.1:8088/ in your browser to name them; each
name is saved at once in config.toml. Ctrl+C stops it; the photos are not
changed.
💡 The page does not open? docker run must publish the same port on both sides:
-p 127.0.0.1:8088:8088.

✅ Page stopped; nothing was changed.
```

### From the home page

On the home page (`mh`), the **In this page** button next to `people` scans the faces without
the console. It first counts the photos whose faces the cache lacks and the time it should take
(an estimate until a run has measured your computer), then asks: **Scan now**, **Scan for 1 h**
(it stops by itself) or **Not now**. While it runs, the page shows the photos scanned, the rate,
the time left and the faces of the last photo; **Stop after this photo** ends it, and the next
scan goes on where it stopped (each photo's faces are kept in the cache at once). The people
page then shows the groups. Only the cache is written: your photos are not changed.

Once every face is found, the `people` step itself opens the groups **in the home page's own
server** (`/people/`): no wait, the home page keeps running. With faces still to find, the step
runs in the window of `mh` as before (its progress bar, then the page).

## Name the groups

On the page, type a name on a group and press Enter: the name is saved into `config.toml`, read
back and shown. `x` picks several groups to name at once, × takes a wrong face out, `i` ignores
a group of strangers. Each person then shows twice at most: **Chloé ✓ verified**, the faces you
confirmed, and **Chloé attributed**, the faces given to her because they look like those; `y`
confirms the attributed faces shown, which move to verified. The next runs keep every name, and
[`library`](library.md) finds the people by name: `search Chloé montagne`, `search person:chloe`.
The names follow the photos [`sort`](sort.md) moves (and `undo` moves back); `config.toml` is
updated the next time the page saves a name.
Each name is a `[[people.person]]` entry of `config.toml`. Details:
[People](../reference-people.md#name-the-groups).

Each title folds or unfolds its section (click it, or `o`). The **verified** sections, already
done, come folded: one line with the name, ✓, the counts and a strip of a few faces, so that the
work left stands first; their faces are loaded only when you open them. The page remembers in
this browser what you folded, person by person; Enter on a folded section opens it, then goes
to its name field.

The people come in alphabetical order (`Chloé` with `chloe`), each verified then attributed,
then the unnamed groups, largest first: each name given there names the most faces. On a wide
screen, a column lists the people with their counts (✓ verified, attributed still to confirm,
in bold while some are left), and last **Unnamed groups (n)**; on a phone, the field **Go to a
person** of the top bar holds the same list. Type a few letters (`/` reaches the field), pick a
name: the page goes to their sections and opens them; **Show only this person** hides the
others until Esc. The page has the layout of every page of the tool: the
list on the left with the ⌨ keys under it, one bar on top of the sections (what is left, **Next
to do**, the field, the line read back from the disk, **✅ Apply**). The person chosen stays in
the address: a reload or a bookmark comes back to them.

The top bar says what is left, read back from the server after each change: *To do: 312
attributed faces (7 people) · 41 unnamed groups (980 faces)*. **Next to do** (`g`) goes to the
next attributed section, then to the next unnamed group, and focuses its button; after `y`, the
page moves on by itself, so `y`, `y`, `y` goes through the work. **Only what is left** hides
the verified sections (the people list still reaches them).

An unnamed group that looks like the faces you confirmed for someone says so: **It is Papy?
(0.42)**, two names for siblings. A click (or `y`) names the group so, as typing the name would;
a face you took out of someone never counts for them. The figure is the likeness, from 0 to 1:
a hint shown from 0.30, below the `[people] similarity` that attributes faces.

## Remove every photo of someone

To forget someone (a former partner, say), remove the photos they are on from the group itself:

1. Click **and N more faces**: the page shows every face of the group, not only the few dozen of
   the sample. Take out with × each face that is someone else's: its photo stays.
2. Click **Set aside their N photos**. The button waits until every face is shown. Every photo
   this person is on goes, with others or not. Nothing is deleted from the page: the choice is
   saved at once in `decisions.json` of your reports (`/reports`, mounted by `mh`), read back and
   shown with its count and size. The photos set aside then leave the page: not shown, not
   counted, never confirmed with the others. Their section says *N photos set aside, hidden*:
   **Show** draws them again, dimmed, each with ↺ to take that one back; **Take out of the set
   aside** takes them all back. The same goes for photos set aside on any other page
   ([`library`](library.md)), until `clean --decisions` moves them.
3. Opened from the home page (`mh`), **Apply now** runs [`clean --decisions`](clean.md), which
   asks first; served by the home page, the page stays open and offers **↶ Undo** of that run once
   it ended, the files then looked for where they were. Otherwise, the command proposes it when you
   stop the page. It moves the photos to the quarantine, journaled; [`undo`](undo.md) puts them
   back, [`purge`](purge.md) frees the space.

**The page remembers the person.** Setting aside the photos of a group keeps their faces in the
cache, without a name and without the photos (nothing goes into `config.toml`). Each time the
page opens, the photos that look like that person come first, in a section of their own: *N
other photos look like the person you set aside on <date>*, the faces of no group included (too
small, too blurry, seen once). They are shown for you to check, never set aside on their own:
take out with × the faces of someone else, then **Set these N photos aside too**. A photo added
later shows there at the next opening. The faces are kept after `clean` and `purge`; taking the
photos back (↺, **Take out of the set aside**, or `undo`) forgets them, and `people --forget`
forgets them with every other face.

**One photo at a time.** A face the tool cannot see (in profile, blurred, a tilted photo) leaves
its photo in someone else's section. Click the face: the large view shows the photo with **Set
this photo aside** (or the Delete key); the view then shows the previous face (the next one at the start). Backspace takes it back. It is the same large view as
in `library`: ← → go through the faces of the section, F full screen, I the photo's path, ? every
key; Esc, a click beside the photo or the browser's Back closes it.

The same `decisions.json` keeps what [`library`](library.md#set-photos-aside) and
[`review`](review.md) set aside: one `clean --decisions` applies everything. A photo changed
since you chose it is left in place.

## From any photo: name or set aside someone

A photo shows someone the people page never asked you about ("this is Aunt Juliette"), or
someone you never want to see again, on any page (`review`, `library`): **👤 Identify someone**
under a shot of `review` or in the large view of `library` opens the page *Identify someone* in
a new tab, on that photo. You can
also open it from the people page (**👤 Name someone from a photo**, under the list of people),
from the home page (*Find*, *Name someone from a photo*), or from the console:
[`mh person C:\Photos\…\IMG_1234.jpg`](person.md); on the page, paste the path of a photo.

**Who is on this photo, at a glance**: in the large view of every page (`library`, `review`…),
a line under the photo says who is on it, from the index: **👤 ✓ Chloé · ≈ Paul · ? not named**
(asked only when you open a photo large). A click on **? not named** opens the page on that
photo, its naming line on that face. No line: no face found there by `audit --people`.

1. The page shows the faces found on that photo by `audit --people`, each with its name:
   **✓ Chloé** (confirmed by you), **≈ Chloé** (given by the tool because it looks like her
   confirmed faces) or **? not named**. Click the right one (one face alone is taken at once).
   Under the faces, **This face is… [name]** (or *Not Chloé, this face is…*): type a name or
   pick one in the list, Enter. It is saved in `config.toml` as a confirmed face, read back and
   shown (*Saved in config.toml, read back: Juliette, 1 confirmed face*); a new name creates the
   person, an existing one adds to them. When the tool guessed names (≈), **✓ Confirm the names
   guessed: N** confirms them all in one click, as they are shown.
2. On the right, the photos of that person, the closest first, as a grid to pick like in
   [the folders of `library`](library.md#walk-through-your-folders): click, Ctrl, Shift, rectangle, Ctrl+A, I, Delete, the large view and
   its keys. If they look like someone you set aside before, the bar says so (*the person set
   aside on <date>*): what you set aside now joins that person. Each photo shows, in its corner,
   the face that matched, and under it its name (✓, ≈ or ?).
   Once the face is named, a line above the grid says what to do: *① Tick the photos where it
   really is Juliette (Ctrl+A ticks them all; × when it is not them) ② then:* **These are
   Juliette: N**, which confirms the photos you ticked, N stated (until one is ticked, it reads
   *Tick their photos in the grid, then confirm them here*). **Show** picks the photos
   by the name of the face that matched: *To confirm (≈ and ?)* (the default: only the work
   left), *All the photos*, *✓ Confirmed as this person*, *≈ Guessed as this person*, *? Not
   named*, *Someone else* (a face that looks like them but is named another person). The
   status line counts the photos hidden; Ctrl+A and the buttons act on the photos shown only.
   **S M L XL** in the bar sets the size of the photos (XL to tell small children apart: the
   face that matched grows too), and **◀ Hide the panel** gives the whole width to the grid;
   both are kept in this browser. When a photo's folder or file name holds the name of a
   person you named (*Avril 2004 - Manon 5 mois*, *Petite Manon.png*; whole words, without case
   or accents), its tile says **📁 Manon**, in red when it names someone else than the face's
   name. A hint only: nothing is named from it. **Show** keeps *📁 The folder or file name
   names this person* (open the page from a photo of Manon, then Ctrl+A and **These are
   Manon: N**) or *… names someone else* (the look-alikes to check first).
   Only the ticked photos are confirmed; the photos not ticked, or not shown, stay undecided. A photo whose face you
   confirmed as someone else is left out (the button's tooltip counts them): move it on the people
   page. The **×** of a photo says *not Juliette*: saved in `config.toml`, read back, the photo
   leaves the search for good, and the photos found again leave that face out of their likeness. Before the face is named, × only drops the photo from this search.
   The confirmed faces make the person show on the people page, which then gives her other
   groups that look like her, as for any name.
3. Delete (or **🗑 Put aside**) saves them at once in `decisions.json`, read back
   and shown, and remembers the face, as [above](#remove-every-photo-of-someone): the people
   page will show the photos that look like it. Opened from a page `mh` opened from the home
   page, **Apply now** in the bar runs `clean --decisions` like on that page.
4. **📚 Album ▾** in the bar adds the photos picked to an album, and, the page served by the home
   page, **▶ Slideshow ▾** shows them on this PC or on the TV (nothing picked: every photo of the
   grid), as in [`library`](library.md).
5. A photo of the grid shows the person from another angle? Its **👤** (next to its name, or in
   its large view) opens the page again on that photo, in a new tab.

**No face on the photo?** A face tilted, lying on its side or blurred is often missed by the
audit, which looks at each photo upright. **Look again, slower** looks at that one photo turned
(up to 90° each way) and less strictly; what it finds is shown to choose from, never stored.
Measured on 9 real photos of one person missed by the audit: 6 found, 1 just at the limit, 2
not (very blurred). Still nothing, though you see the face? **✏ Draw a face the tool missed**
shows the photo: drag a box around the face. The tool looks for it in that box, enlarged, or
takes the box itself; the face is then kept in the index like a face found (flagged *drawn*, so
a new audit keeps it), named and searched like the others. A face even smaller or more blurred
than the people page shows can be drawn: it is kept for the search, not shown on the people
page. Too small or too blurred to find anyone (under 20 pixels, or nearly no detail), the page
says so and writes nothing; a box on an empty area writes nothing either. When nothing is
found, set the photo aside on its own (Delete in its large view).

## Options

| Option | What it does |
|---|---|
| `--path PATH` | Only the photos below this folder (host path, as you mounted it); repeat it for several. |
| `--sample N` | Analyse N random photos, print the time per photo and the estimate of a full run, and stop. |
| `--forget` | Delete every face from the cache, then show that none is left; asks before deleting the names of `config.toml` too. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Your privacy

The numbers that describe a face are **biometric data**. They stay in the cache, never in your
photos nor in the reports; the page is served on `127.0.0.1` only and cuts the faces out of the
photos on request, never saved. The only network access is the one-time download of the two
models from OpenCV Zoo, checked by their SHA-256: it sends nothing about your photos.

## Good to know

- The settings `[people]` (`similarity`, `min_face`, `min_sharpness`) change the grouping, and
  the faces too small or too blurry for the page are named by nobody anywhere (`library`,
  `classify`, XMP), unless you confirmed them: nothing is analysed again.
- `audit --people` looks for the faces right after an audit, once you agreed to the time it
  takes; `with_audit = true` in `[people]` does it at every audit.
- Videos are not analysed yet.
- Without network, the error names the two model files to save by hand into the `models` folder
  of the cache.

## Go further

- [Find in short](../find/quick-guide.md)
- [People](../reference-people.md): how it works, naming, the settings, what comes next.
- [Sorting, step 10: sort by person](../sort/10-sort-by-person.md): from the named groups to
  sorted folders.

## The built-in help

<details>
<summary><code>people --help</code></summary>

<!-- capture: help-people.txt -->
```text
 Usage: media-hygiene people [OPTIONS]

 🔒 Read-only: never changes your photos. Find the faces in the photos, group
 those alike and name them in your browser. Faces kept in the cache, never sent
 anywhere.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path            <str>               Only the photos below this folder      │
│                                       (host path, as you mounted it); repeat │
│                                       it for several. Default: every photo   │
│                                       of the index.                          │
│ --sample          <int range> [x>=0]  Analyse this many random photos, print │
│                                       the time per photo and the estimate of │
│                                       a full run, and stop.                  │
│ --forget                              Delete every face from the cache, then │
│                                       show that none is left; asks before    │
│                                       deleting the names of config.toml too. │
│ --port            <int range> [x>=1]  Port of the page. docker run publishes │
│                                       it under the same number on your       │
│                                       computer: -p 127.0.0.1:9000:9000 for   │
│                                       --port 9000. Default:  port in         │
│                                       config.toml, 8088.                     │
│ --help    -h                          Show this message and exit.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
