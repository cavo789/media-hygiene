# Trier en bref : le parcours complet

[Documentation](../README.md) › Trier en bref · 🇬🇧 [English](../../en/sort/quick-guide.md)

Tout ce que l'outil sait faire pour **ranger** vos photos et vidéos, puis pour les **retrouver**,
dans l'ordre, une étape à la fois, prêt à copier dans **PowerShell**. Chaque étape tient en
quelques lignes et renvoie à sa page détaillée, si vous voulez comprendre. Arrivé en bas, vous
avez fait le tour : [la dernière section](#vous-avez-fait-le-tour) reprend chaque commande et
l'étape qui la montre. Remplacez `C:\Photos` par votre dossier.

Le principe : `classify` **propose** une place pour chaque photo et vidéo (`année/catégorie` par
défaut), vous corrigez la proposition, et seul `sort` déplace les fichiers. Rien ne bouge avant,
et `sort` peut être annulé. Les étapes marquées *facultatif* peuvent être sautées : le parcours
continue sans elles.

> 🤖 **IA locale requise** : ce signe marque les seules commandes qui ne fonctionnent qu'avec un
> modèle de vision installé sur votre ordinateur ([Ollama](https://ollama.com), étape 7). Sans
> lui, sautez-les : tout le reste du parcours fonctionne, rien ne vous l'impose.

- **Ranger** (étapes 1 à 11) : une proposition, vos corrections, ce que vous savez (dates,
  lieux, personnes, sujets), puis le tri et les albums.
- **Retrouver** (étapes 12 à 15) : « Chloé en vacances à la montagne », par des mots, dans votre
  navigateur, dans d'autres logiciels photo ou dans Excel.

## 0. Avant de commencer

**Nettoyez d'abord les doublons** ([nettoyer en bref](../clean/quick-guide.md)) : sinon les deux
copies d'une photo sont triées. La commande `mh` écrite pour le nettoyage sert aussi ici ; sinon,
écrivez-la une fois : [nettoyer en bref, étape 0](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh).
Dans un nouveau terminal, rechargez-la :

```powershell
. "$HOME\media-hygiene\mh.ps1"
```

## Ranger

## 1. Demander une proposition

```powershell
mh classify
```

Rien n'est modifié : `mh` monte vos dossiers en lecture seule (`:ro`). `classify` date chaque
fichier (EXIF, nom, dossier), regroupe les photos prises à peu d'intervalle en **événements**,
et propose un dossier pour chacun. À la fin, deux fichiers dans un nouveau dossier
`<date>-classify` de vos rapports :

- `classify.xlsx`, le classeur, à ouvrir dans Excel ou LibreOffice : c'est là que vous
  **modifiez** ;
- `report.html`, le rapport, à ouvrir dans votre navigateur : c'est là que vous **regardez** les
  photos.

Une grande collection ? `mh classify --year 2016` propose une année à la fois. Détails :
[proposer une arborescence](04-classify.md).

## 2. Corriger la proposition dans le classeur

Ouvrez les deux côte à côte. Seules les cellules **jaunes** du classeur se modifient.

1. **Commencez par la feuille Événements** : les plus grands d'abord. Tapez un **Nom**
   (`Italie 2023`) : il devient le dossier de l'événement. Nommer les dix premières lignes règle
   souvent l'essentiel de la collection.
2. Pour comprendre un événement, cherchez son identifiant dans le rapport : ses dates, ses
   aperçus, d'où viennent ses photos.
3. Un fichier mal placé ? Feuille Fichiers, colonne **Dossier final** (`2016/Kermesse`).
4. **Enregistrez et fermez** le classeur.

Détails : [revoir la proposition](05-review-the-proposal.md).

## 3. … ou dans le navigateur (facultatif)

Plutôt une photo à l'écran qu'un tableur ? Les mêmes événements, un à la fois, avec leurs photos :

```powershell
mh review-sort
```

Ouvrez `http://127.0.0.1:8088/` (Ctrl+clic). <kbd>Entrée</kbd> accepte le nom et la catégorie
et passe au suivant, <kbd>E</kbd> tape un nom, <kbd>O</kbd> envoie les photos choisies ailleurs,
<kbd>V</kbd> accepte d'un coup toutes les propositions sûres. Vos choix vont dans
`sort-decisions.json`, à côté du classeur, jamais dedans : `sort` lit les deux, et une même ligne
modifiée des deux côtés lui est signalée, jamais tranchée en silence. Détails : [nommer les
événements dans le navigateur](11-name-events-in-the-browser.md).

## 4. Écrire ce que vous savez (facultatif)

Vos voyages, vos fêtes, vos dossiers existants : écrits une fois comme règles dans
`$HOME\media-hygiene\config\config.toml`, ils servent à chaque `classify`. Par exemple :

```toml
[[classify.rules]]
name = "Italie 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Vacances et sorties/Italie 2023"

[[classify.rules]]
name = "Noël"
match = "calendar"
dates = "12-24..12-26"
category = "Fêtes/Noël {year}"
```

| `match` | Reconnaît |
|---|---|
| `existing_folder` | Un nom de dossier que vous avez choisi (`2019/Vacances à la mer`). |
| `calendar`, `date_range` | Des jours qui reviennent chaque année (anniversaires, Noël), ou une seule fois (un voyage). |
| `kind` | Les captures d'écran, les images reçues par une messagerie, les films téléchargés. |
| `path`, `camera` | Un mot dans le chemin, une marque d'appareil (un drone, une caméra sport). |
| `place`, `trip`, `folder_town` | Vos lieux, vos voyages, les villes nommées par vos dossiers : étape 5. |
| `person` | Quelqu'un que vous avez nommé : étape 6. |
| `subject` | Ce que voit un modèle de vision local : étape 7. |
| `other_category` | Tout ce qu'aucune règle au-dessus n'a reconnu. |

Les règles sont lues dans l'ordre : la première sûre décide. Votre propre arborescence se règle
dans `[classify]` : `layout = "{year}/{month}"` (par mois), `target` (construire ailleurs),
`leave` (un dossier jamais trié). Détails : [écrire ce que vous savez](06-write-down-what-you-know.md),
[votre propre structure](04-classify.md#votre-propre-structure).

## 5. Les lieux et les voyages, grâce au GPS (facultatif)

Les téléphones récents écrivent où chaque photo a été prise ; l'audit dit combien des vôtres ont
une position. Nommez vos lieux sur une carte :

```powershell
mh places
```

Ouvrez `http://127.0.0.1:8088/` : les cercles sont vos photos, les plus grands groupes sans nom
d'abord. Cliquez, nommez (« Maison », « Chez papy »), réglez le rayon, cochez **Maison** pour la
vôtre, **Enregistrer** : le lieu est écrit dans `config.toml`. Un village ou un parc entier ?
**Chercher sur OpenStreetMap** prend son contour. Puis trois règles :

```toml
[[classify.rules]]
name = "Mes lieux"
match = "place"

[[classify.rules]]
name = "Voyages"
match = "trip"

[[classify.rules]]
name = "Villes des dossiers"
match = "folder_town"
```

`place` range dans le nom du lieu (`2023/Maison`), `trip` nomme chaque voyage à plus de 100 km de
la maison d'après son pays et sa ville (`2023/Italie/Turin`), `folder_town` lit les dossiers
nommés comme une ville (`2017\Durbuy`). Les villes sont nommées hors ligne : aucune position ne
quitte votre ordinateur. Détails : [lieux et voyages grâce au GPS](09-places-from-gps.md).

## 6. Les personnes (facultatif)

Aucune IA à installer : l'outil apporte ses propres modèles de visages (39 Mo, téléchargés
une fois). Nommez une fois les visages de vos photos ; ils servent à ranger (ici) et à retrouver
(étape 13). Trouver les visages prend du temps la première fois : mesurez d'abord, puis lancez
la page.

```powershell
mh people --sample 200
mh people
```

Ouvrez `http://127.0.0.1:8088/` : les visages qui se ressemblent sont regroupés, les plus grands
groupes d'abord. **Tapez un nom** sur un groupe, Entrée : il est écrit dans `config.toml`. `x`
choisit plusieurs groupes de la même personne, × retire un visage, `i` ignore des inconnus, `y`
confirme une suggestion « Chloé ? ». Nommer les dix plus grands groupes suffit souvent. Pour
ranger les événements où quelqu'un figure :

```toml
[[classify.rules]]
name = "Avec Chloé"
match = "person"
names = ["Chloé"]
category = "Personnes/Chloé"
```

Placez-la **sous** vos règles de dates et de lieux : sinon elle prend tout événement où Chloé
figure. Les visages restent dans le cache, jamais envoyés ; `mh people --forget` les supprime
tous. Plus tard, `mh audit --people` cherche les visages des nouvelles photos avec l'audit.
Détails : [trier par personne](10-sort-by-person.md), [les personnes](../reference-people.md).

## 7. Les sujets, avec une IA locale (facultatif)

> 🤖 **Toute cette étape demande Ollama installé sur votre ordinateur.** Sans lui, sautez-la :
> les dates, les lieux et les personnes rangent déjà l'essentiel.

Les photos dans des dossiers qui ne portent qu'une date (`DCIM`, `Juillet 2016`) n'ont pas de
sujet. Un modèle de vision **sur votre ordinateur** peut dire ce qu'elles montrent :

1. Installez [Ollama](https://ollama.com), puis un modèle qui voit les images :
   `ollama pull qwen2.5vl:7b`.
2. Indiquez-le dans `config.toml`, avec une règle `subject`, en bas de la liste :

   ```toml
   [classify.ai]
   url = "http://host.docker.internal:11434"
   model = "qwen2.5vl:7b"

   [[classify.rules]]
   name = "Sujet"
   match = "subject"
   categories = [
       "École = classe, excursions, spectacles et fêtes de l'école",
       "Animaux = un animal de compagnie ou un animal comme sujet principal",
   ]
   ```

3. 🤖 Mesurez le coût sur quelques photos : `mh classify --sample 50`.

Seules les photos qu'aucune autre règle n'a rangées sont envoyées, quelques-unes par événement,
au seul `url` que vous indiquez. Avec WSL ou Linux sans Docker Desktop, voyez la page détaillée.
Détails : [nommer les sujets avec un modèle local](08-subjects-from-a-local-model.md).

## 8. Relancer la proposition

Après vos règles, vos lieux, vos personnes, relancez l'étape 1 :

```powershell
mh classify
```

Les modifications déjà faites dans l'ancien classeur et dans `review-sort` sont reprises. Le
tableau *Pourquoi* compte les fichiers que chaque règle a décidés ; une règle listée sous
*Règles qui n'ont rien décidé* est placée trop bas, ou ne reconnaît rien. Corrigez encore
(étapes 2 et 3), autant de fois qu'il le faut : rien ne bouge avant `sort`.

## 9. Trier

```powershell
mh sort
```

Pour `sort`, `mh` monte vos dossiers en écriture (`sort` déplace des fichiers) et ajoute le
journal et la quarantaine. `sort` prend le classeur du dernier `classify`, le vérifie, dit combien de
modifications il a lues (pas assez ? le classeur n'était pas enregistré) et demande
confirmation : répondez `o`. Il finit en prouvant que rien n'est perdu : autant de fichiers,
de la même taille, avant et après. Détails : [trier](07-sort.md).

## 10. Vérifier, ou annuler

```powershell
explorer "C:\Photos"
```

Vous changez d'avis ? `mh undo` : chaque fichier revient où il était. Un `classify` relancé après
un tri ne propose pas ailleurs ce qui est déjà rangé. Détails : [changer d'avis](07-sort.md#changer-davis).

## 11. Les albums (facultatif)

Une photo de Noël qui est aussi parmi vos plus belles ? Un album la met dans un second dossier
sans la copier : un lien physique, aucune place prise.

```powershell
mh album "Noël" --category Noël
mh album "Noël" --category Noël --apply
```

La première ligne montre ce qu'il ferait, la seconde crée l'album dans `C:\Photos\Albums\Noël`.
Ce qu'il rassemble : `--category`, `--event`, `--rule`, ou `--rating 4` (au moins 4 étoiles dans
Windows), ensemble si vous voulez (`--category Noël --rating 4`). `mh undo` supprime ses liens,
jamais une photo. Détails : [albums](12-albums.md).

## Retrouver

## 12. Donner des mots à vos photos

```powershell
mh tags
```

En quelques secondes, chaque photo et vidéo reçoit les mots de ses dossiers et de son nom
(`2022/Durbuy - ours` donne `Durbuy`, `ours`), de sa date (année, mois, saison, Noël, vos règles
de dates) et de son lieu (votre lieu, la ville et le pays les plus proches). Ils restent dans le
cache, jamais dans vos photos.

Cette commande ne demande aucune IA. Avec Ollama ([étape 7](#7-les-sujets-avec-une-ia-locale-facultatif)),
la même commande ajoute aussi ce que **montre** chaque photo (« montagne », « neige »,
« gâteau ») :

> 🤖 **IA locale requise** : seulement si `[classify.ai] model` est rempli dans `config.toml`.
> Sinon, `tags` le dit en une ligne et s'en tient aux dossiers, noms, dates et lieux.

```powershell
mh tags --sample 20
mh tags
```

Environ 2 secondes par photo, donc souvent une nuit ou plus : `--sample 20` mesure d'abord ;
Ctrl+C arrête, le suivant reprend, les plus récentes d'abord. Ses réponses servent aussi à la
règle `subject`, jamais demandées deux fois.
Détails : [les tags](../reference-tags.md).

## 13. Retrouver une photo : `search`

```powershell
mh search
```

Ouvrez `http://127.0.0.1:8088/` : tapez ce dont vous vous souvenez, la grille montre les photos,
les meilleures d'abord ; Entrée en agrandit une. Filtres : années, une partie du chemin, une
source de mots.

| Vous tapez | Elle trouve |
|---|---|
| `Chloé montagne` | Chloé (étape 6) sur une photo où « montagne » vient d'un dossier ou d'un nom (`Vacances montagne`), ou, 🤖 avec une IA locale, de ce que montre la photo (étape 12). |
| `person:"Mamie Jeanne"` | Le nom parmi les personnes seulement. |
| `neige 2008` | La neige de 2008 : l'année est un mot de la date. |
| `place:durbuy` | Le mot parmi les lieux seulement. |
| `anniv*`, `"bord de mer"` | Un début de mot, une expression. |

Sans navigateur, `mh search Chloé montagne` affiche les premiers résultats en tableau. De
nouvelles photos ? `mh audit` puis `mh tags` d'abord. Détails : [`search`](../commands/search.md).

## 14. Emporter les mots dans un autre logiciel photo (facultatif)

Vous voulez les mêmes mots dans digiKam, darktable, Lightroom ou Immich ?

```powershell
mh xmp
mh xmp --apply
```

La première ligne montre ce qu'il écrirait ; la seconde écrit un fichier compagnon `.xmp` à côté
de chaque photo (`IMG_1.jpg.xmp`) : la photo elle-même n'est jamais modifiée, un `.xmp` déjà là
est complété, jamais remplacé. Les noms des personnes n'y vont que si vous ajoutez `person` à
`[tags] xmp_sources`. `mh undo` retire ce qu'il a écrit. Détails : [emporter les mots avec les
photos](../reference-tags.md#emporter-les-mots-avec-les-photos--xmp).

## 15. Répondre à vos propres questions dans Excel (facultatif)

```powershell
mh inventory
```

Un classeur `inventory.xlsx`, dans vos rapports : chaque photo et vidéo avec sa date, son
appareil, sa position, sa taille, des mots de qualité (*flou*, *petit*) et d'exposition
(*sombre*, *clair*), et ses mots de `tags`. Lu depuis le cache seul, en secondes : filtrez,
triez, comptez. `--format csv` pour un fichier CSV. Détails : [le classeur
d'inventaire](../reference-inventory.md).

## Plus tard : de nouvelles photos

Le même chemin, en plus court, car le cache se souvient de tout : `mh audit` et `mh clean`
([nettoyer en bref](../clean/quick-guide.md)), `mh people` pour les nouveaux visages, `mh tags`,
puis `mh classify`, le classeur et `mh sort`. Ce qui est déjà rangé reste à sa place. Perdu ?
`mh status` dit où vous en êtes, et si la dernière proposition a été triée.

## Vous avez fait le tour

Chaque commande du tri et de la recherche, et l'étape de cette page qui la montre :

| Commande | Étape | Ce qu'elle fait |
|---|---|---|
| [`classify`](../commands/classify.md) | 1, 4, 7, 8 | Propose une place pour chaque fichier, sans rien modifier ; 🤖 la règle `subject` et `--sample` demandent une IA locale. |
| [`review-sort`](../commands/review-sort.md) | 3 | Nomme les événements dans le navigateur. |
| [`places`](../commands/places.md) | 5 | Nomme vos lieux sur une carte. |
| [`people`](../commands/people.md) | 6 | Trouve et nomme les visages ; `--forget` les supprime. |
| [`sort`](../commands/sort.md) | 9 | Déplace les fichiers comme le dit le classeur. |
| [`undo`](../commands/undo.md) | 10, 11, 14 | Annule un tri, un album, des fichiers `.xmp`. |
| [`album`](../commands/album.md) | 11 | Une photo dans plusieurs dossiers, sans copie. |
| [`tags`](../commands/tags.md) | 12 | Donne des mots à chaque photo et vidéo ; 🤖 ce qu'elles montrent, avec une IA locale seulement. |
| [`search`](../commands/search.md) | 13 | Retrouve une photo par un mot, un lieu, une année, une personne. |
| [`xmp`](../commands/xmp.md) | 14 | Écrit les mots dans des fichiers compagnons `.xmp`. |
| [`inventory`](../commands/inventory.md) | 15 | Chaque photo et vidéo dans un classeur Excel. |
| [`status`](../commands/status.md) | Plus tard | Dit où vous en êtes et la prochaine étape. |

Les autres commandes trouvent et nettoient les doublons (`audit`, `clean`, `review`, `purge`,
`history`, `crosscheck`, `reports`, `config`, `launcher`) : **[nettoyer en
bref](../clean/quick-guide.md)**. Un mot vous échappe ? [Les mots de ce
guide](../reference-glossary.md). Un message d'erreur ? [Dépannage](../reference-troubleshooting.md).

<details>
<summary>Sans <code>mh</code> : les commandes complètes</summary>

Pour celles qui ne modifient rien (`classify`, `tags`, `inventory`, et `xmp` sans `--apply`), en
lecture seule ; ajoutez `-p 127.0.0.1:8088:8088` après `-it` pour celles qui ouvrent une page
(`review-sort`, `places`, `people`, `search`) :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr classify
```

Pour `sort`, `undo`, `album --apply` et `xmp --apply` : `:ro` est retiré, `/journal` et
`/quarantine` sont ajoutés ; remplacez `sort` par la commande de l'étape :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr sort
```

</details>

---

[Documentation](../README.md) · Pas à pas : **[4. Proposer une arborescence](04-classify.md)** →
