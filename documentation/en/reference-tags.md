# Tags

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-tags.md)

`tags` gives every photo and video **words to find it by**: "Durbuy", "bear", "birthday",
"Christmas", "snow". It reads what the audits learnt, from the cache: run an
[audit](start/01-first-audit.md) first, with `/cache` mounted
([step 2](start/02-keep-the-cache.md)). The words stay **in the cache**, never in your photos.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene tags
```

```text
🔒 Read-only: your photos and videos are not touched.
✅ 52,318 files: 241,906 words from their folders, dates and places.
💡 Set [classify.ai] model to a local vision model (Ollama) to add what the photos show: they
are sent to its url, and only there.
```

Then [`search`](#find-a-photo-by-its-words-search) finds the photos by these words in your
browser, and [`inventory`](reference-inventory.md) lists them in its last column, **Tags**.
[`xmp`](#carry-the-words-with-the-photos-xmp) writes them into `.xmp` sidecars that other
applications read.

## Where the words come from

| Source | Words | Cost |
|---|---|---|
| Folders | The words of the folder names you chose: `2022/Durbuy - ours` gives `Durbuy`, `ours`. Folders named by a device or an app (`DCIM`, `100CANON`, `Camera`), dates (`2019`, `Juillet 2019`) and small linking words (`les`, `the`) are left out, as for [the kept copy](clean/05-choose-the-kept-copy.md). | Seconds |
| Date | The year, the month, the season (turned around below the equator), the holidays (Christmas, New Year, Saint Nicholas, Valentine's Day, Halloween, Easter) and the names of your own `calendar` and `date_range` rules ([sorting, step 6](sort/06-write-down-what-you-know.md#dates)). A photo without a date takes the year of its folder (`Avril 2007`). | Seconds |
| Place | The name of your place when the GPS position lies in one ([sorting, step 9](sort/09-places-from-gps.md)), then the nearest town and its country, offline (GeoNames), when it lies within `town_km` (20 km). | Seconds |
| Vision model | A short sentence and 5 to 10 words about what the photo shows (optional, below). | About 2 s per photo |

These words are computed again at every run: rename a folder or add a rule, run `tags` again.

## The words of a local vision model

A vision model sees **scenes and objects** well (a wedding cake, candles, a snowman, an ice rink,
a cathedral) and reads visible text. It never knows the **occasion** (Easter, Christmas) nor the
**place** (Durbuy, Sicily): that is why the folders, dates and places come first, and the model
only adds to them.

It is the model of [sorting, step 8](sort/08-subjects-from-a-local-model.md): install it, then
set it in `config.toml`.

```toml
[classify.ai]
url = "http://host.docker.internal:11434"
model = "qwen2.5vl:7b"
```

On Docker Engine (Linux, WSL), add `--add-host=host.docker.internal:host-gateway` to
`docker run`. Without a `model`, `tags` never sends anything.

- **Privacy**: each photo is sent, as a 768-pixel JPEG, to the `url` of `[classify.ai]`, and only
  there. Keep that server on your own computer.
- **One photo per set**: identical copies share their words, and a burst series takes those of
  its sharpest shot. Videos, and photos smaller than `min_edge` (512 pixels), are not sent.
- **Newest first**: the first night already covers your recent years.
- **What it is asked**: one sentence and 5 to 10 words, in the language of `[tags] language`
  (the interface's by default); people as adult, child, baby or group, never a relationship
  ("mother", "sister") nor a name.
- **Cleaned words**: lower case, singular (`bougies` → `bougie`), each once; words of one or two
  letters and words that fit every photo (`sol`, `mur`, `floor`, `wall`: `[tags] stop_words`)
  are left out.

### Measure first: `--sample`

```powershell
docker run --rm -it ... cavo789/media-hygiene tags --sample 20
```

It describes 20 random photos, prints their sentence, their words and their time, and the
estimate of a full run. Their answers are kept: the full run does not describe them again.

### The long run

**How long**: about 2 seconds per photo on one graphics card with a 27-billion-parameter model,
so about 30 hours for 50,000 photos, less once copies and burst series are counted once. Above
`confirm_above` photos (200), `tags` prints the count and the time and asks first; `--yes` does
not ask.

**The graphics card to itself**: when another program uses the same card (another model in
Ollama), Ollama swaps the models and a photo can take 10 to 30 seconds. Let the run have the card
alone, for example at night.

**Stop whenever you want**: Ctrl+C lets the photos being described finish. Each answer is kept at
once: the next `tags` run goes on where this one stopped. `tags --no-describe` asks the model
nothing new: the words of the folders, dates and places, and the answers already in the cache.

### One folder first: `--path`

```powershell
docker run --rm -it ... cavo789/media-hygiene tags --path "C:\Photos\2022"
```

Only the photos below that folder (repeat `--path` for several).

## Find a photo by its words: `search`

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene search
```

