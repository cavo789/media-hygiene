# 7. Le fichier de configuration

[Documentation](../README.md) › Nettoyer, étape 7 sur 13 · 🇬🇧 [English](../../en/clean/07-configuration-file.md)

Vos dossiers préférés, votre sauvegarde exclue, votre langue : plutôt que de les taper dans
chaque commande, écrivez-les une fois dans un fichier, `config.toml`. L'outil le lit à chaque
lancement.

## Créer le fichier

L'outil ne voit que les dossiers que vous montez : donnez-lui donc un de vos dossiers sur
`/config`, et lancez une fois la commande `config` :

```powershell
mkdir "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene --locale fr config
```

La première ligne dit ce qui s'est passé :

<!-- capture: config-first.txt|Un fichier de configuration commenté| -->
```text
💡 Un fichier de configuration commenté a été créé : /config/config.toml.
Réglages effectifs
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Réglage                     ┃ Valeur                     ┃ Origine           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ general.locale              │ fr                         │ ligne de commande │
│ general.verbosity           │ info                       │ défaut            │
│ general.color               │ never                      │ ligne de commande │
│ folders.preferred           │ []                         │ défaut            │
│ folders.protected           │ []                         │ défaut            │
│ folders.excluded            │ []                         │ défaut            │
│ scan.categories             │ {}                         │ défaut            │
│ scan.extensions             │ []                         │ défaut            │
│ scan.excluded_names         │ []                         │ défaut            │
│ (toujours ignorés)          │ ['$recycle.bin', 'system   │ intégrée          │
│                             │ volume information',       │                   │
│                             │ '@eadir', '#recycle',      │                   │
│                             │ '@recycle', '.@__thumb',   │                   │
│                             │ '.trash', '.trash-*',      │                   │
│                             │ '.trashes', '.thumbnails'] │                   │
│ keep.generated_names        │ ['_?(IMG|VID|MVI|MOV|SAM|D │ défaut            │
│                             │ SC[NF]?|_DSC|PICT|CIMG)[_- │                   │
│                             │ ]?\\d+',                   │                   │
│                             │ '(IMG|VID)[_-]\\d{8}[_-]\\ │                   │
│                             │ d{6}([_-]\\d+)?',          │                   │
│                             │ '(IMG|VID|AUD)-\\d{8}-WA\\ │                   │
│                             │ d+', '_?MG_\\d+',          │                   │
│                             │ 'P\\d{7}',                 │                   │
│                             │ 'PXL_\\d{8}_\\d+.*',       │                   │
│                             │ '\\d{8}_\\d{6}(_\\d+)?',   │                   │
│                             │ '\\d{4}-\\d{2}-\\d{2}      │                   │
│                             │ \\d{2}\\.\\d{2}\\.\\d{2}(- │                   │
│                             │ \\d+)?',                   │                   │
│                             │ '(GOPR|G[HX]\\d{2})\\d{4}' │                   │
│                             │ , 'DJI_\\d+',              │                   │
│                             │ '(FB_IMG|received|Snapchat │                   │
│                             │ )[_-]\\d+',                │                   │
│                             │ '(Screenshot|Screen        │                   │
│                             │ Shot|Capture d.écran)([    │                   │
│                             │ _-].*)?', 'image\\d*',     │                   │
│                             │ '[0-9a-f]{8}(-[0-9a-f]{4}) │                   │
│                             │ {3}-[0-9a-f]{12}',         │                   │
│                             │ '[0-9a-f]{16,}']           │                   │
│ keep.generic_folders        │ ['DCIM',                   │ défaut            │
│                             │ '\\d{3}[A-Z0-9_]{5}',      │                   │
│                             │ 'Camera( Roll| Uploads)?', │                   │
│                             │ 'WhatsApp (Images|Video)', │                   │
│                             │ 'Sent',                    │                   │
│                             │ 'Downloads?|Téléchargement │                   │
│                             │ s', 'Screenshots|Captures  │                   │
│                             │ d.écran', '(New            │                   │
│                             │ folder|Nouveau dossier)(   │                   │
│                             │ \\(\\d+\\))?',             │                   │
│                             │ 'Import(s|ed)?|Temp|tmp']  │                   │
│ clean.confirm               │ True                       │ défaut            │
│ classify.target             │                            │ défaut            │
│ classify.leave              │ []                         │ défaut            │
│ classify.timezone           │                            │ défaut            │
│ classify.layout             │ {year}/{category}          │ défaut            │
│ classify.unsure_layout      │ {year}/To check/{category} │ défaut            │
│ classify.manual_layout      │ {year}/To sort/{event}     │ défaut            │
│ classify.undated_layout     │ To sort/Undated            │ défaut            │
│ classify.received_layout    │ To sort/Received and       │ défaut            │
│                             │ downloaded                 │                   │
│ classify.session_gap_hours  │ 6.0                        │ défaut            │
│ classify.merge_gap_hours    │ 18.0                       │ défaut            │
│ classify.min_event_size     │ 5                          │ défaut            │
│ classify.event_year         │ start                      │ défaut            │
│ classify.sure               │ 80                         │ défaut            │
│ classify.unsure             │ 50                         │ défaut            │
│ classify.scores             │ {'existing-folder': 90,    │ défaut            │
│                             │ 'person-folder': 85,       │                   │
│                             │ 'event-neighbour': 70,     │                   │
│                             │ 'calendar': 85,            │                   │
│                             │ 'date-range': 95, 'kind':  │                   │
│                             │ 85, 'path': 90, 'camera':  │                   │
│                             │ 90, 'other-category': 85,  │                   │
│                             │ 'subject': 85, 'place':    │                   │
│                             │ 90, 'place-neighbour': 70, │                   │
│                             │ 'trip': 90,                │                   │
│                             │ 'trip-neighbour': 70,      │                   │
│                             │ 'date-only': 90,           │                   │
│                             │ 'no-signal': 0}            │                   │
│ classify.name_dates         │ ['(?:IMG|VID|PXL|MVIMG)?[_ │ défaut            │
│                             │ -]?(?P<y>\\d{4})(?P<m>\\d{ │                   │
│                             │ 2})(?P<d>\\d{2})[_-](?P<H> │                   │
│                             │ \\d{2})(?P<M>\\d{2})(?P<S> │                   │
│                             │ \\d{2}).*',                │                   │
│                             │ '(?:IMG|VID|AUD)-(?P<y>\\d │                   │
│                             │ {4})(?P<m>\\d{2})(?P<d>\\d │                   │
│                             │ {2})-WA\\d+',              │                   │
│                             │ '(?:Screenshot|Capture)[   │                   │
│                             │ _-]*(?P<y>\\d{4})-?(?P<m>\ │                   │
│                             │ \d{2})-?(?P<d>\\d{2}).*',  │                   │
│                             │ '(?P<y>\\d{4})-(?P<m>\\d{2 │                   │
│                             │ })-(?P<d>\\d{2})[          │                   │
│                             │ _](?P<H>\\d{2})(?P<M>\\d{2 │                   │
│                             │ })[._](?P<S>\\d{2}).*']    │                   │
│ classify.generic_folders    │ ['(My |Mes                 │ défaut            │
│                             │ )?(Photos|Pictures|Images| │                   │
│                             │ Videos|Vidéos|Mes          │                   │
│                             │ images)',                  │                   │
│                             │ '(Family|Famille|Photos de │                   │
│                             │ famille|Family photos)']   │                   │
│ classify.rules              │ [{'name': 'Films and       │ défaut            │
│                             │ series', 'match': 'kind',  │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ 'download', 'categories':  │                   │
│                             │ [], 'per_photo': False,    │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Existing folders',        │                   │
│                             │ 'match':                   │                   │
│                             │ 'existing_folder',         │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Screenshots and           │                   │
│                             │ documents', 'match':       │                   │
│                             │ 'kind', 'category':        │                   │
│                             │ 'Documents and             │                   │
│                             │ screenshots', 'dates': '', │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ 'screenshot',              │                   │
│                             │ 'categories': [],          │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Event neighbours',        │                   │
│                             │ 'match':                   │                   │
│                             │ 'event_neighbour',         │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Christmas', 'match':      │                   │
│                             │ 'calendar', 'category':    │                   │
│                             │ 'Parties/Christmas',       │                   │
│                             │ 'dates': '12-24..12-26',   │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'New Year', 'match':       │                   │
│                             │ 'calendar', 'category':    │                   │
│                             │ 'Parties/New Year',        │                   │
│                             │ 'dates': '12-31..01-01',   │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}]            │                   │
│ classify.ai                 │ {'url':                    │ défaut            │
│                             │ 'http://host.docker.intern │                   │
│                             │ al:11434', 'model': '',    │                   │
│                             │ 'map_model': '',           │                   │
│                             │ 'samples_per_event': 3,    │                   │
│                             │ 'min_edge': 512,           │                   │
│                             │ 'image_edge': 768,         │                   │
│                             │ 'concurrency': 1,          │                   │
│                             │ 'timeout_seconds': 180.0,  │                   │
│                             │ 'retries': 2,              │                   │
│                             │ 'batch_size': 20,          │                   │
│                             │ 'confirm_above': 200,      │                   │
│                             │ 'seconds_per_photo': 4.5}  │                   │
│ classify.places             │ []                         │ défaut            │
│ classify.trip_min_km        │ 100.0                      │ défaut            │
│ classify.trip_merge_gap_hou │ 48.0                       │ défaut            │
│ rs                          │                            │                   │
│ classify.trip_merge_max_km  │ 120.0                      │ défaut            │
│ sort.confirm                │ True                       │ défaut            │
│ sort.junk_files             │ ['Thumbs.db',              │ défaut            │
│                             │ 'desktop.ini',             │                   │
│                             │ '.DS_Store']               │                   │
│ inventory.blurry_below      │ 100.0                      │ défaut            │
│ inventory.small_below       │ 1000                       │ défaut            │
│ inventory.dark_below        │ 50.0                       │ défaut            │
│ inventory.bright_above      │ 205.0                      │ défaut            │
│ inventory.clipped_above     │ 0.25                       │ défaut            │
│ places.tiles                │ https://tile.openstreetmap │ défaut            │
│                             │ .org/{z}/{x}/{y}.png       │                   │
│ places.attribution          │ © OpenStreetMap            │ défaut            │
│                             │ contributors               │                   │
│ places.nominatim_url        │ https://nominatim.openstre │ défaut            │
│                             │ etmap.org                  │                   │
│ album.root                  │                            │ défaut            │
└─────────────────────────────┴────────────────────────────┴───────────────────┘

Catégories d'extensions (--ext)
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Catégorie ┃ Extensions                                            ┃ Origine  ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ photo     │ avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif, │ intégrée │
│           │ tiff, webp                                            │          │
│ raw       │ arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw      │ intégrée │
│ video     │ 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg,   │ intégrée │
│           │ mpg, mts, ts, webm, wmv                               │          │
│ media     │ 3g2, 3gp, arw, avi, avif, bmp, cr2, cr3, dng, flv,    │ intégrée │
│           │ gif, heic, heif, jpe, jpeg, jpg, m2ts, m4v, mkv, mov, │          │
│           │ mp4, mpeg, mpg, mts, nef, orf, pef, png, raf, rw2,    │          │
│           │ srw, tif, tiff, ts, webm, webp, wmv                   │          │
└───────────┴───────────────────────────────────────────────────────┴──────────┘

Points de montage
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Montage               ┃ Dossier sur votre ordinateur ┃ État          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ /data/c/Photos        │ C:\Photos                    │ lecture seule │
│ /data/d/Ancien disque │ D:\Ancien disque             │ lecture seule │
│ /config               │ —                            │ monté         │
│ /journal              │ —                            │ monté         │
│ /quarantine           │ —                            │ monté         │
│ /reports              │ —                            │ monté         │
│ /cache                │ —                            │ monté         │
└───────────────────────┴──────────────────────────────┴───────────────┘

💡 Modifiez /config/config.toml pour changer ces réglages ; les options de ligne
de commande l'emportent.
```

