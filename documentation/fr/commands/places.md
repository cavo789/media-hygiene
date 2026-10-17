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
| Écrit | Des entrées `[[classify.places]]` dans `config.toml`, en gardant vos commentaires et le reste du fichier. |
| Annuler | Supprimez un lieu sur la carte, ou ses lignes dans `config.toml`. |
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
- **Cliquez sur le nombre de photos** (par exemple « 11 photos ») sur une ligne de cette liste
  pour voir les photos du groupe (24 au plus) et reconnaître le lieu avant de le nommer ;
  survolez une photo pour voir où elle a été prise. Cliquez à nouveau, ou sur ✕, pour les refermer.
- **Repliez une liste** en cliquant sur son titre : *Vos lieux (10)* se replie d'elle-même à
  partir de 8 lieux, pour que les groupes restent à portée ; votre navigateur retient votre choix.
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
