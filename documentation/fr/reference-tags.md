# Les tags

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-tags.md)

`tags` donne à chaque photo et vidéo **des mots pour la retrouver** : « Durbuy », « ours »,
« anniversaire », « Noël », « neige ». Il lit ce que les audits ont appris, depuis le cache :
lancez d'abord un [audit](start/01-first-audit.md), avec `/cache` monté
([étape 2](start/02-keep-the-cache.md)). Les mots restent **dans le cache**, jamais dans vos
photos.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr tags
```

```text
🔒 Lecture seule : vos photos et vidéos ne sont pas touchées.
✅ 52 318 fichiers : 241 906 mots tirés de leurs dossiers, noms, dates et lieux.
💡 Indiquez un modèle de vision local (Ollama) dans [classify.ai] model pour ajouter ce que
montrent les photos : elles sont envoyées à son url, et seulement là.
```

Ensuite, [`search`](#retrouver-une-photo-par-ses-mots--search) retrouve les photos par ces mots
dans votre navigateur, et [`inventory`](reference-inventory.md) les liste dans sa dernière
colonne, **Tags**. [`xmp`](#emporter-les-mots-avec-les-photos--xmp) les écrit dans des fichiers compagnons `.xmp` que
d'autres applications lisent.

## D'où viennent les mots

| Source | Mots | Coût |
|---|---|---|
| Dossiers | Les mots des noms de dossiers que vous avez choisis : `2022/Durbuy - ours` donne `Durbuy`, `ours`. Les dossiers nommés par un appareil ou une application (`DCIM`, `100CANON`, `Camera`), les dates (`2019`, `Juillet 2019`) et les petits mots de liaison (`les`, `the`) sont écartés, comme pour [la copie gardée](clean/05-choose-the-kept-copy.md). | Secondes |
| Nom du fichier | Les mots d'un nom que vous avez choisi : `Anniversaire Léa.mp4` donne `Anniversaire`, `Léa` ; `2019-07-12 Plage (petite).jpg` donne `Plage`, `petite`. Un nom donné par un appareil ou une application (`IMG_1234.jpg`, `DSC00042.JPG`, `VID-20190712-WA0001.mp4`, `PXL_20230101_120000.jpg`, un simple nombre) ne donne rien, pas plus que sa part dans un nom plus long (`IMG_1234 Léa.jpg` donne `Léa`) : ce sont les noms que reconnaît [la copie gardée](clean/05-choose-the-kept-copy.md), `[keep] generated_names`. Les nombres, les dates, les mois et les petits mots de liaison sont écartés, comme pour les dossiers. Les vidéos aussi. | Secondes |
| Copies retirées | Les mots des dossiers et des noms des copies que [`clean`](clean/08-clean.md) a retirées, gardés sur la photo conservée : une photo gardée dans `DCIM` dont la copie était dans `Mariage Julie 2015` reçoit `Mariage`, `Julie`. Les mots que donnent déjà les dossiers et le nom de la photo ne sont pas répétés. Un [`undo`](clean/09-undo-history-purge.md) de ce nettoyage les retire : la copie a de nouveau son propre nom. | Secondes |
| Date | L'année, le mois, la saison (inversée sous l'équateur), les fêtes (Noël, Nouvel an, Saint-Nicolas, Saint-Valentin, Halloween, Pâques) et les noms de vos propres règles `calendar` et `date_range` ([trier, étape 6](sort/06-write-down-what-you-know.md#les-dates)). Une photo sans date prend l'année de son dossier (`Avril 2007`). | Secondes |
| Lieu | Le nom de votre lieu quand la position GPS s'y trouve ([trier, étape 9](sort/09-places-from-gps.md)), puis la ville la plus proche et son pays, hors ligne (GeoNames), quand elle est à moins de `town_km` (20 km). | Secondes |
| Modèle de vision | Une courte phrase et 5 à 10 mots sur ce que montre la photo (facultatif, ci-dessous). | Environ 2 s par photo |
| Personne | Les noms des personnes sur la photo, une fois leur groupe nommé dans [`people`](reference-people.md#nommer-les-groupes). Calculés par `search` à chaque lancement, depuis les visages et `config.toml` : `tags` ne les calcule pas, et ils ne sont jamais écrits dans les fichiers compagnons `.xmp`. | Aucun pour `tags` |

Ces mots sont recalculés à chaque passage : renommez un dossier ou un fichier, ou ajoutez une
règle, relancez `tags`.

## Les mots d'un modèle de vision local

Un modèle de vision voit bien les **scènes et les objets** (une pièce montée, des bougies, un
bonhomme de neige, une patinoire, une cathédrale) et lit le texte visible. Il ne connaît jamais
l'**occasion** (Pâques, Noël) ni le **lieu** (Durbuy, la Sicile) : c'est pourquoi les dossiers,
les dates et les lieux passent d'abord, et le modèle ne fait qu'y ajouter.

C'est le modèle de [trier, étape 8](sort/08-subjects-from-a-local-model.md) : installez-le, puis
indiquez-le dans `config.toml`.

```toml
[classify.ai]
url = "http://host.docker.internal:11434"
model = "qwen2.5vl:7b"
```

Avec Docker Engine (Linux, WSL), ajoutez `--add-host=host.docker.internal:host-gateway` à
`docker run`. Sans `model`, `tags` n'envoie jamais rien.

- **Vie privée** : chaque photo est envoyée, en JPEG de 768 pixels, à l'`url` de
  `[classify.ai]`, et seulement là. Gardez ce serveur sur votre propre ordinateur.
- **Une photo par ensemble** : les copies identiques partagent leurs mots, et une rafale prend
  ceux de sa photo la plus nette. Les quasi-doublons (une copie WhatsApp et son original, une
  vidéo réencodée) sont trouvés comme l'audit les trouve : la version que l'audit conserve est
  envoyée, et ses copies prennent ses mots, même une copie trop petite pour être envoyée. Les
  décisions de [`review --near`](commands/review.md) sont suivies : un groupe laissé tel quel est
  envoyé fichier par fichier, et quand vous avez gardé une autre version, c'est elle qui est
  envoyée.
- **Les vidéos par une image** : l'image montrée au milieu de la vidéo est envoyée, comme une
  photo ; les copies identiques d'une vidéo partagent ses mots. Les photos et vidéos plus
  petites que `min_edge` (512 pixels sur leur petit côté) ne sont pas envoyées.
- **Demandé une seule fois, pour `classify` aussi** : une règle `subject`
  ([trier, étape 8](sort/08-subjects-from-a-local-model.md)) lit la phrase et les mots que
  `tags` a déjà, quand le même modèle les a donnés, et les range seulement dans ses catégories :
  une photo décrite par `tags` n'est jamais renvoyée.
- **Les plus récentes d'abord** : la première nuit couvre déjà vos dernières années.
- **Ce qui lui est demandé** : une phrase et 5 à 10 mots, dans la langue de `[tags] language`
  (celle de l'interface par défaut) ; les personnes comme adulte, enfant, bébé ou groupe, jamais
  une relation (« mère », « sœur ») ni un nom.
- **Des mots nettoyés** : en minuscules, au singulier (`bougies` → `bougie`), une fois chacun ;
  les mots d'une ou deux lettres et ceux qui conviennent à toutes les photos (`sol`, `mur`,
  `floor`, `wall` : `[tags] stop_words`) sont écartés.

### Mesurer d'abord : `--sample`

```powershell
docker run --rm -it ... cavo789/media-hygiene --locale fr tags --sample 20
```

Il décrit 20 photos prises au hasard, affiche leur phrase, leurs mots et leur temps, puis
l'estimation d'une exécution complète. Leurs réponses sont gardées : l'exécution complète ne les
décrit pas à nouveau.

### La longue exécution

**Combien de temps** : environ 2 secondes par photo sur une carte graphique avec un modèle de
27 milliards de paramètres, soit environ 30 heures pour 50 000 photos, moins une fois les copies,
les rafales et les quasi-doublons comptés une seule fois. Au-delà de `confirm_above` photos (200), `tags` affiche
le nombre et la durée et demande d'abord ; `--yes` ne demande pas.

**La carte graphique pour lui seul** : quand un autre programme utilise la même carte (un autre
modèle dans Ollama), Ollama échange les modèles et une photo peut prendre de 10 à 30 secondes.
Laissez la carte à l'exécution seule, la nuit par exemple.

**Arrêtez quand vous voulez** : Ctrl+C laisse finir les photos en cours. Chaque réponse est
gardée aussitôt : le prochain passage de `tags` reprend là où celui-ci s'est arrêté.
`tags --no-describe` ne demande rien de nouveau au modèle : les mots des dossiers, des noms, des
dates et des lieux, et les réponses déjà dans le cache.

### Un dossier d'abord : `--path`

```powershell
docker run --rm -it ... cavo789/media-hygiene --locale fr tags --path "C:\Photos\2022"
```

Seulement les photos sous ce dossier (répétez `--path` pour plusieurs).

## Retrouver une photo par ses mots : `search`

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr search
```