Un `config.toml` commenté est apparu dans `C:\Users\<vous>\media-hygiene\config`. Ouvrez-le avec
n'importe quel éditeur de texte (le Bloc-notes convient). Chaque réglage y est expliqué, par
exemple :

<!-- capture: config.toml|[general]|color =  -->
```toml
[general]
# Langue de l'interface : "en" ou "fr".
# CLI: --locale
locale = "fr"

# Quantité de messages : "error", "warning", "info" ou "debug".
# CLI: --verbosity
verbosity = "info"

# Couleurs ANSI : "auto", "always" ou "never".
# CLI: --color
color = "auto"
```

Le fichier n'est jamais écrasé ; supprimez-le pour en obtenir un neuf.

> 💡 Ses commentaires sont écrits dans la langue de ce premier lancement, et cette langue y est
> enregistrée : créé avec `--locale fr`, comme ici, le fichier est commenté en français et
> contient `locale = "fr"`. Les lancements suivants parlent donc français **sans** `--locale fr`,
> dès que ce `-v …:/config` est dans la commande.

## Le remplir

Les réglages des étapes 5 et 6, dans le fichier. Écrivez les chemins Windows entre
**apostrophes** :

```toml
[general]
locale = "fr"          # en | fr

[folders]
preferred = ['C:\Photos\Ancien téléphone', 'C:\Photos\Famille']
protected = []
excluded = ['D:\sauvegarde']

[scan]
excluded_names = []    # noms de dossiers ignorés partout, p. ex. ["Thumbnails", ".Trash-*"]
extensions = []        # p. ex. ["photo", "mp4"] ; vide : photos, RAW et vidéos

[scan.categories]      # vos propres catégories pour --ext
documents = ["pdf", "docx", "txt"]

[clean]
confirm = true         # clean demande avant de faire quoi que ce soit

[sort]
confirm = true         # sort demande avant de déplacer quoi que ce soit
junk_files = ["Thumbs.db", "desktop.ini", ".DS_Store"]  # ne gardent pas un dossier en vie
```

