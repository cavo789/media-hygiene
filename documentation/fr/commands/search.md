# `search` : retrouver une photo par ses mots

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `search` · 🇬🇧 [English](../../en/commands/search.md)

## En bref

**Retrouver une photo par ce dont vous vous souvenez : un mot, un lieu, une année, une
personne.**

`search` retrouve des photos par les mots que [`tags`](tags.md) leur a donnés et les noms donnés
dans [`people`](people.md), dans une page de votre navigateur : un champ, une grille des photos
trouvées, les meilleures d'abord, chacune avec son dossier, sa date et ses mots. Avec des mots
après la commande, il affiche à la place les premiers résultats en tableau. Les photos choisies
dans la page peuvent être **mises de côté** : le prochain [`clean --decisions`](clean.md) les
déplace en quarantaine, journalisé et annulable.

**Quand** : après [`tags`](tags.md) (et [`people`](people.md) pour les noms) ; à nouveau une
fois les nouvelles photos passées par `tags`.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr search
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | `/cache` (les mots de `tags`), vos dossiers (pour montrer les photos), et `-p 127.0.0.1:8088:8088` pour la page ; `/reports` pour mettre des photos de côté. |
| Écrit | Les petits aperçus de la grille, dans le cache ; les photos mises de côté, dans `decisions.json` des rapports. |
| Annuler | Rien à annuler dans la page : [`clean --decisions`](clean.md) déplace les photos mises de côté, [`undo`](undo.md) les remet. |
| Avec `mh` | `mh search`, `mh search durbuy ours`. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr search
```

Ouvrez <http://127.0.0.1:8088/>. `/` relance une recherche, les flèches se déplacent, un clic ou
Espace choisit une photo, Entrée ou un double clic la montre en grand (avec un lien vers
l'original), Échap la ferme. Filtres : années, une partie du chemin, les mots d'une seule source.
Ctrl+C, ou fermer son onglet, arrête la page.

Sans navigateur (WSL, un script), donnez les mots : `search durbuy ours` affiche les 20 premiers
fichiers en tableau.

## Mettre des photos de côté

Pour retirer toutes les photos de quelqu'un, ou d'un évènement : cherchez-les (`person:"Anne"`,
une année, un mot), choisissez-les (un clic ou Espace sur chacune, ou **Choisir les N fichiers
trouvés** : tous les fichiers que la recherche trouve, pas seulement les 240 affichés), puis
**Mettre de côté les fichiers choisis**.

- Rien n'est supprimé depuis la page. Le choix est enregistré aussitôt dans `decisions.json` de
  vos rapports, relu sur le disque et affiché avec son nombre et sa taille : *37 fichiers mis de
  côté (412 Mo), enregistrés dans … : 'clean --decisions' les déplace en quarantaine, et s'en
  souvient : si l'un d'eux revient (une nouvelle copie depuis le téléphone), l'audit le propose à
  nouveau.* Les photos
  mises de côté portent une étiquette rouge *à mettre de côté*.
- **Retirer de la mise de côté** en retire les fichiers choisis.
- Quand vous arrêtez la page, `search` propose l'étape suivante : `mh clean --decisions`. Il
  demande d'abord combien de fichiers et d'octets partent (à part des doublons), les déplace en
  quarantaine, journalisé ; [`undo`](undo.md) les remet, [`purge`](purge.md) libère la place.
- Un fichier modifié depuis votre choix (autre taille ou date) est laissé en place et listé dans
  le rapport du nettoyage ; un fichier d'un dossier protégé fait refuser tout le fichier, comme
  partout.
- Le même `decisions.json` garde ce que [`review`](review.md) a décidé : les deux sont gardés, et
  un seul `clean --decisions` applique tout.

## Ce que vous pouvez taper

| Vous tapez | Il trouve |
|---|---|
| `Durbuy ours` | Les photos qui ont les deux mots, quelle que soit leur source. |
| `noel`, `gateau` | `Noël`, `gâteau` : la casse et les accents ne comptent pas. |
| `bougies` | `bougie` aussi : les mots sont gardés au singulier. |
| `anniv*` | Chaque mot qui commence ainsi. |
| `"bord de mer"` | L'expression, ses mots dans cet ordre. |
| `place:durbuy` | Le mot parmi les lieux seulement ; aussi `vision`, `caption`, `folder`, `name` (le nom du fichier), `date`, `person`. |
| `anniversaire` | Aussi `Anniversaire Léa.mp4` : les mots d'un nom de fichier choisi comptent aussi (`IMG_1234` n'en donne aucun). |
| `neige 2008` | L'année est un mot de la date : la neige de 2008. |
| `Chloé montagne` | Les photos de Chloé avec « montagne » venu de n'importe quelle source, une fois son groupe nommé dans [`people`](people.md). |
| `person:chloe`, `person:"Mamie Jeanne"` | Le nom parmi les personnes seulement. Un nom que personne ne porte encore est signalé en une ligne. |
| `un chat sur un canapé` | Après [`tags --meaning`](tags.md) : les photos qui le montrent d'abord, même sans aucun de ces mots ([recherche par le sens](../reference-tags.md#retrouver-une-photo-par-ce-quelle-montre----meaning)). |
| `Chloé cuisine` | Après `tags --meaning` : les photos de Chloé seulement, les cuisines d'abord. |

## Options

| Option | Rôle |
|---|---|
| `MOTS` | Les mots à trouver, affichés en tableau au lieu d'ouvrir la page. |
| `--limit N` | Avec des mots : combien de fichiers le tableau liste au plus (20 par défaut). |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- Sans `/reports` (ou avec un dossier où l'outil ne peut pas écrire), **Mettre de côté les fichiers choisis** dit
  pourquoi et n'enregistre rien ; la recherche elle-même fonctionne.
- La recherche ne lit que le cache : relancez [`audit`](audit.md) puis [`tags`](tags.md) pour
  trouver les nouvelles photos.
- Sans `/cache`, ou avec un cache qu'aucun audit n'a encore rempli, il s'arrête et dit pourquoi.
- **Par le sens** : une fois que [`tags --meaning`](tags.md) a donné leurs vecteurs aux photos,
  la recherche les classe aussi par ce qu'elles montrent, et le dit au lancement (*Recherche par
  le sens : 52 318 photos peuvent être trouvées par ce qu'elles montrent.*). Le modèle est lu
  dans le cache, jamais téléchargé par `search`.
- Les noms des personnes viennent des visages du cache et des noms de `config.toml`, à chaque
  lancement : montez aussi `/config` pour les trouver. Rien d'autre à lancer après avoir nommé un
  groupe.

## Pour aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
- [Les tags : retrouver une photo par ses mots](../reference-tags.md#retrouver-une-photo-par-ses-mots--search)

## L'aide intégrée

<details>
<summary><code>search --help</code></summary>

<!-- capture: help-search.txt -->
```text
 Utilisation : media-hygiene search [OPTIONS] [words]...

 🔒 Lecture seule : ne modifie jamais vos photos. Retrouver des photos par
 leurs mots dans votre navigateur (ou en tableau) : les mots que 'tags' leur a
 donnés.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   words      <str>  Mots à trouver, affichés en tableau au lieu d'ouvrir la  │
│                     page : "bord de mer" une expression, anniv* un début de  │
│                     mot, place:durbuy parmi les lieux seulement (aussi       │
│                     vision, caption, folder, name, date, person).            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --limit          <int range> [x>=1]  Nombre maximal de fichiers listés dans  │
│                                      le tableau. Par défaut : 20.            │
│ --port           <int range> [x>=1]  Port de la page. docker run le publie   │
│                                      sous le même numéro sur votre           │
│                                      ordinateur, par exemple -p              │
│                                      127.0.0.1:9000:9000 pour --port 9000.   │
│                                      Par défaut :  port dans config.toml,    │
│                                      8088.                                   │
│ --help   -h                          Affiche ce message et quitte.           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