Ouvrez <http://127.0.0.1:8088/> : un champ, une grille des photos trouvées, les meilleures
d'abord, chacune avec son dossier, sa date et ses mots. Tapez `/` pour chercher à nouveau,
déplacez-vous avec les flèches, Entrée montre l'image en grand (avec un lien vers l'original),
Échap la ferme. Filtres : années, une partie du chemin, les mots d'une seule source. Ctrl+C
arrête la page. Lecture seule 🔒 : elle ne change jamais un fichier ; seuls les petits aperçus de
la grille sont gardés dans `/cache`.

![La page de recherche : anniversaire tapé dans le champ Mots, à côté les filtres d'année, de chemin et de source, 8 fichiers trouvés ; une grille de photos d'anniversaire, chacune avec son nom, son dossier, sa date et ses mots Anniversaire, 2022, mai, printemps](images/search.webp)

| Vous tapez | Elle trouve |
|---|---|
| `Durbuy ours` | Les photos qui ont les deux mots, quelle que soit leur source. |
| `noel`, `gateau` | `Noël`, `gâteau` : la casse et les accents ne comptent pas. |
| `bougies` | `bougie` aussi : les tags sont gardés au singulier. |
| `anniv*` | Chaque mot qui commence ainsi : `anniversaire`, `anniv`. |
| `"bord de mer"` | L'expression, ses mots dans cet ordre. |
| `place:durbuy` | Le mot parmi les lieux seulement ; aussi `vision`, `caption` (la phrase du modèle), `folder` (dossier), `name` (nom du fichier), `former` (les dossiers et noms des copies retirées par `clean`), `date`, `person` (les noms de [`people`](reference-people.md)). |
| `neige 2008` | L'année est un mot de la date : la neige de 2008. |