- **`preferred`** : leurs copies sont gardées en priorité, dans cet ordre (`--prefer`).
- **`protected`** : jamais modifiés, et leurs fichiers sont toujours les copies gardées
  (`--protect`).
- **`excluded`** : jamais analysés, pour une vraie sauvegarde (`--exclude`).
- **`excluded_names`** : noms de dossiers jamais analysés, où qu'ils soient ; des motifs comme
  `.Trash-*`, sans tenir compte de la casse, ajoutés aux dossiers système toujours ignorés
  (`--exclude-name`, [étape 5](05-choose-the-kept-copy.md#ignorer-un-nom-de-dossier-sur-tous-les-disques)).
  Des motifs, pas les expressions régulières de `[keep]` plus bas : `$RECYCLE.BIN` en expression
  régulière ne correspond jamais.
- **`extensions`** : seulement ces catégories ou types de fichiers (`--ext`).
- **`[scan.categories]`** : vos noms pour des listes d'extensions, à côté des catégories
  intégrées `photo`, `raw`, `video` et `media` ([étape 6](06-file-types.md#vos-propres-catégories)).

Pourquoi des apostrophes ? Entre guillemets, TOML lit la barre oblique inverse comme un
caractère spécial : le `\b` de `"D:\backup"` devient un caractère de contrôle (l'outil refuse
alors ce chemin au lieu de l'ignorer), et `"D:\sauvegarde"` rend même le fichier illisible.

Deux listes avancées, `generated_names` et `generic_folders` (dans `[keep]`), contiennent les
expressions régulières des règles 5 et 6 des [règles de choix](05-choose-the-kept-copy.md#comment-loutil-choisit) :
les noms de fichiers générés par les appareils et applications, les noms de dossiers créés par
les appareils. Laissez-les en commentaire pour utiliser les listes intégrées ; une liste vide `[]`
désactive la règle.

## L'utiliser

Ajoutez le même `-v …:/config` à chaque commande, et l'outil lit le fichier. Avec
`locale = "fr"` dans le fichier, `--locale fr` n'est plus nécessaire :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

Ce guide garde `--locale fr` dans ses commandes, pour celles et ceux qui n'ont pas de fichier de
configuration : il ne gêne pas.

## Vérifier ce que l'outil utilise : `config`

`config` montre chaque réglage, son origine, et l'état de chaque point de montage. Lancez-le avec
les mêmes options `-v` que votre audit (ici `config` au lieu de `audit`) :

<!-- capture: config.txt -->
```text
Réglages effectifs
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Réglage                     ┃ Valeur                     ┃ Origine           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ general.locale              │ fr                         │ ligne de commande │
│ general.verbosity           │ info                       │ config.toml       │
│ general.color               │ never                      │ ligne de commande │
│ folders.preferred           │ []                         │ config.toml       │
│ folders.protected           │ []                         │ config.toml       │
│ folders.excluded            │ []                         │ config.toml       │
│ scan.categories             │ {}                         │ config.toml       │
│ scan.extensions             │ []                         │ config.toml       │
│ scan.excluded_names         │ []                         │ config.toml       │
│ (toujours ignorés)          │ ['$recycle.bin', 'system   │ intégrée          │
│                             │ volume information',       │                   │
│                             │ '@eadir', '#recycle',      │                   │
│                             │ '@recycle', '.@__thumb',   │                   │
│                             │ '.trash', '.trash-*',      │                   │
│                             │ '.trashes', '.thumbnails'] │                   │
│ keep.generated_names        │ ['_?(IMG|VID|MVI|MOV|SAM|D │ défaut            │
│                             │ SC[NF]?|_DSC|PICT|CIMG)[_- │                   │
│                             │ ]?\\d+',                   │                   │
│                             │ '(IMG|VID)[_-]\\d{8}[_-]\\ │                   │
│                             │ d{6}([_-]\\d+)?',          │                   │
│                             │ '(IMG|VID|AUD)-\\d{8}-WA\\ │                   │
│                             │ d+', '_?MG_\\d+',          │                   │
│                             │ 'P\\d{7}',                 │                   │
│                             │ 'PXL_\\d{8}_\\d+.*',       │                   │
│                             │ '\\d{8}_\\d{6}(_\\d+)?',   │                   │
│                             │ '\\d{4}-\\d{2}-\\d{2}      │                   │
│                             │ \\d{2}\\.\\d{2}\\.\\d{2}(- │                   │
│                             │ \\d+)?',                   │                   │
│                             │ '(GOPR|G[HX]\\d{2})\\d{4}' │                   │
│                             │ , 'DJI_\\d+',              │                   │
│                             │ '(FB_IMG|received|Snapchat │                   │
│                             │ )[_-]\\d+',                │                   │
│                             │ '(Screenshot|Screen        │                   │
│                             │ Shot|Capture d.écran)([    │                   │
│                             │ _-].*)?', 'image\\d*',     │                   │
│                             │ '[0-9a-f]{8}(-[0-9a-f]{4}) │                   │
│                             │ {3}-[0-9a-f]{12}',         │                   │
│                             │ '[0-9a-f]{16,}']           │                   │
│ keep.generic_folders        │ ['DCIM',                   │ défaut            │
│                             │ '\\d{3}[A-Z0-9_]{5}',      │                   │
│                             │ 'Camera( Roll| Uploads)?', │                   │
│                             │ 'WhatsApp (Images|Video)', │                   │
│                             │ 'Sent',                    │                   │
│                             │ 'Downloads?|Téléchargement │                   │
│                             │ s', 'Screenshots|Captures  │                   │
│                             │ d.écran', '(New            │                   │
│                             │ folder|Nouveau dossier)(   │                   │
│                             │ \\(\\d+\\))?',             │                   │
│                             │ 'Import(s|ed)?|Temp|tmp']  │                   │
│ clean.confirm               │ True                       │ config.toml       │
│ classify.target             │                            │ config.toml       │
│ classify.leave              │ []                         │ config.toml       │
│ classify.timezone           │                            │ config.toml       │
│ classify.layout             │ {year}/{category}          │ config.toml       │
│ classify.unsure_layout      │ {year}/À                   │ config.toml       │
│                             │ vérifier/{category}        │                   │
│ classify.manual_layout      │ {year}/À trier/{event}     │ config.toml       │
│ classify.undated_layout     │ À trier/Sans date          │ config.toml       │
│ classify.received_layout    │ À trier/Reçues et          │ config.toml       │
│                             │ téléchargées               │                   │
│ classify.session_gap_hours  │ 6.0                        │ défaut            │
│ classify.merge_gap_hours    │ 18.0                       │ config.toml       │
│ classify.min_event_size     │ 5                          │ config.toml       │
│ classify.event_year         │ start                      │ défaut            │
│ classify.sure               │ 80                         │ config.toml       │
│ classify.unsure             │ 50                         │ config.toml       │
│ classify.scores             │ {'existing-folder': 90,    │ défaut            │
│                             │ 'person-folder': 85,       │                   │
│                             │ 'event-neighbour': 70,     │                   │
│                             │ 'calendar': 85,            │                   │
│                             │ 'date-range': 95, 'kind':  │                   │
│                             │ 85, 'path': 90, 'camera':  │                   │
│                             │ 90, 'other-category': 85,  │                   │
│                             │ 'subject': 85, 'place':    │                   │
│                             │ 90, 'place-neighbour': 70, │                   │
│                             │ 'trip': 90,                │                   │
│                             │ 'trip-neighbour': 70,      │                   │
│                             │ 'date-only': 90,           │                   │
│                             │ 'no-signal': 0}            │                   │
│ classify.name_dates         │ ['(?:IMG|VID|PXL|MVIMG)?[_ │ défaut            │
│                             │ -]?(?P<y>\\d{4})(?P<m>\\d{ │                   │
│                             │ 2})(?P<d>\\d{2})[_-](?P<H> │                   │
│                             │ \\d{2})(?P<M>\\d{2})(?P<S> │                   │
│                             │ \\d{2}).*',                │                   │
│                             │ '(?:IMG|VID|AUD)-(?P<y>\\d │                   │
│                             │ {4})(?P<m>\\d{2})(?P<d>\\d │                   │
│                             │ {2})-WA\\d+',              │                   │
│                             │ '(?:Screenshot|Capture)[   │                   │
│                             │ _-]*(?P<y>\\d{4})-?(?P<m>\ │                   │
│                             │ \d{2})-?(?P<d>\\d{2}).*',  │                   │
│                             │ '(?P<y>\\d{4})-(?P<m>\\d{2 │                   │
│                             │ })-(?P<d>\\d{2})[          │                   │
│                             │ _](?P<H>\\d{2})(?P<M>\\d{2 │                   │
│                             │ })[._](?P<S>\\d{2}).*']    │                   │
│ classify.generic_folders    │ ['(My |Mes                 │ défaut            │
│                             │ )?(Photos|Pictures|Images| │                   │
│                             │ Videos|Vidéos|Mes          │                   │
│                             │ images)',                  │                   │
│                             │ '(Family|Famille|Photos de │                   │
│                             │ famille|Family photos)']   │                   │
│ classify.rules              │ [{'name': 'Films et        │ config.toml       │
│                             │ séries', 'match': 'kind',  │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ 'download', 'categories':  │                   │
│                             │ [], 'per_photo': False,    │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Dossiers existants',      │                   │
│                             │ 'match':                   │                   │
│                             │ 'existing_folder',         │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ "Captures d'écran et       │                   │
│                             │ documents", 'match':       │                   │
│                             │ 'kind', 'category':        │                   │
│                             │ "Documents et captures     │                   │
│                             │ d'écran", 'dates': '',     │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ 'screenshot',              │                   │
│                             │ 'categories': [],          │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ "Voisins d'événement",     │                   │
│                             │ 'match':                   │                   │
│                             │ 'event_neighbour',         │                   │
│                             │ 'category': '', 'dates':   │                   │
│                             │ '', 'pattern': '', 'kind': │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Noël', 'match':           │                   │
│                             │ 'calendar', 'category':    │                   │
│                             │ 'Fêtes/Noël', 'dates':     │                   │
│                             │ '12-24..12-26', 'pattern': │                   │
│                             │ '', 'kind': None,          │                   │
│                             │ 'categories': [],          │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Nouvel An', 'match':      │                   │
│                             │ 'calendar', 'category':    │                   │
│                             │ 'Fêtes/Nouvel An',         │                   │
│                             │ 'dates': '12-31..01-01',   │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}, {'name':   │                   │
│                             │ 'Saint-Nicolas', 'match':  │                   │
│                             │ 'calendar', 'category':    │                   │
│                             │ 'Fêtes/Saint-Nicolas',     │                   │
│                             │ 'dates': '12-05..12-06',   │                   │
│                             │ 'pattern': '', 'kind':     │                   │
│                             │ None, 'categories': [],    │                   │
│                             │ 'per_photo': False,        │                   │
│                             │ 'score': None}]            │                   │
│ classify.ai                 │ {'url':                    │ config.toml       │
│                             │ 'http://host.docker.intern │                   │
│                             │ al:11434', 'model': '',    │                   │
│                             │ 'map_model': '',           │                   │
│                             │ 'samples_per_event': 3,    │                   │
│                             │ 'min_edge': 512,           │                   │
│                             │ 'image_edge': 768,         │                   │
│                             │ 'concurrency': 1,          │                   │
│                             │ 'timeout_seconds': 180.0,  │                   │
│                             │ 'retries': 2,              │                   │
│                             │ 'batch_size': 20,          │                   │
│                             │ 'confirm_above': 200,      │                   │
│                             │ 'seconds_per_photo': 4.5}  │                   │
│ classify.places             │ []                         │ défaut            │
│ classify.trip_min_km        │ 100.0                      │ config.toml       │
│ classify.trip_merge_gap_hou │ 48.0                       │ config.toml       │
│ rs                          │                            │                   │
│ classify.trip_merge_max_km  │ 120.0                      │ config.toml       │
│ sort.confirm                │ True                       │ config.toml       │
│ sort.junk_files             │ ['Thumbs.db',              │ config.toml       │
│                             │ 'desktop.ini',             │                   │
│                             │ '.DS_Store']               │                   │
│ inventory.blurry_below      │ 100.0                      │ config.toml       │
│ inventory.small_below       │ 1000                       │ config.toml       │
│ inventory.dark_below        │ 50.0                       │ config.toml       │
│ inventory.bright_above      │ 205.0                      │ config.toml       │
│ inventory.clipped_above     │ 0.25                       │ config.toml       │
│ places.tiles                │ https://tile.openstreetmap │ config.toml       │
│                             │ .org/{z}/{x}/{y}.png       │                   │
│ places.attribution          │ © OpenStreetMap            │ config.toml       │
│                             │ contributors               │                   │
│ places.nominatim_url        │ https://nominatim.openstre │ config.toml       │
│                             │ etmap.org                  │                   │
│ album.root                  │                            │ config.toml       │
└─────────────────────────────┴────────────────────────────┴───────────────────┘

Catégories d'extensions (--ext)
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Catégorie ┃ Extensions                                            ┃ Origine  ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ photo     │ avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif, │ intégrée │
│           │ tiff, webp                                            │          │
│ raw       │ arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw      │ intégrée │
│ video     │ 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg,   │ intégrée │
│           │ mpg, mts, ts, webm, wmv                               │          │
│ media     │ 3g2, 3gp, arw, avi, avif, bmp, cr2, cr3, dng, flv,    │ intégrée │
│           │ gif, heic, heif, jpe, jpeg, jpg, m2ts, m4v, mkv, mov, │          │
│           │ mp4, mpeg, mpg, mts, nef, orf, pef, png, raf, rw2,    │          │
│           │ srw, tif, tiff, ts, webm, webp, wmv                   │          │
└───────────┴───────────────────────────────────────────────────────┴──────────┘

Points de montage
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Montage               ┃ Dossier sur votre ordinateur ┃ État          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ /data/c/Photos        │ C:\Photos                    │ lecture seule │
│ /data/d/Ancien disque │ D:\Ancien disque             │ lecture seule │
│ /config               │ —                            │ monté         │
│ /journal              │ —                            │ monté         │
│ /quarantine           │ —                            │ monté         │
│ /reports              │ —                            │ monté         │
│ /cache                │ —                            │ monté         │
└───────────────────────┴──────────────────────────────┴───────────────┘

💡 Modifiez /config/config.toml pour changer ces réglages ; les options de ligne
de commande l'emportent.
```

- **Origine** dit d'où vient chaque valeur : `défaut`, `config.toml`, `environnement` ou
  `ligne de commande`.
- **Dossier sur votre ordinateur** montre le dossier Windows derrière chaque montage ; `—` pour
  un volume Docker comme le cache.

## Qui l'emporte ?

De la plus forte à la plus faible : les options de la ligne de commande, puis les variables
d'environnement, puis `config.toml`, puis les valeurs par défaut. `--prefer` sur la ligne de
commande remplace donc `preferred` du fichier pour ce lancement.

Les variables d'environnement s'appellent `MEDIA_HYGIENE_<SECTION>__<CLÉ>` (deux soulignés), par
exemple `-e MEDIA_HYGIENE_GENERAL__LOCALE=fr` dans `docker run` ; les listes s'écrivent en
tableau JSON, les tables en objet JSON qui remplace toute la table du fichier
(`MEDIA_HYGIENE_SCAN__CATEGORIES='{"documents": ["pdf", "docx"]}'`). Les listes de tables, comme
les règles de `classify` (`[[classify.rules]]`), se lisent dans `config.toml` seulement. Jusqu'à
la version 0.2, leur préfixe était `MEDIA_DEDUP_` : il fonctionne encore jusqu'à la version
0.4.0, avec un avertissement.

---

← [6. Seulement certains types de fichiers](06-file-types.md) · [Documentation](../README.md) · Suivant : **[8. Nettoyer](08-clean.md)** →
