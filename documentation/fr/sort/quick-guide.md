# Trier en bref : le parcours complet

[Documentation](../README.md) › Trier en bref · 🇬🇧 [English](../../en/sort/quick-guide.md)

Donnez à vos photos et vidéos une arborescence bien rangée, `année/catégorie` ou celle que vous
choisissez : une commande par étape, à coller dans **PowerShell**. `classify` **propose** une
place pour chaque fichier, vous corrigez la proposition, et seul `sort` déplace les fichiers. Rien
ne bouge avant, et `sort` peut être annulé.

<div class="mh-path" markdown>

**Le strict minimum**, pour un premier tri : quatre étapes. Les autres sont facultatives.

- [0 · Avant de commencer](#0-avant-de-commencer)
- [1 · Demander une proposition](#1-demander-une-proposition)
- [2 · La corriger](#2-corriger-la-proposition-dans-le-classeur)
- [9 · Trier](#9-trier)

</div>

Chaque étape dit ce qu'elle risque : <span class="mh-badge mh-safe">🔒 Photos intactes</span>
<span class="mh-badge mh-undo">↩️ Annulable</span>. <span class="mh-badge mh-ai">🤖 IA
locale</span> marque les seules commandes qui demandent un modèle de vision sur votre ordinateur :
sans lui, sautez-les. Vous voulez seulement **retrouver** une photo, sans rien déplacer ?
**[Retrouver en bref](../find/quick-guide.md)**.

## 0. Avant de commencer

<span class="mh-badge mh-once">⏱ Une fois</span>

**Nettoyez d'abord les doublons** ([nettoyer en bref](../clean/quick-guide.md)) : sinon les deux
copies d'une photo sont triées. La commande `mh` écrite pour le nettoyage sert aussi ici ; sinon,
écrivez-la une fois : [nettoyer en bref, étape 0](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh).
L'étape 0 l'a écrite dans votre profil PowerShell : chaque nouveau terminal la connaît.

**Perdu ?** Tapez `mh` seul : la [page d'accueil](../commands/home.md) s'ouvre dans votre
navigateur, chaque étape des guides un bouton, la prochaine proposée. Dans le terminal seulement :
[`mh menu`](../commands/menu.md).

## 1. Demander une proposition

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

`classify` date chaque fichier, regroupe les photos prises à peu d'intervalle en **événements**,
et propose un dossier pour chacun :

```powershell
mh classify
```

À la fin, un nouveau dossier `<date>-classify` de vos rapports contient deux fichiers :

- `classify.xlsx`, le classeur, à ouvrir dans Excel ou LibreOffice : c'est là que vous
  **modifiez** ;
- `report.html`, le rapport, à ouvrir dans votre navigateur : c'est là que vous **regardez** les
  photos.

![La première page du rapport de classify : quatre compteurs (fichiers, déjà à leur place, à vérifier ou à trier, événements), un tableau des années avec des liens vers leurs pages, les événements par où commencer avec leur part du travail, puis l'arborescence proposée avec le nombre de fichiers de chaque dossier](../images/classify-report.webp)

??? info "Détails"

    Rien n'est modifié : `mh` monte vos dossiers en lecture seule (`:ro`). La date d'un
    événement vient de l'EXIF, du nom ou du dossier de ses fichiers. Une grande collection ?
    `mh classify --year 2016` propose une année à la fois. Plus : [proposer une
    arborescence](04-classify.md).

## 2. Corriger la proposition dans le classeur

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

Ouvrez les deux côte à côte. Seules les cellules **jaunes** du classeur se modifient.

1. **Commencez par la feuille Événements** : les plus grands d'abord. Tapez un **Nom**
   (`Italie 2023`) : il devient le dossier de l'événement. Nommer les dix premières lignes règle
   souvent l'essentiel de la collection.
2. Pour comprendre un événement, copiez son **Identifiant** (la première colonne, 12
   caractères), ouvrez la page de son année dans le rapport et cherchez-le (Ctrl+F) : ses dates,
   ses aperçus, les dossiers d'où viennent ses photos.
3. Un fichier mal placé ? Feuille Fichiers, colonne **Dossier final** (`2016/Kermesse`).
4. **Enregistrez et fermez** le classeur.

![Une page d'année du rapport de classify : un événement de vacances avec son identifiant, son nombre de fichiers dont quelques-uns à vérifier ou à trier, la part cumulée du travail, le dossier proposé marqué Sûr, les dossiers d'où viennent ses photos, puis huit aperçus répartis sur ses jours avec leurs noms et leurs heures, et un lien vers tous les fichiers](../images/classify-year.webp)

Plus : [revoir la proposition](05-review-the-proposal.md).

## 3. … ou dans le navigateur (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Plutôt une photo à l'écran qu'un tableur ? Les mêmes événements, un à la fois, avec leurs photos :

```powershell
mh review-sort
```

Votre navigateur s'ouvre sur la page (sinon : `http://127.0.0.1:8088/`). <kbd>Entrée</kbd> accepte le nom et la catégorie
et passe au suivant, <kbd>E</kbd> tape un nom, <kbd>O</kbd> envoie les photos choisies ailleurs,
<kbd>V</kbd> accepte d'un coup toutes les propositions sûres.

??? info "Détails"

    Vos choix vont dans `sort-decisions.json`, à côté du classeur, jamais dedans : `sort` lit les
    deux, et une même ligne modifiée des deux côtés lui est signalée, jamais tranchée en silence.
    Plus : [nommer les événements dans le navigateur](11-name-events-in-the-browser.md).

## 4. Écrire ce que vous savez (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Vos voyages, vos fêtes, vos dossiers existants : écrits une fois comme règles dans `config.toml`,
ils servent à chaque `classify`. La première fois, `mh config` crée ce fichier, chaque réglage
expliqué ; ouvrez-le ensuite :

```powershell
mh config
notepad "$HOME\media-hygiene\config\config.toml"
```

Ajoutez vos règles à la fin du fichier, par exemple :

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

Les règles sont lues dans l'ordre : la première sûre décide.

??? info "Toutes les sortes de règles, et votre propre arborescence"

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

    Votre propre arborescence se règle dans `[classify]` : `layout = "{year}/{month}"` (par
    mois), `target` (construire ailleurs), `leave` (un dossier jamais trié). Plus : [écrire ce que
    vous savez](06-write-down-what-you-know.md), [votre propre
    structure](04-classify.md#votre-propre-structure).

## 5. Les lieux et les voyages, grâce au GPS (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Les téléphones récents écrivent où chaque photo a été prise. Nommez vos lieux sur une carte :

```powershell
mh places
```

Votre navigateur s'ouvre sur la page (sinon : `http://127.0.0.1:8088/`) : les cercles sont vos photos, les plus grands groupes sans nom
d'abord. Cliquez, nommez (« Maison », « Chez papy »), réglez le rayon, cochez **Maison** pour la
vôtre, **Enregistrer** : le lieu est écrit dans `config.toml`.

![La carte des lieux : les tuiles OpenStreetMap du parc du Cinquantenaire à Bruxelles, le cercle des photos prises là, le cercle vert du lieu Parc du Cinquantenaire qui vient d'être enregistré, et à gauche la liste des lieux et des plus grands groupes sans nom](../images/places.webp)

Ajoutez ensuite trois règles à `config.toml` :

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

??? info "Détails"

    L'audit dit combien de vos photos ont une position. Un village ou un parc entier ?
    **Chercher sur OpenStreetMap** prend son contour. `place` range dans le nom du lieu
    (`2023/Maison`), `trip` nomme chaque voyage à plus de 100 km de la maison d'après son pays et
    sa ville (`2023/Italie/Turin`), `folder_town` lit les dossiers nommés comme une ville
    (`2017\Durbuy`). Les villes sont nommées hors ligne : aucune position ne quitte votre
    ordinateur. Plus : [lieux et voyages grâce au GPS](09-places-from-gps.md).

## 6. Les personnes (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Nommez une fois les visages de vos photos : ils servent à ranger (ici) et à retrouver
([retrouver en bref](../find/quick-guide.md)). Aucune IA à installer. Trouver les visages prend
du temps la première fois : mesurez d'abord, puis lancez la page.

```powershell
mh people --sample 200
mh people
```

Votre navigateur s'ouvre sur la page (sinon : `http://127.0.0.1:8088/`) : les visages qui se ressemblent sont regroupés, les plus grands
groupes d'abord. **Tapez un nom** sur un groupe, Entrée : il est écrit dans `config.toml`. Nommer
les dix plus grands groupes suffit souvent.

![La page des personnes : le plus grand groupe nommé Chloé, le nom relu dans config.toml en haut de la page, ses sept visages en dessous ; puis le groupe 2 et le groupe 3, pas encore nommés, chacun avec son champ pour taper un nom et ses boutons pour nommer, nommer avec d'autres ou ignorer le groupe](../images/people.webp)

Pour ranger les événements où quelqu'un figure, ajoutez une règle **sous** vos règles de dates
et de lieux (sinon elle prend tout événement où Chloé figure) :

```toml
[[classify.rules]]
name = "Avec Chloé"
match = "person"
names = ["Chloé"]
category = "Personnes/Chloé"
```

??? info "Détails"

    L'outil apporte ses propres modèles de visages (39 Mo, téléchargés une fois). Sur la page,
    `x` choisit plusieurs groupes de la même personne, × retire un visage, `i` ignore des
    inconnus, `y` confirme une suggestion « Chloé ? ». Les visages restent dans le cache, jamais
    envoyés ; `mh people --forget` les supprime tous. Plus tard, `mh audit --people` cherche les
    visages des nouvelles photos avec l'audit. Plus : [trier par personne](10-sort-by-person.md),
    [les personnes](../reference-people.md).

## 7. Les sujets, avec une IA locale (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-ai">🤖 IA locale</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Les photos dans des dossiers qui ne portent qu'une date (`DCIM`, `Juillet 2016`) n'ont pas de
sujet. Un modèle de vision **sur votre ordinateur** peut dire ce qu'elles montrent. Sans lui,
sautez cette étape : les dates, les lieux et les personnes rangent déjà l'essentiel.

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

3. Mesurez le coût sur quelques photos : `mh classify --sample 50`.

??? info "Détails"

    Seules les photos qu'aucune autre règle n'a rangées sont envoyées, quelques-unes par
    événement, au seul `url` que vous indiquez. Avec WSL ou Linux sans Docker Desktop, voyez la
    page détaillée. Plus : [nommer les sujets avec un modèle
    local](08-subjects-from-a-local-model.md).

## 8. Relancer la proposition

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

Après vos règles, vos lieux, vos personnes, relancez l'étape 1 :

```powershell
mh classify
```

Les modifications déjà faites dans l'ancien classeur et dans `review-sort` sont reprises.
Corrigez encore (étapes 2 et 3), autant de fois qu'il le faut : rien ne bouge avant `sort`.

??? info "Détails"

    Le tableau *Pourquoi* compte les fichiers que chaque règle a décidés ; une règle listée sous
    *Règles qui n'ont rien décidé* est placée trop bas, ou ne reconnaît rien.

## 9. Trier

<span class="mh-badge mh-undo">↩️ Annulable</span>

Déplacez les fichiers comme le dit le classeur :

```powershell
mh sort
```

`sort` dit combien de modifications il a lues (pas assez ? le classeur n'était pas enregistré)
et demande confirmation : répondez `o`. Il finit en prouvant que rien n'est perdu : autant de
fichiers, de la même taille, avant et après.

??? info "Détails"

    Pour `sort`, `mh` monte vos dossiers en écriture (`sort` déplace des fichiers) et ajoute le
    journal et la quarantaine. `sort` prend le classeur du dernier `classify` et le vérifie avant
    de rien déplacer. Plus : [trier](07-sort.md).

## 10. Vérifier, ou annuler

<span class="mh-badge mh-undo">↩️ undo remet en place</span>

```powershell
explorer "C:\Photos"
```

Vous changez d'avis ? `mh undo` : chaque fichier revient où il était. Un `classify` relancé après
un tri ne propose pas ailleurs ce qui est déjà rangé. Plus : [changer d'avis](07-sort.md#changer-davis).

## 11. Les albums (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-undo">↩️ Annulable</span>

Une photo de Noël qui est aussi parmi vos plus belles ? Un album la met dans un second dossier
sans la copier : un lien physique, aucune place prise. La première ligne montre ce qu'il ferait,
la seconde crée l'album dans `C:\Photos\Albums\Noël` :

```powershell
mh album "Noël" --category Noël
mh album "Noël" --category Noël --apply
```

??? info "Détails"

    Ce qu'il rassemble : `--category`, `--event`, `--rule`, ou `--rating 4` (au moins 4 étoiles
    dans Windows), ensemble si vous voulez (`--category Noël --rating 4`). `mh undo` supprime ses
    liens, jamais une photo. Plus : [albums](12-albums.md).

## Plus tard : de nouvelles photos

Le même chemin, en plus court, car le cache se souvient de tout : `mh audit` et `mh clean`
([nettoyer en bref](../clean/quick-guide.md)), `mh people` pour les nouveaux visages, puis
`mh classify`, le classeur et `mh sort`. Ce qui est déjà rangé reste à sa place. Perdu ?
`mh status` dit où vous en êtes, et si la dernière proposition a été triée.

## Vous avez fait le tour

Chaque commande du tri, et l'étape de cette page qui la montre :

| Commande | Étape | Ce qu'elle fait |
|---|---|---|
| [`classify`](../commands/classify.md) | 1, 4, 7, 8 | Propose une place pour chaque fichier, sans rien modifier ; 🤖 la règle `subject` et `--sample` demandent une IA locale. |
| [`review-sort`](../commands/review-sort.md) | 3 | Nomme les événements dans le navigateur. |
| [`places`](../commands/places.md) | 5 | Nomme vos lieux sur une carte. |
| [`people`](../commands/people.md) | 6 | Trouve et nomme les visages ; `--forget` les supprime. |
| [`sort`](../commands/sort.md) | 9 | Déplace les fichiers comme le dit le classeur. |
| [`undo`](../commands/undo.md) | 10, 11 | Annule un tri, un album. |
| [`album`](../commands/album.md) | 11 | Une photo dans plusieurs dossiers, sans copie. |
| [`status`](../commands/status.md) | Plus tard | Dit où vous en êtes et la prochaine étape. |
| [`menu`](../commands/menu.md) | Plus tard | Liste chaque étape avec sa commande ; Entrée lance la prochaine. |

Pour retrouver une photo par un mot, un lieu, une année ou une personne (`tags`, `search`, `xmp`,
`inventory`) : **[retrouver en bref](../find/quick-guide.md)**. Pour trouver et nettoyer les
doublons (`audit`, `clean`, `review`, `purge`…) : **[nettoyer en bref](../clean/quick-guide.md)**.
Un mot vous échappe ? [Les mots de ce guide](../reference-glossary.md). Un message d'erreur ?
[Dépannage](../reference-troubleshooting.md).

??? note "Sans `mh` : les commandes complètes"

    Pour celles qui ne modifient rien (`classify`), en lecture seule ; ajoutez
    `-p 127.0.0.1:8088:8088` après `-it` pour celles qui ouvrent une page (`review-sort`,
    `places`, `people`) :

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      cavo789/media-hygiene --locale fr classify
    ```

    Pour `sort`, `undo` et `album --apply` : `:ro` est retiré, `/journal` et `/quarantine` sont
    ajoutés ; remplacez `sort` par la commande de l'étape :

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

---

[Documentation](../README.md) · Pas à pas : **[4. Proposer une arborescence](04-classify.md)** →
