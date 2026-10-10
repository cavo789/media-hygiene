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

Then [`inventory`](reference-inventory.md) lists them in its last column, **Tags**. A search page
and portable `.xmp` files will build on them next.

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

## Settings

```toml
[tags]
language = ""   # "en", "fr", or empty for the language of the interface
# stop_words = ["sol", "mur", "intérieur", "floor", "wall", "indoor"]
town_km = 20
```

A list of `stop_words` written here replaces the built-in one. The model itself is set in
`[classify.ai]` (model, url, `min_edge`, `confirm_above`).

## Why not inside the photos

Writing the words into a JPEG changes its bytes: its fingerprint, its date, and two identical
copies would stop being identical when only one is tagged. That would break what this tool is
built on, and risk the originals. The words stay in the cache, where `inventory` reads them.
