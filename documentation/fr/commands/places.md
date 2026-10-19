# `places` : nommer vos lieux sur une carte

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `places` · 🇬🇧 [English](../../en/commands/places.md)

## En bref

**Nommer sur une carte les lieux qui comptent pour vous (la maison, chez papy, un village), pour
que `classify` range vos photos par lieu et par voyage.**

Les téléphones récents écrivent **où** chaque photo a été prise. `places` montre ces positions
sur une carte dans votre navigateur, regroupées en cercles, et enregistre les lieux que vous
nommez dans `config.toml`, où les règles `place` et `trip` de [`classify`](classify.md) les
utilisent.

**Quand** : avant [`classify`](classify.md), une fois qu'un audit lancé avec le [cache](../reference-glossary.md#cache) a lu les
positions ; à nouveau chaque fois qu'un nouveau lieu compte.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr places
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : les positions viennent du cache. Les dossiers de photos, en lecture seule (`:ro`), montrent les photos d'un groupe ; sans eux, la carte marche mais ne montre aucune photo. |
| Il faut | `/cache` (les positions notées par les audits, et les aperçus), `/config` (où les lieux sont enregistrés), vos dossiers de photos en lecture seule, et `-p 127.0.0.1:8088:8088`. |
| Écrit | Des entrées `[[classify.places]]` dans `config.toml`, en gardant vos commentaires et le reste du fichier ; aussi les positions des dossiers (`[[places.folders]]`), les noms qui ne sont pas des villes (`folder_town_ignore`), les groupes écartés (`[[places.ignored]]`) et les photos données à la main à un lieu (`[[classify.place_photos]]`). Chaque changement est relu dans le fichier avant que la page ne le montre. |
| Annuler | Supprimez un lieu sur la carte, ou ses lignes dans `config.toml` ; **Rétablir** ce que vous avez écarté ; ✕ sur une photo donnée à la main, dans l'éditeur de son lieu. |
| Avec `mh` | `mh places` : vos dossiers de photos sont montés en lecture seule et le port est publié pour vous. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr places
```

Ctrl+clic sur l'adresse qu'il affiche, `http://127.0.0.1:8088/`. Ctrl+C arrête la carte.

