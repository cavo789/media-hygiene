# 7. The configuration file

[Documentation](../README.md) › Cleaning, step 7 of 13 · 🇫🇷 [Français](../../fr/clean/07-configuration-file.md)

Your preferred folders, your excluded backup, your language: rather than typing them in every
command, write them once in a file, `config.toml`. The tool reads it at every run.

## Create the file

The tool only sees the folders you mount: it reads the file in a folder of yours mounted on
`/config` (`mh` mounts `$HOME\media-hygiene\config`). Run the `config` command once:

```powershell
mh config
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
mkdir -Force "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config
```

</details>

A commented `config.toml` has appeared in `C:\Users\<you>\media-hygiene\config`. Open it with any
text editor, Notepad is fine:

```powershell
notepad "$HOME\media-hygiene\config\config.toml"
```

<details>
<summary>What <code>config</code> printed (its first line says the file was created, then every setting)</summary>

<!-- capture: config-first.txt|A commented configuration file| -->
```text
💡 A commented configuration file was created: /config/config.toml.
Effective settings
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Setting                       ┃ Value                         ┃ Origin       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ general.locale                │ en                            │ command line │
│ general.timezone              │                               │ default      │
│ general.verbosity             │ info                          │ default      │
│ general.color                 │ never                         │ command line │
│ folders.preferred             │ []                            │ default      │
│ folders.protected             │ []                            │ default      │
│ folders.excluded              │ []                            │ default      │
│ scan.categories               │ {}                            │ default      │
│ scan.extensions               │ []                            │ default      │
│ scan.excluded_names           │ []                            │ default      │
│ (always skipped)              │ ['$recycle.bin', 'system      │ built-in     │
│                               │ volume information',          │              │
│                               │ '@eadir', '#recycle',         │              │
│                               │ '@recycle', '.@__thumb',      │              │
│                               │ '.trash', '.trash-*',         │              │
│                               │ '.trashes', '.thumbnails']    │              │
│ keep.generated_names          │ ['_?(IMG|VID|MVI|MOV|SAM|DSC[ │ default      │
│                               │ NF]?|_DSC|PICT|CIMG)[_-]?\\d+ │              │
│                               │ ',                            │              │
│                               │ '(IMG|VID)[_-]\\d{8}[_-]\\d{6 │              │
│                               │ }([_-]\\d+)?',                │              │
│                               │ '(IMG|VID|AUD)-\\d{8}-WA\\d+' │              │
│                               │ , '_?MG_\\d+', 'P\\d{7}',     │              │
│                               │ 'PXL_\\d{8}_\\d+.*',          │              │
│                               │ '\\d{8}_\\d{6}(_\\d+)?',      │              │
│                               │ '\\d{4}-\\d{2}-\\d{2}         │              │
│                               │ \\d{2}\\.\\d{2}\\.\\d{2}(-\\d │              │
│                               │ +)?',                         │              │
│                               │ '(GOPR|G[HX]\\d{2})\\d{4}',   │              │
│                               │ 'DJI_\\d+',                   │              │
│                               │ '(FB_IMG|received|Snapchat)[_ │              │
│                               │ -]\\d+', '(Screenshot|Screen  │              │
│                               │ Shot|Capture d.écran)([       │              │
│                               │ _-].*)?', 'image\\d*',        │              │
│                               │ '[0-9a-f]{8}(-[0-9a-f]{4}){3} │              │
│                               │ -[0-9a-f]{12}',               │              │
│                               │ '[0-9a-f]{16,}', '\\d{1,6}']  │              │
│ keep.generic_folders          │ ['DCIM',                      │ default      │
│                               │ '\\d{3}[A-Z0-9_]{5}',         │              │
│                               │ 'Camera( Roll| Uploads)?',    │              │
│                               │ 'WhatsApp (Images|Video)',    │              │
│                               │ 'Sent',                       │              │
│                               │ 'Downloads?|Téléchargements', │              │
│                               │ 'Screenshots|Captures         │              │
│                               │ d.écran', '(New               │              │
│                               │ folder|Nouveau dossier)(      │              │
│                               │ \\(\\d+\\))?',                │              │
│                               │ 'Import(s|ed)?|Temp|tmp',     │              │
│                               │ '(?P<year>(?:19|20)\\d{2})',  │              │
│                               │ '(?P<year>(?:19|20)\\d{2})[-_ │              │
│                               │ . ](?P<month>\\d{1,2})',      │              │
│                               │ '(?P<month_name>janvier|janua │              │
│                               │ ry|januari|jan|février|fevrie │              │
│                               │ r|february|februari|feb|fév|f │              │
│                               │ ev|mars|march|maart|mar|avril │              │
│                               │ |april|apr|avr|mai|may|mei|ju │              │
│                               │ in|june|juni|jun|juillet|july │              │
│                               │ |juli|jul|juil|août|aout|augu │              │
│                               │ st|augustus|aug|septembre|sep │              │
│                               │ tember|sep|sept|octobre|octob │              │
│                               │ er|oktober|oct|okt|novembre|n │              │
│                               │ ovember|nov|décembre|decembre │              │
│                               │ |december|dec|déc)\\.?[       │              │
│                               │ _-]*(?P<year>(?:19|20)\\d{2}) │              │
│                               │ ',                            │              │
│                               │ '(?P<year>(?:19|20)\\d{2})[   │              │
│                               │ _-]*(?P<month_name>janvier|ja │              │
│                               │ nuary|januari|jan|février|fev │              │
│                               │ rier|february|februari|feb|fé │              │
│                               │ v|fev|mars|march|maart|mar|av │              │
│                               │ ril|april|apr|avr|mai|may|mei │              │
│                               │ |juin|june|juni|jun|juillet|j │              │
│                               │ uly|juli|jul|juil|août|aout|a │              │
│                               │ ugust|augustus|aug|septembre| │              │
│                               │ september|sep|sept|octobre|oc │              │
│                               │ tober|oktober|oct|okt|novembr │              │
│                               │ e|november|nov|décembre|decem │              │
│                               │ bre|december|dec|déc)',       │              │
│                               │ '(?P<month_name>janvier|janua │              │
│                               │ ry|januari|jan|février|fevrie │              │
│                               │ r|february|februari|feb|fév|f │              │
│                               │ ev|mars|march|maart|mar|avril │              │
│                               │ |april|apr|avr|mai|may|mei|ju │              │
│                               │ in|june|juni|jun|juillet|july │              │
│                               │ |juli|jul|juil|août|aout|augu │              │
│                               │ st|augustus|aug|septembre|sep │              │
│                               │ tember|sep|sept|octobre|octob │              │
│                               │ er|oktober|oct|okt|novembre|n │              │
│                               │ ovember|nov|décembre|decembre │              │
│                               │ |december|dec|déc)',          │              │
│                               │ '(?P<year>(?:19|20)\\d{2})-\\ │              │
│                               │ d{2}-\\d{2}(?:\\.\\.[\\d-]+)? │              │
│                               │ ']                            │              │
│ clean.confirm                 │ True                          │ default      │
│ clean.purge_hint_days         │ 30                            │ default      │
│ review.propose_aside_below    │ 0.35                          │ default      │
│ review.identical_below        │ 6                             │ default      │
│ review.brightness_gap         │ 60.0                          │ default      │
│ review.clipped_gap            │ 0.25                          │ default      │
│ classify.target               │                               │ default      │
│ classify.leave                │ []                            │ default      │
│ classify.timezone             │                               │ default      │
│ classify.layout               │ {year}/{category}             │ default      │
│ classify.unsure_layout        │ {year}/To check/{category}    │ default      │
│ classify.manual_layout        │ {year}/To sort/{event}        │ default      │
│ classify.undated_layout       │ To sort/Undated               │ default      │
│ classify.received_layout      │ To sort/Received and          │ default      │
│                               │ downloaded                    │              │
│ classify.session_gap_hours    │ 6.0                           │ default      │
│ classify.merge_gap_hours      │ 18.0                          │ default      │
│ classify.min_event_size       │ 5                             │ default      │
│ classify.event_year           │ start                         │ default      │
│ classify.sure                 │ 80                            │ default      │
│ classify.unsure               │ 50                            │ default      │
│ classify.scores               │ {'existing-folder': 90,       │ default      │
│                               │ 'person-folder': 85,          │              │
│                               │ 'event-neighbour': 70,        │              │
│                               │ 'calendar': 85, 'date-range': │              │
│                               │ 95, 'kind': 85, 'path': 90,   │              │
│                               │ 'camera': 90,                 │              │
│                               │ 'other-category': 85,         │              │
│                               │ 'subject': 85, 'person': 85,  │              │
│                               │ 'place': 90,                  │              │
│                               │ 'place-neighbour': 70,        │              │
│                               │ 'trip': 90, 'trip-neighbour': │              │
│                               │ 70, 'date-only': 90,          │              │
│                               │ 'no-signal': 0}               │              │
│ classify.name_dates           │ ['(?:IMG|VID|PXL|MVIMG)?[_-]? │ default      │
│                               │ (?P<y>\\d{4})(?P<m>\\d{2})(?P │              │
│                               │ <d>\\d{2})[_-](?P<H>\\d{2})(? │              │
│                               │ P<M>\\d{2})(?P<S>\\d{2}).*',  │              │
│                               │ '(?:IMG|VID|AUD)-(?P<y>\\d{4} │              │
│                               │ )(?P<m>\\d{2})(?P<d>\\d{2})-W │              │
│                               │ A\\d+',                       │              │
│                               │ '(?:Screenshot|Capture)[      │              │
│                               │ _-]*(?P<y>\\d{4})-?(?P<m>\\d{ │              │
│                               │ 2})-?(?P<d>\\d{2}).*',        │              │
│                               │ '(?P<y>\\d{4})-(?P<m>\\d{2})- │              │
│                               │ (?P<d>\\d{2})[                │              │
│                               │ _](?P<H>\\d{2})(?P<M>\\d{2})[ │              │
│                               │ ._](?P<S>\\d{2}).*']          │              │
│ classify.generic_folders      │ ['(My |Mes                    │ default      │
│                               │ )?(Photos|Pictures|Images|Vid │              │
│                               │ eos|Vidéos|Mes images)',      │              │
│                               │ '(Family|Famille|Photos de    │              │
│                               │ famille|Family photos)']      │              │
│ classify.rules                │ [{'name': 'Films and series', │ default      │
│                               │ 'match': 'kind', 'category':  │              │
│                               │ '', 'dates': '', 'pattern':   │              │
│                               │ '', 'kind': 'download',       │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Existing     │              │
│                               │ folders', 'match':            │              │
│                               │ 'existing_folder',            │              │
│                               │ 'category': '', 'dates': '',  │              │
│                               │ 'pattern': '', 'kind': None,  │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Screenshots  │              │
│                               │ and documents', 'match':      │              │
│                               │ 'kind', 'category':           │              │
│                               │ 'Documents and screenshots',  │              │
│                               │ 'dates': '', 'pattern': '',   │              │
│                               │ 'kind': 'screenshot',         │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Event        │              │
│                               │ neighbours', 'match':         │              │
│                               │ 'event_neighbour',            │              │
│                               │ 'category': '', 'dates': '',  │              │
│                               │ 'pattern': '', 'kind': None,  │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Christmas',  │              │
│                               │ 'match': 'calendar',          │              │
│                               │ 'category':                   │              │
│                               │ 'Parties/Christmas', 'dates': │              │
│                               │ '12-24..12-26', 'pattern':    │              │
│                               │ '', 'kind': None,             │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'New Year',   │              │
│                               │ 'match': 'calendar',          │              │
│                               │ 'category': 'Parties/New      │              │
│                               │ Year', 'dates':               │              │
│                               │ '12-31..01-01', 'pattern':    │              │
│                               │ '', 'kind': None,             │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}]                        │              │
│ classify.ai                   │ {'url':                       │ default      │
│                               │ 'http://host.docker.internal: │              │
│                               │ 11434', 'model': '',          │              │
│                               │ 'map_model': '',              │              │
│                               │ 'samples_per_event': 3,       │              │
│                               │ 'min_edge': 512,              │              │
│                               │ 'image_edge': 768,            │              │
│                               │ 'concurrency': 1,             │              │
│                               │ 'timeout_seconds': 180.0,     │              │
│                               │ 'retries': 2, 'batch_size':   │              │
│                               │ 20, 'confirm_above': 200,     │              │
│                               │ 'seconds_per_photo': 4.5}     │              │
│ classify.places               │ []                            │ default      │
│ classify.trip_min_km          │ 100.0                         │ default      │
│ classify.trip_merge_gap_hours │ 48.0                          │ default      │
│ classify.trip_merge_max_km    │ 120.0                         │ default      │
│ sort.confirm                  │ True                          │ default      │
│ sort.junk_files               │ ['Thumbs.db', 'desktop.ini',  │ default      │
│                               │ '.DS_Store']                  │              │
│ inventory.blurry_below        │ 100.0                         │ default      │
│ inventory.small_below         │ 1000                          │ default      │
│ inventory.dark_below          │ 50.0                          │ default      │
│ inventory.bright_above        │ 205.0                         │ default      │
│ inventory.clipped_above       │ 0.25                          │ default      │
│ places.tiles                  │ https://tile.openstreetmap.or │ default      │
│                               │ g/{z}/{x}/{y}.png             │              │
│ places.attribution            │ © OpenStreetMap contributors  │ default      │
│ places.nominatim_url          │ https://nominatim.openstreetm │ default      │
│                               │ ap.org                        │              │
│ album.root                    │                               │ default      │
│ tags.language                 │                               │ default      │
│ tags.stop_words               │ ['sol', 'mur', 'murs',        │ default      │
│                               │ 'intérieur', 'extérieur',     │              │
│                               │ 'plafond', 'photo', 'image',  │              │
│                               │ 'personne', 'personnes',      │              │
│                               │ 'chose', 'objet', 'fond',     │              │
│                               │ 'scène', 'vue', 'floor',      │              │
│                               │ 'wall', 'indoor', 'indoors',  │              │
│                               │ 'outdoor', 'outdoors',        │              │
│                               │ 'ceiling', 'picture',         │              │
│                               │ 'person', 'people', 'thing',  │              │
│                               │ 'object', 'background',       │              │
│                               │ 'scene', 'view']              │              │
│ tags.town_km                  │ 20.0                          │ default      │
│ tags.xmp_sources              │ ['vision', 'place']           │ default      │
│ people.similarity             │ 0.363                         │ default      │
│ people.min_face               │ 40                            │ default      │
│ people.min_sharpness          │ 30.0                          │ default      │
│ people.with_audit             │ False                         │ default      │
│ people.ignored                │ 0 faces                       │ default      │
│ people.person                 │                               │ default      │
└───────────────────────────────┴───────────────────────────────┴──────────────┘

Extension categories (--ext)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Category ┃ Extensions                                             ┃ Origin   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ photo    │ avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif,  │ built-in │
│          │ tiff, webp                                             │          │
│ raw      │ arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw       │ built-in │
│ video    │ 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg,    │ built-in │
│          │ mpg, mts, ts, webm, wmv                                │          │
│ media    │ 3g2, 3gp, arw, avi, avif, bmp, cr2, cr3, dng, flv,     │ built-in │
│          │ gif, heic, heif, jpe, jpeg, jpg, m2ts, m4v, mkv, mov,  │          │
│          │ mp4, mpeg, mpg, mts, nef, orf, pef, png, raf, rw2,     │          │
│          │ srw, tif, tiff, ts, webm, webp, wmv                    │          │
└──────────┴────────────────────────────────────────────────────────┴──────────┘

Mount points
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Mount            ┃ Folder on your computer ┃ State     ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ /data/c/Photos   │ C:\Photos               │ read-only │
│ /data/d/Old disk │ D:\Old disk             │ read-only │
│ /config          │ —                       │ mounted   │
│ /journal         │ —                       │ mounted   │
│ /quarantine      │ —                       │ mounted   │
│ /reports         │ —                       │ mounted   │
│ /cache           │ —                       │ mounted   │
└──────────────────┴─────────────────────────┴───────────┘

💡 Edit /config/config.toml to change these settings; command-line options win.
```