Sans navigateur (WSL, un script), donnez les mots : `search durbuy ours` affiche les 20 premiers
fichiers en tableau (`--limit N` pour plus). La recherche ne lit que le cache : relancez `tags`
après un audit pour retrouver les nouvelles photos.

## Emporter les mots avec les photos : `xmp`

Les mots vivent dans le cache de cet outil. Pour les retrouver dans digiKam, darktable,
Lightroom ou Immich (bibliothèque externe), `xmp` les écrit dans des **fichiers compagnons**,
de petits fichiers `.xmp` à côté des photos : les photos elles-mêmes ne sont jamais modifiées.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr xmp --apply
```

Sans `--apply`, `xmp` montre seulement ce qu'il écrirait (les dossiers de photos peuvent alors
rester en `:ro`). Avec, les dossiers doivent être modifiables et `/journal` monté, comme pour
`clean`.

- **Ce qui est écrit** : les mots des sources de `xmp_sources` (`vision` et `place` par défaut :
  les mots des dossiers, des noms et des dates sont déjà dans le chemin ; ajoutez `name` ou
  `folder` pour les écrire aussi, `former` pour ceux des copies retirées par `clean`) dans `dc:subject`, la phrase du
  modèle dans `dc:description`.
- **Le lieu à part** : avec `place` dans `xmp_sources`, la ville va aussi dans `photoshop:City`,
  son pays dans `photoshop:Country` et votre premier lieu personnel (`[[classify.places]]`) dans
  `Iptc4xmpCore:Location`, les champs que digiKam, Lightroom et Immich affichent à part des
  mots-clés. Un nom qui est deux de ces lieux à la fois (Luxembourg, ville et pays ; un lieu à
  vous qui porte le nom de sa ville) remplit les deux champs. Un champ déjà rempli par une autre
  application garde sa valeur ; un champ que vous y avez vidé n'est pas rempli à nouveau. Après
  une mise à jour, relancez `tags` une fois : les lieux trouvés avant ne savent pas encore s'ils
  sont une ville ou un pays, et ne remplissent ces champs qu'ensuite.
- **Les personnes, seulement si vous le demandez** : avec `person` dans `xmp_sources` (jamais par
  défaut), les noms des personnes sur la photo ([`people`](reference-people.md)) vont dans
  `Iptc4xmpExt:PersonInImage`, le champ que lisent digiKam, Lightroom et Immich. `xmp` le dit
  avant d'écrire : les noms voyagent alors avec chaque copie des photos (un téléphone, un cloud,
  un disque partagé). Un nom écrit par une autre application reste ; retirez `person` et relancez
  `xmp --apply` pour reprendre les nôtres.
- **Une position, seulement si vous le demandez** : avec `[tags] xmp_folder_gps = true`, une photo
  sans GPS dans un dossier au nom d'une ville reçoit le centre de cette ville comme position,
  approximative ([`xmp`](commands/xmp.md#une-position-daprès-la-ville-du-dossier)).
- **Où** : `IMG_1.jpg.xmp` à côté de `IMG_1.jpg`. Un fichier compagnon déjà là (`IMG_1.jpg.xmp`,
  ou `IMG_1.xmp` quand il n'appartient qu'à cette photo) est complété, jamais remplacé : ses
  retouches, ses autres propriétés et ses propres mots restent ; la phrase n'est posée que s'il
  n'en a pas. Un fichier compagnon qui n'est pas du XMP lisible est listé et laissé tel quel.
- **Relancez-le** après `tags` : les mots que cet outil avait écrits et ne donne plus sont
  retirés, un mot que vous avez retiré dans une autre application n'est pas remis, et un fichier
  compagnon déjà à jour n'est pas réécrit.
- **Laissés de côté** : les dossiers protégés (jamais écrits), et les fichiers qui ont une copie
  identique : deux copies auraient des fichiers compagnons divergents ; lancez d'abord `clean`,
  seule la copie gardée en reçoit un.
- **Sûr** : chaque fichier compagnon est journalisé avant d'être écrit, écrit dans un fichier
  temporaire puis renommé (jamais par-dessus un fichier apparu entre-temps), relu et vérifié.
  Celui d'une autre application est d'abord copié en quarantaine. `undo <exécution>` supprime les
  fichiers compagnons créés par cet outil et remet les autres octet pour octet, sauf s'ils ont été
  modifiés depuis : ils sont alors gardés, et `undo` dit pourquoi.
- **Copie gardée** : un fichier compagnon écrit par `xmp` seul ne compte pas comme des retouches
  quand `clean` choisit la copie à garder ([fichiers compagnons](reference-sidecars.md)).

## Réglages

```toml
[tags]
language = ""   # "en", "fr", ou vide pour la langue de l'interface
# stop_words = ["sol", "mur", "intérieur", "floor", "wall", "indoor"]
town_km = 20
xmp_sources = ["vision", "place"]   # les mots écrits dans les fichiers compagnons .xmp
```

Une liste `stop_words` écrite ici remplace celle intégrée. Le modèle lui-même se règle dans
`[classify.ai]` (model, url, `min_edge`, `confirm_above`).

## Pourquoi pas dans les photos

Écrire les mots dans un JPEG change ses octets : son empreinte, sa date, et deux copies
identiques cesseraient de l'être si une seule était étiquetée. Cela casserait ce sur quoi cet
outil repose, et mettrait les originaux en risque. Les mots restent dans le cache, où `search`
et `inventory` les lisent, et ne vont dans des fichiers compagnons à côté des photos que si vous
le demandez (`xmp`).