![La carte des lieux : les tuiles OpenStreetMap du parc du Cinquantenaire à Bruxelles, le cercle des photos prises là, le cercle vert du lieu Parc du Cinquantenaire qui vient d'être enregistré, et à gauche la liste des lieux et des plus grands groupes sans nom](../images/places.webp)

## Sur la carte

- **Les cercles** sont vos photos avec une position GPS, regroupées par 200 mètres environ. La
  liste de gauche donne d'abord les plus gros groupes sans nom : la maison est en général le
  premier.
- **Cliquez sur le nombre de photos** (par exemple « 🖼 11 photos », ou « 🎞 1 vidéo » pour un
  groupe de vidéos) sur une ligne de cette liste : un **tiroir** s'ouvre sur la droite de la carte,
  toujours au même endroit, avec les photos du groupe (24 au plus, et ses vidéos par leur nom) pour
  reconnaître le lieu avant de le nommer. **Nommer ce lieu** est en haut, avant les photos. Les
  photos sont regroupées par dossier, sous le chemin du dossier (`C:\Photos\2014\Geer`, son nom
  en gras) : un nom de dossier dit souvent le lieu ou l'événement. Survolez une photo pour voir où
  elle a été prise ; cliquez dessus pour la voir en grand, avec son chemin complet (← et → pour les
  autres, Échap pour revenir à la grille). La ligne cliquée reste en surbrillance ; cliquez-la à
  nouveau, sur ✕ ou sur Échap pour fermer le tiroir.
- **Repliez une liste** en cliquant sur son titre : *Vos lieux (10)* se replie d'elle-même à
  partir de 8 lieux, pour que les groupes restent à portée ; votre navigateur retient votre choix. *Vos lieux* est triée par nom,
  sans tenir compte des majuscules ni des accents, la maison (🏠) d'abord ; le fichier garde son
  propre ordre.
- **Dossiers au nom d'une ville** liste les dossiers dont le nom est celui d'une ville
  (`Douarnenez`, `Saint-Jean de Luz`) et qui contiennent des photos sans GPS : *📁 Douarnenez —
  37 photos sans GPS*. Cliquez sur l'un d'eux : la carte va sur la ville, un repère vert marque
  son centre et le même tiroir montre ses photos, regroupées par dossier, avec **Enregistrer cette
  position**, **Oublier sa position** et **Pas une ville** en haut. Faites glisser le repère là où
  elles ont été prises (la plage, pas la mairie) et cliquez sur **Enregistrer cette position** : elle va dans
  `config.toml` sous `[[places.folders]]`, relue et affichée avec 📌.
  [`xmp`](xmp.md#une-position-daprès-la-ville-du-dossier) écrit ensuite cette position dans les
  fichiers `.xmp` des photos. **Oublier sa position** la retire ; **Pas une ville** ajoute le nom
  du dossier à `[classify] folder_town_ignore` (un dossier `Martin` est un prénom, pas Martin en
  Slovaquie). Un dossier enregistré, renommé ou déplacé depuis, affiche ⚠ *introuvable* :
  rendez-lui son nom, ou oubliez sa position.

  La liste a deux sous-listes, chacune avec son nombre : **À placer** (📁, ouverte) et **Placés**
  (📌, repliée ; les dossiers introuvables, ⚠, en tête). Chacune est triée par le nom affiché,
  sans tenir compte des majuscules ni des accents (*Écluse* parmi les E) ; enregistrer une
  position fait passer la ligne de l'une à l'autre et la fait clignoter, **Oublier sa position**
  la ramène. Les dossiers écartés comme *pas une ville* ne sont dans aucune. **Tapez un nom** dans
  la zone en haut de la liste pour filtrer les deux sous-listes au fil de la frappe (le nom
  affiché et le chemin du dossier ; les nombres se lisent *3 / 41*) ; Échap vide la zone.
- **N'importe quel dossier**, replié sous les dossiers au nom d'une ville, liste chaque dossier
  de l'index comme [`browse`](browse.md) les montre (lu dans `/cache`, sans parcourir le disque) :
  vos dossiers montés ouverts, les autres fermés (▸ en ouvre un). Chaque ligne compte les photos
  et vidéos sans GPS du dossier et de ses sous-dossiers : *📁 Mariage Julie — 42 photos sans GPS* ;
  un dossier dont toutes les photos ont leur GPS est grisé. Cliquez sur un dossier qui ne porte le
  nom d'aucune ville (un mariage, des vacances) : le même tiroir montre ses photos sans GPS et un
  repère vert au milieu de la carte ; **cliquez sur la carte** ou faites glisser le repère là où
  elles ont été prises, puis **Enregistrer cette position**. Elle est enregistrée comme pour un
  dossier au nom d'une ville (`[[places.folders]]`, relue, 📌) et le dossier passe dans **Placés** ;
  ses sous-dossiers reçoivent aussi cette position, sauf s'ils ont la leur. La zone du haut filtre
  les dossiers au fil de la frappe (nom ou chemin, en liste à plat). Un dossier renommé ou déplacé
  depuis le dernier audit est refusé (relancez `audit`, puis placez-le sous son nouveau nom) ; une
  fois enregistré, renommé ou déplacé plus tard (par vous dans l'Explorateur, ou par
  [`sort`](sort.md)), il s'affiche ⚠ *introuvable* dans **Placés**, et `xmp` le signale.
- **✕ au bout d'une ligne** l'écarte d'un clic, sans question (Rétablir l'annule) :
  - sur un groupe (*Pas un lieu qui mérite un nom* : deux enfants dans une voiture), le groupe
    quitte la liste et la carte, et le suivant remonte. Il est enregistré comme un cercle de
    150 mètres autour de son milieu (`[[places.ignored]]`, `radius_m` à changer à la main) : un
    audit suivant qui déplace le milieu de quelques mètres le retrouve, et tout groupe dans ce
    cercle part avec lui. **✕ Écarter ce groupe**, dans son tiroir, fait la même chose ;
  - sur un dossier au nom d'une ville (*Léo* est le chat, pas une ville), son nom va dans
    `[classify] folder_town_ignore`, comme **Pas une ville** dans le tiroir : ce nom n'est plus
    jamais lu comme une ville, dans aucun dossier. Un dossier dont la position est enregistrée
    (📌) n'a pas de ✕ : **Oublier sa position** reste dans son tiroir.

  La liste **Écartés de la carte**, repliée, en bas, donne les deux, chacun avec **Rétablir**.
  [`classify`](classify.md) ne lit pas les groupes écartés : un tel groupe est simplement sans
  nom (la ville d'une règle `trip` le nomme toujours).
- **Donner ces photos à…**, dans le tiroir d'un groupe, quand ses photos ont été prises dans un
  lieu déjà nommé mais que leur GPS dit ailleurs (un téléphone à l'intérieur note souvent une
  position à quelques rues de là) : choisissez le lieu, le plus proche d'abord avec sa distance
  (*Geer — 1,4 km*). Toutes les photos du groupe lui sont données, sauf celles du tiroir que vous
  décochez (une vraiment prise dans le village). Ces photos seulement : pas de cercle plus grand
  (il nommerait tout le village) ni de deuxième zone (une vraie photo prise à cet endroit serait
  nommée aussi). Elles sont enregistrées dans `[[classify.place_photos]]` par leur **contenu**
  (taille et SHA-256, le chemin seulement pour vous) : déplacées ou renommées depuis (`sort`,
  `undo`, un dossier renommé dans l'Explorateur), elles sont retrouvées ; une photo modifiée
  depuis (nouveau contenu) revient à son GPS. Le nombre du groupe baisse (toutes données, il
  quitte la liste) ; l'étiquette du lieu dit *+ 3 photos placées à la main*, et son éditeur les
  liste, chacune avec ✕ pour la reprendre. Renommer le lieu les garde ; le supprimer demande, et
  les emporte avec lui.
- **Un lieu n'est pas une ville.** Il sert pour un endroit que la liste des villes ne connaît pas
  (la maison, chez les grands-parents, le bureau) : [`classify`](classify.md) nomme déjà les
  villes d'après la liste GeoNames. Tapez un nom pareil à celui d'une ville à moins de 10 km
  environ (*Blankenberge*) et une indication le dit sous le nom ; le lieu porte ⓘ dans *Vos
  lieux*. Ce n'est qu'une indication, l'enregistrement fonctionne : gardez un tel lieu pour des
  frontières exactes (une zone OpenStreetMap) ou un autre nom.
- **Cliquez sur un cercle, ou n'importe où**, pour nommer un lieu ; réglez son rayon avec le
  curseur, déplacez son repère. Cochez **Maison** pour votre domicile : les voyages se mesurent
  depuis lui.
- **Chercher une ville** cherche parmi les villes livrées avec l'image, hors ligne.
- **Chercher sur OpenStreetMap** trouve un village, un quartier ou un parc avec son contour : une
  photo lui appartient alors quand elle a été prise à l'intérieur.
- **Enregistrer** écrit le lieu dans `config.toml` aussitôt ; sa ligne clignote dans *Vos lieux*.
  Cliquez sur un lieu pour le déplacer, le renommer ou le supprimer.

## Options

| Option | Rôle |
|---|---|
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Ce qui quitte votre ordinateur

Aucune position, aucune photo, aucune liste de lieux. Les photos d'un groupe sont montrées par
l'outil lui-même, depuis vos dossiers ; leurs aperçus restent dans `/cache`. La carte charge des **tuiles** (les zones
que vous regardez) depuis le serveur de `[places] tiles` ; **Chercher sur OpenStreetMap** envoie
**le texte que vous avez tapé**, sur votre clic seulement, à `[places] nominatim_url` (vide, cette
recherche est désactivée). `classify` ne va jamais en ligne.

## Bon à savoir

- Un nom de lieu devient un nom de dossier : deux lieux ne peuvent pas partager un nom, et les
  caractères que Windows refuse sont refusés.
- Les lieux ne font rien tout seuls : ajoutez une règle `place` ou `trip` dans
  `[[classify.rules]]`. Une règle `trip` demande un lieu avec `home = true`.
- Les lieux peuvent aussi s'écrire à la main dans `config.toml`, la latitude et la longitude
  copiées depuis n'importe quelle carte.

## Pour aller plus loin

- [Trier, étape 9 : lieux et voyages d'après le GPS](../sort/09-places-from-gps.md)
- [Trier, étape 6 : les règles](../sort/06-write-down-what-you-know.md)

## L'aide intégrée

<details>
<summary><code>places --help</code></summary>

<!-- capture: help-places.txt -->
```text
 Utilisation : media-hygiene places [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Nommer vos lieux sur une
 carte des endroits où les photos ont été prises ; enregistrés dans config.toml
 pour les règles 'place' et 'trip'.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut : 8088.                       │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