</details>

## The three settings most people change

Find these lines in the file, change their values, save:

```toml
[general]
locale = "fr"                 # the language of the tool: en | fr
timezone = "Europe/Brussels"  # your time zone; empty: UTC, one or two hours off

[folders]
preferred = ['C:\Photos\Family']  # the folders whose copies are kept first
```

- **`locale`**: `"fr"` for French, `"en"` for English.
- **`timezone`**: your zone, such as `Europe/Paris` or `America/Montreal`, so that the reports
  are named and dated in your local time.
- **`preferred`**: the folders that keep their copies ([step 5](05-choose-the-kept-copy.md));
  Windows paths between **single quotes**.

The next runs read the file as long as `-v …:/config` is in the command (`mh` adds it for you).
Everything else can wait: the rest of this page explains the other settings.

## Every setting is explained in the file

For instance, the start of the file:

<!-- capture: config.toml|[general]|color =  -->
```toml
[general]
# Interface language: "en" or "fr".
# CLI: --locale
locale = "en"

# Your time zone, for the dates and the names of reports and runs, e.g.
# "Europe/Brussels" or "America/Montreal" (list:
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). Empty: UTC, as Docker
# does not know yours.
timezone = ""

# How much to log: "error", "warning", "info", "verbose" (info and every tip, not only
# the best two) or "debug".
# CLI: --verbosity
verbosity = "info"

# ANSI colours: "auto", "always" or "never".
# CLI: --color
color = "auto"
```

