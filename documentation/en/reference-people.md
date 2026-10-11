# People

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-people.md)

`people` finds the **faces** in your photos, groups those that look alike, and shows the groups
in your browser: probably one person per group. It reads the photos the audits listed, from the
cache: run an [audit](start/01-first-audit.md) first, with `/cache` mounted
([step 2](start/02-keep-the-cache.md)). The faces stay **in the cache**, on your computer.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  -p 127.0.0.1:8088:8088 `
  cavo789/media-hygiene people
```

```text
🔒 Read-only: your photos and videos are not touched.
🔒 Faces are personal data: they stay in the cache (/cache), nothing is sent anywhere.
'people --forget' deletes them all.
Downloading the two face models into the cache, once (39 MB): they run on this computer,
nothing about your photos is sent.
2,000 photos of 2,000 to analyse; the next runs analyse new ones only.
✅ 2,000 photos analysed: 1,436 faces, 0.21 s per photo.
✅ 1,436 faces in 2,000 photos: 37 groups of faces alike, the largest 212, 140, 96, 51, 33; 288
seen once.
Left out: 301 faces smaller than 40 pixels, 64 blurrier than 30.
✅ Named: Chloé: 412 photos, Manon: 236 photos.
✅ Faces ready, open http://127.0.0.1:8088/ in your browser to name them; each name is saved at
once in config.toml. Ctrl+C stops it; the photos are not changed.
```

The page shows the people already named first, then the groups, largest first, a few dozen faces
each; a click on a face opens its photo. **Type a name** on a group to name it (below). The
photos are never changed: the names go into your `config.toml` (`/config`). Without `/config`
mounted, the page shows the groups and the names already given, and saves none.

## Name the groups

| On a group | What it does |
|---|---|
| Type a name, then Enter | The faces shown are this person's. The names already given are suggested as you type. A second group named like an existing person **adds** to their faces: a child at every age. |
| Pick (`x`), then name | Name several groups at once: the same person split in two groups. |
| × on a face | This face is not this person: it is taken out of the group, and never given this name again. |
| Ignore (`i`) | Strangers, posters, statues: the group is not shown again, nor the faces close to it. |
| Yes, it is … (`y`) | Confirms a suggestion: a group whose faces come close to someone already named, shown as "Chloé?". |

The keyboard is enough: ↑ ↓ (or `j` `k`) move between groups, Enter types a name. Each change is
written into `config.toml`, then **read back from the file** and shown at the top of the page
("Saved in config.toml, read back: Chloé, 58 confirmed faces."). The names look like this:

```toml
[[people.person]]
name = "Chloé"
faces = [
    "/data/c/Photos/2019/IMG_0412.jpg#0",
    "/data/c/Photos/2023/IMG_7781.jpg#1",
]
```

Each face is written by its photo and its number in it, never by its group: a new grouping (new
photos, another `similarity`) keeps every name. The other faces get the name of the **nearest
confirmed face**, when they look alike enough (`similarity`); below that, they stay unnamed.
Suggestions ("Chloé?") never count until you confirm them.

## Find them: `search`