Open <http://127.0.0.1:8088/>: one field, a grid of the photos found, best first, each with its
folder, date and words. Type `/` to search again, move with the arrows, Enter shows the picture
large (with a link to the original), Escape closes it. Filters: years, a part of the path, the
words of one source only. Ctrl+C stops the page. Read-only 🔒: it never changes a file; only
the small previews of the grid are kept in `/cache`.

| You type | It finds |
|---|---|
| `Durbuy ours` | The photos with both words, whatever their source. |
| `noel`, `gateau` | `Noël`, `gâteau`: case and accents do not matter. |
| `bougies` | `bougie` too: the tags are kept in the singular. |
| `anniv*` | Every word starting so: `anniversaire`, `anniv`. |
| `"bord de mer"` | The phrase, its words in that order. |
| `place:durbuy` | The word among the places only; also `vision`, `caption` (the model's sentence), `folder`, `date`. |
| `neige 2008` | The year is a word of the date: the snow of 2008. |

Without a browser (WSL, a script), give the words: `search durbuy ours` prints the first 20
files as a table (`--limit N` for more). The search reads the cache only: run `tags` again after
an audit to find the new photos.

## Carry the words with the photos: `xmp`

The words live in the cache of this tool. To find them in digiKam, darktable, Lightroom or
Immich (an external library), `xmp` writes them into **sidecars**, small `.xmp` files next to
the photos: the photos themselves are never changed.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene xmp --apply
```

Without `--apply`, `xmp` only shows what it would write (the photo folders may then stay
`:ro`). With it, the folders must be writable and `/journal` mounted, like `clean`.

- **What is written**: the words of the sources in `xmp_sources` (`vision` and `place` by
  default: the folder and date words are in the path already) into `dc:subject`, the model's
  sentence into `dc:description`.
- **The place apart**: with `place` in `xmp_sources`, the town also goes into `photoshop:City`,
  its country into `photoshop:Country` and your first personal place (`[[classify.places]]`)
  into `Iptc4xmpCore:Location`, the fields digiKam, Lightroom and Immich show apart from the
  keywords. A field another application filled keeps its value; a field you emptied there is not
  filled again. After an update, run `tags` once more: the places found before do not know yet
  whether they are a town or a country, and fill these fields only then.
- **Where**: `IMG_1.jpg.xmp` next to `IMG_1.jpg`. A sidecar already there (`IMG_1.jpg.xmp`, or
  `IMG_1.xmp` when it belongs to that photo alone) is completed, never replaced: its edits, its
  other properties and its own words stay; the sentence is only set when it has none. A sidecar
  that is not readable XMP is listed and left as is.
- **Run it again** after `tags`: the words this tool wrote and no longer gives are taken back, a
  word you removed in another application is not added again, and a sidecar already up to date is
  not written.
- **Left out**: protected folders (never written), and files with an identical copy: two copies
  would get diverging sidecars, so run `clean` first and only the copy kept gets one.
- **Safe**: each sidecar is journaled before it is written, written to a temporary file then
  renamed (never over a file that appeared meanwhile), read back and checked. A sidecar of
  another application is first copied into the quarantine. `undo <run>` removes the sidecars this
  tool created and puts the others back byte for byte, unless one was edited since: then it is
  kept, and `undo` says why.
- **Copy kept**: a sidecar written by `xmp` alone does not count as edits when `clean` chooses
  which copy to keep ([sidecars](reference-sidecars.md)).

## Settings

```toml
[tags]
language = ""   # "en", "fr", or empty for the language of the interface
# stop_words = ["sol", "mur", "intérieur", "floor", "wall", "indoor"]
town_km = 20
xmp_sources = ["vision", "place"]   # the words written into the .xmp sidecars
```

A list of `stop_words` written here replaces the built-in one. The model itself is set in
`[classify.ai]` (model, url, `min_edge`, `confirm_above`).

## Why not inside the photos

Writing the words into a JPEG changes its bytes: its fingerprint, its date, and two identical
copies would stop being identical when only one is tagged. That would break what this tool is
built on, and risk the originals. The words stay in the cache, where `search` and `inventory`
read them, and go into sidecars next to the photos only when you ask (`xmp`).