The file is never overwritten; delete it to get a fresh one.

> 💡 Its comments are written in the language of that first run, and that language is saved in
> it: created with `cavo789/media-hygiene --locale fr config`, the file is commented in French and
> holds `locale = "fr"`, so the next runs speak French without `--locale`.

## Fill it in

The settings of steps 5 and 6, in the file. Write Windows paths between **single quotes**:

```toml
[general]
locale = "en"          # en | fr
timezone = "Europe/Brussels"  # your time zone; empty: UTC

[folders]
preferred = ['C:\Photos\Old phone', 'C:\Photos\Family']
protected = []
excluded = ['D:\backup']

[scan]
excluded_names = []    # folder names skipped on every disk, e.g. ["Thumbnails", ".Trash-*"]
extensions = []        # e.g. ["photo", "mp4"]; empty: every photo, RAW and video

[scan.categories]      # your own categories for --ext
documents = ["pdf", "docx", "txt"]

[clean]
confirm = true         # clean asks before doing anything

[sort]
confirm = true         # sort asks before moving anything
junk_files = ["Thumbs.db", "desktop.ini", ".DS_Store"]  # do not keep a folder alive
```

- **`timezone`**: your time zone, for the times shown and the names of the reports and runs.
  Docker does not know it: empty, everything is in UTC (the audit reminds you). Its name comes from
  [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), e.g.
  `Europe/Paris`, `America/Montreal`. `-e TZ=Europe/Brussels` in `docker run` works too.