Once named, people are words of [`search`](commands/search.md), with nothing else to run:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search Chloé montagne
```

`Chloé montagne` finds the photos with Chloé where "montagne" comes from any source (folder,
town, what the vision model saw); `person:chloe` looks among the people only (case and accents
do not matter); `person:"Mamie Jeanne"` is a name of two words. A name nobody has yet is said in
one line: name the group on the page first.

## File them: a `person` rule

Once named, people can also sort the photos: a `person` rule of `classify`
([sorting, step 6](sort/06-write-down-what-you-know.md#people)) gives a category to the events
where someone shows.

```toml
[[classify.rules]]
name = "With Chloé"
match = "person"
names = ["Chloé"]
category = "People/Chloé"
```

An event goes to the rule when at least **10 %** of its photos show Chloé (`min_share = 10`:
she may be the one taking the pictures); a photo outside any event goes when it shows her.
`names = ["Chloé", "Manon"]` takes the events with either of them; add `all = true` for those
with both. The names are those of the page: the faces confirmed, and the faces close enough to
them, as `search` finds them; suggestions do not count. A name nobody has yet stops `classify`
before anything is read, and names the rule.

## During the audit: `audit --people`

`audit --people` runs the audit, then counts the photos not looked at for faces yet, measures a
few of them on your computer, says how long the rest takes, and **asks** before going on.
`--yes` does not ask; without a terminal (no `-it`), nothing waits: the audit ends without faces.
No page opens: run `people` afterwards to see the groups. `[people] with_audit = true` does it
at every audit.

## How it works

| Step | What happens | Where |
|---|---|---|
| Find | YuNet (OpenCV Zoo, MIT licence) finds each face: a box and five points (eyes, nose, mouth). | Your computer |
| Describe | SFace (OpenCV Zoo, Apache 2.0 licence) turns each face, set upright, into 128 numbers: close numbers, probably the same person. | Your computer |
| Group | Faces whose numbers are close enough are grouped, again at every run, in seconds: a new setting groups differently without analysing anything again. | Your computer |
| Show | The page cuts each face out of its photo when your browser asks for it; nothing is written. | `127.0.0.1` only |

Each photo is analysed **once**: the next runs analyse only the new or changed photos. Ctrl+C
stops between two photos and keeps what is done. Videos are not analysed yet. A large collection
takes a while the first time: measure first (below).

## Your privacy

The numbers that describe a face are **biometric data**, the most sensitive kind of personal
data (GDPR, article 9). The tool treats them so:

- they stay in the index of the cache (`/cache`), never in your photos, never in the reports;
- nothing is sent anywhere: the models run on your computer, the page is served on `127.0.0.1`
  only, and the faces it shows are cut from the photos on request, never saved;
- the only access to the network is the **one-time download of the two models** from OpenCV Zoo
  on GitHub, checked by their SHA-256. It sends nothing about your photos. Without network, the
  error names the two files to save by hand into the `models` folder of the cache;
- the names are in your `config.toml`, as text: the faces they name are written by photo and
  number, never as numbers that describe a face;
- **`people --forget`** deletes every face from the cache (their place in the file is
  overwritten), then reads the index again to show that none is left. It then asks whether the
  names of `config.toml` go too, and reads the file back to show it.

## Measure first: `--sample`

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v media-hygiene-cache:/cache `
  cavo789/media-hygiene people --sample 200
```

`--sample N` analyses N photos at random, prints the time per photo and the estimate of a full
run, and stops. The faces found are kept: the full run goes on from there.

## One folder first: `--path`

`--path "C:\Photos\2019"` analyses and groups only the photos below that folder (host path, as
you mounted it); repeat it for several folders.

## Settings: `[people]`

| Setting | Default | Meaning |
|---|---|---|
| `similarity` | `0.363` | How alike two faces must be (cosine, 0 to 1) to be the same person. Higher: more, smaller groups; lower: people mixed. `0.363` is SFace's documented value. |
| `min_face` | `40` | Faces smaller than this many pixels (shorter side of their box) are left out: too small to recognise. |
| `min_sharpness` | `30` | Faces blurrier than this are left out: a blurred face drifts away from the same face seen sharp. |
| `with_audit` | `false` | `true`: every `audit` looks for faces too, after asking, as `audit --people` does. |
| `ignored`, `[[people.person]]` | none | Written by the page: the faces ignored, and each person's name, confirmed faces (`faces`) and faces taken out (`rejected`). |

They only choose which faces are grouped, and how: changing them analyses nothing again. To try
another value once: `-e MEDIA_HYGIENE_PEOPLE__SIMILARITY=0.45`.

## Not there yet

- A column in the inventory; the names in the `.xmp` sidecars.
- The faces of videos.

To **find** the photos of someone, a photo manager such as Immich already does it well; `people`
is here to **file** them by who is in them, with `classify` and `sort`.
