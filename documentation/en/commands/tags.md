# `tags`: words to find every photo by

[Documentation](../README.md) › [Commands](../reference-commands.md) › `tags` · 🇫🇷 [Français](../../fr/commands/tags.md)

## In short

**Give every photo and video words you can search for (its folders, name, date, place, what it
shows), without touching the files.**

`tags` gives every photo and video **words to find it by**: the meaningful words of its folders
("Durbuy", "bear") and of its name, its date (year, month, season, holidays), its place, and, if
you wish, what a local [vision model](../reference-glossary.md#vision-model) sees ("cake", "candles", "snow"). The words stay **in the
cache**, never in your photos; [`search`](search.md) finds them, [`xmp`](xmp.md) writes them
into [sidecars](../reference-glossary.md#sidecar).

**When**: after an audit run with the cache; again after new photos or a renamed folder.

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene tags
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | `/cache`, filled by an earlier [`audit`](audit.md). |
| Recommended | Your folders (needed for the vision model, which reads the photos), `/config` (the model, `[tags]`). |
| Writes | The words, in the cache. |
| Undo | Nothing to undo; run it again after renaming a folder or adding a rule. |
| With `mh` | `mh tags`. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene tags
```

Without a vision model, it takes seconds: *✅ 52,318 files: 241,906 words from their folders,
names, dates and places.*

## Where the words come from

| Source | Words | Cost |
|---|---|---|
| Folders | The words of the folder names you chose (`2022/Durbuy - ours` gives `Durbuy`, `ours`); device folders, dates and small linking words are left out. | Seconds |
| File name | The words of a name you chose (`Anniversaire Léa.mp4` gives `Anniversaire`, `Léa`); names a camera or an app gave (`IMG_1234`, `VID-20190712-WA0001`), numbers and dates give nothing. | Seconds |
| Date | Year, month, season, holidays, and the names of your `calendar` and `date_range` rules. | Seconds |
| Place | Your place when the GPS position lies in one, then the nearest town and its country, offline. | Seconds |
| Vision model | A sentence and 5 to 10 words about what the photo shows (optional). | About 2 s per photo |

## Options

| Option | What it does |
|---|---|
| `--path PATH` | Only the photos below this folder (host path, as you mounted it); repeat it for several. |
| 🤖 `--sample N` | **With a local AI only.** Describe N random photos with the model, print their words, the time per photo and the estimate of a full run, and stop. |
| 🤖 `--no-describe` | **With a local AI only.** Ask the model nothing new: the words of the folders, names, dates and places, and the descriptions already in the cache. |
| 🤖 `--yes`, `-y` | **With a local AI only.** Describe the photos without asking, however many (above 200, it asks first). |
| 🤖 `--meaning` | A model on this computer's processor (CLIP: no Ollama, no GPU, nothing sent) looks at each photo once, about 1 minute per 1,000 photos, so that [`search`](search.md) finds what a photo shows ([search by meaning](../reference-tags.md#find-a-photo-by-what-it-shows---meaning)). The model (894 MB) is downloaded into the cache the first time. Default: `[tags] meaning`. |

## Good to know

- **Searchable as the run goes**: each photo described writes its words at once, with those of
  its identical copies, its burst series and its near group. A search open during a run of hours
  finds them (within about 20 seconds); a run stopped, or a window closed, loses no word already
  written.
- **The vision model** is the one of `[classify.ai]` (`model`, `url`): each photo is sent there,
  as a 768-pixel JPEG, and only there. Keep that server on your own computer. Without a `model`,
  nothing is ever sent.
- **One photo per set**: identical copies share their words, a burst takes those of its sharpest
  shot; a video is seen by the frame in its middle; small pictures and videos are not sent.
  `classify` then reuses these answers instead of sending the photos again.
- **Search by meaning** (`--meaning`, opt-in): what a photo shows, never who nor where (names
  come from `people`, places from the GPS); identical copies are looked at once, videos never.
- **Stop whenever you want**: Ctrl+C lets the photos being described finish; the next run goes on
  where this one stopped.
- **Why not inside the photos?** Writing into a JPEG changes its bytes, its fingerprint, and two
  identical copies would stop being identical. [`xmp`](xmp.md) writes sidecars instead.

## Go further

- [Find in short](../find/quick-guide.md)
- [Tags](../reference-tags.md): every source, the settings, the long run.
- [Sorting, step 8: a local vision model](../sort/08-subjects-from-a-local-model.md)
- Next: [`search`](search.md), [`xmp`](xmp.md), [`inventory`](inventory.md).

## The built-in help

<details>
<summary><code>tags --help</code></summary>

<!-- capture: help-tags.txt -->
```text
 Usage: media-hygiene tags [OPTIONS]

 🔒 Read-only: never changes your photos. Give every photo words to find it by,
 kept in the cache, never in the photos: its folders, name, date and place, and
 what it shows with an optional local AI 🤖

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path             <str>  Only the photos below this folder (host path, as   │
│                           you mounted it); repeat it for several. Default:   │
│                           every file of the index.                           │
│ --meaning                 Also let a model look at each photo on this        │
│                           computer's processor (CLIP, once, about 1 minute   │
│                           per 1,000 photos), so that 'search' finds what a   │
│                           photo shows. Default:  meaning.                    │
│ --help     -h             Show this message and exit.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🤖 Local AI (Ollama), optional: a model set in config.toml ─────────────────╮
│ --sample               <int range> [x>=0]  Describe this many random photos  │
│                                            with the local model, print the   │
│                                            time per photo and the estimate   │
│                                            of a full run, and stop.          │
│ --no-describe                              Ask the local model nothing new:  │
│                                            the words of the folders, names,  │
│                                            dates and places only, and the    │
│                                            descriptions already in the       │
│                                            cache.                            │
│ --yes          -y                          Describe the photos without       │
│                                            asking, however many.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