- **`preferred`**: their copies are kept first, in this order (`--prefer`).
- **`protected`**: never modified, and their files are always the copies kept (`--protect`).
- **`excluded`**: never analysed, for a real backup (`--exclude`).
- **`excluded_names`**: folder names never analysed, wherever they are; globs such as `.Trash-*`,
  case ignored, added to the system folders always skipped (`--exclude-name`,
  [step 5](05-choose-the-kept-copy.md#skip-a-folder-name-on-every-disk)). Globs, not the regular
  expressions of `[keep]` below: `$RECYCLE.BIN` as a regular expression never matches.
- **`extensions`**: only these categories or file types (`--ext`).
- **`[scan.categories]`**: your names for lists of extensions, next to the built-in categories
  `photo`, `raw`, `video` and `media` ([step 6](06-file-types.md#your-own-categories)).

Why single quotes? In double quotes, TOML turns the `\b` of `"D:\backup"` into a control
character; the tool refuses such a path rather than ignoring it.

Two advanced lists, `generated_names` and `generic_folders` (in `[keep]`), hold the regular
expressions of rules 5 and 6 of [the keep rules](05-choose-the-kept-copy.md#how-the-tool-chooses):
file names cameras and apps generate, folder names devices create. Leave them commented to use
the built-in lists; an empty list `[]` disables the rule.

## Use it

`mh` mounts the folder for every command, so the tool reads the file each time. Without `mh`,
add the same `-v …:/config` to every command:

```powershell
mh audit
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

</details>

## Check what the tool uses: `config`

`config` shows every setting, where it comes from, and the state of each mount point: `mh config`
(without `mh`, the same `-v` options as your audit, with `config` instead of `audit`):

<details>
<summary>What <code>config</code> prints: every setting, then every mount point</summary>

<!-- capture: config.txt -->
```text
Effective settings
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Setting                       ┃ Value                         ┃ Origin       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ general.locale                │ en                            │ command line │
│ general.timezone              │                               │ config.toml  │
│ general.verbosity             │ info                          │ config.toml  │
│ general.color                 │ never                         │ command line │
│ folders.preferred             │ []                            │ config.toml  │
│ folders.protected             │ []                            │ config.toml  │
│ folders.excluded              │ []                            │ config.toml  │
│ scan.categories               │ {}                            │ config.toml  │
│ scan.extensions               │ []                            │ config.toml  │
│ scan.excluded_names           │ []                            │ config.toml  │
│ (always skipped)              │ ['$recycle.bin', 'system      │ built-in     │
│                               │ volume information',          │              │
│                               │ '@eadir', '#recycle',         │              │
│                               │ '@recycle', '.@__thumb',      │              │
│                               │ '.trash', '.trash-*',         │              │
│                               │ '.trashes', '.thumbnails']    │              │
│ keep.generated_names          │ ['_?(IMG|VID|MVI|MOV|SAM|DSC[ │ default      │
│                               │ NF]?|_DSC|PICT|CIMG)[_-]?\\d+ │              │
│                               │ ',                            │              │
│                               │ '(IMG|VID)[_-]\\d{8}[_-]\\d{6 │              │
│                               │ }([_-]\\d+)?',                │              │
│                               │ '(IMG|VID|AUD)-\\d{8}-WA\\d+' │              │
│                               │ , '_?MG_\\d+', 'P\\d{7}',     │              │
│                               │ 'PXL_\\d{8}_\\d+.*',          │              │
│                               │ '\\d{8}_\\d{6}(_\\d+)?',      │              │
│                               │ '\\d{4}-\\d{2}-\\d{2}         │              │
│                               │ \\d{2}\\.\\d{2}\\.\\d{2}(-\\d │              │
│                               │ +)?',                         │              │
│                               │ '(GOPR|G[HX]\\d{2})\\d{4}',   │              │
│                               │ 'DJI_\\d+',                   │              │
│                               │ '(FB_IMG|received|Snapchat)[_ │              │
│                               │ -]\\d+', '(Screenshot|Screen  │              │
│                               │ Shot|Capture d.écran)([       │              │
│                               │ _-].*)?', 'image\\d*',        │              │
│                               │ '[0-9a-f]{8}(-[0-9a-f]{4}){3} │              │
│                               │ -[0-9a-f]{12}',               │              │
│                               │ '[0-9a-f]{16,}', '\\d{1,6}']  │              │
│ keep.generic_folders          │ ['DCIM',                      │ default      │
│                               │ '\\d{3}[A-Z0-9_]{5}',         │              │
│                               │ 'Camera( Roll| Uploads)?',    │              │
│                               │ 'WhatsApp (Images|Video)',    │              │
│                               │ 'Sent',                       │              │
│                               │ 'Downloads?|Téléchargements', │              │
│                               │ 'Screenshots|Captures         │              │
│                               │ d.écran', '(New               │              │
│                               │ folder|Nouveau dossier)(      │              │
│                               │ \\(\\d+\\))?',                │              │
│                               │ 'Import(s|ed)?|Temp|tmp',     │              │
│                               │ '(?P<year>(?:19|20)\\d{2})',  │              │
│                               │ '(?P<year>(?:19|20)\\d{2})[-_ │              │
│                               │ . ](?P<month>\\d{1,2})',      │              │
│                               │ '(?P<month_name>janvier|janua │              │
│                               │ ry|januari|jan|février|fevrie │              │
│                               │ r|february|februari|feb|fév|f │              │
│                               │ ev|mars|march|maart|mar|avril │              │
│                               │ |april|apr|avr|mai|may|mei|ju │              │
│                               │ in|june|juni|jun|juillet|july │              │
│                               │ |juli|jul|juil|août|aout|augu │              │
│                               │ st|augustus|aug|septembre|sep │              │
│                               │ tember|sep|sept|octobre|octob │              │
│                               │ er|oktober|oct|okt|novembre|n │              │
│                               │ ovember|nov|décembre|decembre │              │
│                               │ |december|dec|déc)\\.?[       │              │
│                               │ _-]*(?P<year>(?:19|20)\\d{2}) │              │
│                               │ ',                            │              │
│                               │ '(?P<year>(?:19|20)\\d{2})[   │              │
│                               │ _-]*(?P<month_name>janvier|ja │              │
│                               │ nuary|januari|jan|février|fev │              │
│                               │ rier|february|februari|feb|fé │              │
│                               │ v|fev|mars|march|maart|mar|av │              │
│                               │ ril|april|apr|avr|mai|may|mei │              │
│                               │ |juin|june|juni|jun|juillet|j │              │
│                               │ uly|juli|jul|juil|août|aout|a │              │
│                               │ ugust|augustus|aug|septembre| │              │
│                               │ september|sep|sept|octobre|oc │              │
│                               │ tober|oktober|oct|okt|novembr │              │
│                               │ e|november|nov|décembre|decem │              │
│                               │ bre|december|dec|déc)',       │              │
│                               │ '(?P<month_name>janvier|janua │              │
│                               │ ry|januari|jan|février|fevrie │              │
│                               │ r|february|februari|feb|fév|f │              │
│                               │ ev|mars|march|maart|mar|avril │              │
│                               │ |april|apr|avr|mai|may|mei|ju │              │
│                               │ in|june|juni|jun|juillet|july │              │
│                               │ |juli|jul|juil|août|aout|augu │              │
│                               │ st|augustus|aug|septembre|sep │              │
│                               │ tember|sep|sept|octobre|octob │              │
│                               │ er|oktober|oct|okt|novembre|n │              │
│                               │ ovember|nov|décembre|decembre │              │
│                               │ |december|dec|déc)',          │              │
│                               │ '(?P<year>(?:19|20)\\d{2})-\\ │              │
│                               │ d{2}-\\d{2}(?:\\.\\.[\\d-]+)? │              │
│                               │ ']                            │              │
│ clean.confirm                 │ True                          │ config.toml  │
│ clean.purge_hint_days         │ 30                            │ config.toml  │
│ review.propose_aside_below    │ 0.35                          │ config.toml  │
│ review.identical_below        │ 6                             │ config.toml  │
│ review.brightness_gap         │ 60.0                          │ config.toml  │
│ review.clipped_gap            │ 0.25                          │ config.toml  │
│ classify.target               │                               │ config.toml  │
│ classify.leave                │ []                            │ config.toml  │
│ classify.timezone             │                               │ config.toml  │
│ classify.layout               │ {year}/{category}             │ config.toml  │
│ classify.unsure_layout        │ {year}/To check/{category}    │ config.toml  │
│ classify.manual_layout        │ {year}/To sort/{event}        │ config.toml  │
│ classify.undated_layout       │ To sort/Undated               │ config.toml  │
│ classify.received_layout      │ To sort/Received and          │ config.toml  │
│                               │ downloaded                    │              │
│ classify.session_gap_hours    │ 6.0                           │ default      │
│ classify.merge_gap_hours      │ 18.0                          │ config.toml  │
│ classify.min_event_size       │ 5                             │ config.toml  │
│ classify.event_year           │ start                         │ default      │
│ classify.sure                 │ 80                            │ config.toml  │
│ classify.unsure               │ 50                            │ config.toml  │
│ classify.scores               │ {'existing-folder': 90,       │ default      │
│                               │ 'person-folder': 85,          │              │
│                               │ 'event-neighbour': 70,        │              │
│                               │ 'calendar': 85, 'date-range': │              │
│                               │ 95, 'kind': 85, 'path': 90,   │              │
│                               │ 'camera': 90,                 │              │
│                               │ 'other-category': 85,         │              │
│                               │ 'subject': 85, 'person': 85,  │              │
│                               │ 'place': 90,                  │              │
│                               │ 'place-neighbour': 70,        │              │
│                               │ 'trip': 90, 'trip-neighbour': │              │
│                               │ 70, 'date-only': 90,          │              │
│                               │ 'no-signal': 0}               │              │
│ classify.name_dates           │ ['(?:IMG|VID|PXL|MVIMG)?[_-]? │ default      │
│                               │ (?P<y>\\d{4})(?P<m>\\d{2})(?P │              │
│                               │ <d>\\d{2})[_-](?P<H>\\d{2})(? │              │
│                               │ P<M>\\d{2})(?P<S>\\d{2}).*',  │              │
│                               │ '(?:IMG|VID|AUD)-(?P<y>\\d{4} │              │
│                               │ )(?P<m>\\d{2})(?P<d>\\d{2})-W │              │
│                               │ A\\d+',                       │              │
│                               │ '(?:Screenshot|Capture)[      │              │
│                               │ _-]*(?P<y>\\d{4})-?(?P<m>\\d{ │              │
│                               │ 2})-?(?P<d>\\d{2}).*',        │              │
│                               │ '(?P<y>\\d{4})-(?P<m>\\d{2})- │              │
│                               │ (?P<d>\\d{2})[                │              │
│                               │ _](?P<H>\\d{2})(?P<M>\\d{2})[ │              │
│                               │ ._](?P<S>\\d{2}).*']          │              │
│ classify.generic_folders      │ ['(My |Mes                    │ default      │
│                               │ )?(Photos|Pictures|Images|Vid │              │
│                               │ eos|Vidéos|Mes images)',      │              │
│                               │ '(Family|Famille|Photos de    │              │
│                               │ famille|Family photos)']      │              │
│ classify.rules                │ [{'name': 'Films and series', │ config.toml  │
│                               │ 'match': 'kind', 'category':  │              │
│                               │ '', 'dates': '', 'pattern':   │              │
│                               │ '', 'kind': 'download',       │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Existing     │              │
│                               │ folders', 'match':            │              │
│                               │ 'existing_folder',            │              │
│                               │ 'category': '', 'dates': '',  │              │
│                               │ 'pattern': '', 'kind': None,  │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Screenshots  │              │
│                               │ and documents', 'match':      │              │
│                               │ 'kind', 'category':           │              │
│                               │ 'Documents and screenshots',  │              │
│                               │ 'dates': '', 'pattern': '',   │              │
│                               │ 'kind': 'screenshot',         │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Event        │              │
│                               │ neighbours', 'match':         │              │
│                               │ 'event_neighbour',            │              │
│                               │ 'category': '', 'dates': '',  │              │
│                               │ 'pattern': '', 'kind': None,  │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'Christmas',  │              │
│                               │ 'match': 'calendar',          │              │
│                               │ 'category':                   │              │
│                               │ 'Parties/Christmas', 'dates': │              │
│                               │ '12-24..12-26', 'pattern':    │              │
│                               │ '', 'kind': None,             │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}, {'name': 'New Year',   │              │
│                               │ 'match': 'calendar',          │              │
│                               │ 'category': 'Parties/New      │              │
│                               │ Year', 'dates':               │              │
│                               │ '12-31..01-01', 'pattern':    │              │
│                               │ '', 'kind': None,             │              │
│                               │ 'categories': [],             │              │
│                               │ 'per_photo': False, 'names':  │              │
│                               │ [], 'all': False,             │              │
│                               │ 'min_share': None, 'score':   │              │
│                               │ None}]                        │              │
│ classify.ai                   │ {'url':                       │ config.toml  │
│                               │ 'http://host.docker.internal: │              │
│                               │ 11434', 'model': '',          │              │
│                               │ 'map_model': '',              │              │
│                               │ 'samples_per_event': 3,       │              │
│                               │ 'min_edge': 512,              │              │
│                               │ 'image_edge': 768,            │              │
│                               │ 'concurrency': 1,             │              │
│                               │ 'timeout_seconds': 180.0,     │              │
│                               │ 'retries': 2, 'batch_size':   │              │
│                               │ 20, 'confirm_above': 200,     │              │
│                               │ 'seconds_per_photo': 4.5}     │              │
│ classify.places               │ []                            │ default      │
│ classify.trip_min_km          │ 100.0                         │ config.toml  │
│ classify.trip_merge_gap_hours │ 48.0                          │ config.toml  │
│ classify.trip_merge_max_km    │ 120.0                         │ config.toml  │
│ sort.confirm                  │ True                          │ config.toml  │
│ sort.junk_files               │ ['Thumbs.db', 'desktop.ini',  │ config.toml  │
│                               │ '.DS_Store']                  │              │
│ inventory.blurry_below        │ 100.0                         │ config.toml  │
│ inventory.small_below         │ 1000                          │ config.toml  │
│ inventory.dark_below          │ 50.0                          │ config.toml  │
│ inventory.bright_above        │ 205.0                         │ config.toml  │
│ inventory.clipped_above       │ 0.25                          │ config.toml  │
│ places.tiles                  │ https://tile.openstreetmap.or │ config.toml  │
│                               │ g/{z}/{x}/{y}.png             │              │
│ places.attribution            │ © OpenStreetMap contributors  │ config.toml  │
│ places.nominatim_url          │ https://nominatim.openstreetm │ config.toml  │
│                               │ ap.org                        │              │
│ album.root                    │                               │ config.toml  │
│ tags.language                 │                               │ config.toml  │
│ tags.stop_words               │ ['sol', 'mur', 'murs',        │ default      │
│                               │ 'intérieur', 'extérieur',     │              │
│                               │ 'plafond', 'photo', 'image',  │              │
│                               │ 'personne', 'personnes',      │              │
│                               │ 'chose', 'objet', 'fond',     │              │
│                               │ 'scène', 'vue', 'floor',      │              │
│                               │ 'wall', 'indoor', 'indoors',  │              │
│                               │ 'outdoor', 'outdoors',        │              │
│                               │ 'ceiling', 'picture',         │              │
│                               │ 'person', 'people', 'thing',  │              │
│                               │ 'object', 'background',       │              │
│                               │ 'scene', 'view']              │              │
│ tags.town_km                  │ 20.0                          │ config.toml  │
│ tags.xmp_sources              │ ['vision', 'place']           │ config.toml  │
│ people.similarity             │ 0.363                         │ config.toml  │
│ people.min_face               │ 40                            │ config.toml  │
│ people.min_sharpness          │ 30.0                          │ config.toml  │
│ people.with_audit             │ False                         │ config.toml  │
│ people.ignored                │ 0 faces                       │ default      │
│ people.person                 │                               │ default      │
└───────────────────────────────┴───────────────────────────────┴──────────────┘

Extension categories (--ext)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Category ┃ Extensions                                             ┃ Origin   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ photo    │ avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif,  │ built-in │
│          │ tiff, webp                                             │          │
│ raw      │ arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw       │ built-in │
│ video    │ 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg,    │ built-in │
│          │ mpg, mts, ts, webm, wmv                                │          │
│ media    │ 3g2, 3gp, arw, avi, avif, bmp, cr2, cr3, dng, flv,     │ built-in │
│          │ gif, heic, heif, jpe, jpeg, jpg, m2ts, m4v, mkv, mov,  │          │
│          │ mp4, mpeg, mpg, mts, nef, orf, pef, png, raf, rw2,     │          │
│          │ srw, tif, tiff, ts, webm, webp, wmv                    │          │
└──────────┴────────────────────────────────────────────────────────┴──────────┘

Mount points
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Mount            ┃ Folder on your computer ┃ State     ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ /data/c/Photos   │ C:\Photos               │ read-only │
│ /data/d/Old disk │ D:\Old disk             │ read-only │
│ /config          │ —                       │ mounted   │
│ /journal         │ —                       │ mounted   │
│ /quarantine      │ —                       │ mounted   │
│ /reports         │ —                       │ mounted   │
│ /cache           │ —                       │ mounted   │
└──────────────────┴─────────────────────────┴───────────┘

💡 Edit /config/config.toml to change these settings; command-line options win.
```

</details>

- **Origin** says where each value comes from: `default`, `config.toml`, `environment` or
  `command line`.
- **Folder on your computer** shows the Windows folder behind each mount; `—` for a Docker
  volume such as the cache.

## Who wins?

From the strongest to the weakest: the command-line options, then the environment variables,
then `config.toml`, then the defaults. `--prefer` on the command line therefore replaces
`preferred` of the file for that run.

The environment variables are named `MEDIA_HYGIENE_<SECTION>__<KEY>` (two underscores), for
instance `-e MEDIA_HYGIENE_GENERAL__LOCALE=fr` in `docker run`; lists are written as JSON
arrays, tables as JSON objects that replace the file's whole table
(`MEDIA_HYGIENE_SCAN__CATEGORIES='{"documents": ["pdf", "docx"]}'`). Lists of tables, such as
the rules of `classify` (`[[classify.rules]]`), are read from `config.toml` only. Up to version
0.2 their prefix was `MEDIA_DEDUP_`: it still works until version 0.4.0, with a warning.

---

← [6. Only some file types](06-file-types.md) · [Documentation](../README.md) · Next: **[8. Clean](08-clean.md)** →
