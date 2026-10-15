# Retrouver en bref : le parcours complet

[Documentation](../README.md) › Retrouver en bref · 🇬🇧 [English](../../en/find/quick-guide.md)

Retrouvez une photo par ce dont vous vous souvenez : une personne, un lieu, une année, un mot
(« Chloé à la montagne »), dans votre navigateur. Une commande par étape, à coller dans
**PowerShell**. **Rien ne bouge** : vos photos restent où elles sont, triées ou non.

<div class="mh-path" markdown>

**Le strict minimum** : trois étapes. Les autres sont facultatives.

- [0 · Avant de commencer](#0-avant-de-commencer)
- [3 · Donner des mots](#3-donner-des-mots-à-vos-photos)
- [4 · Retrouver une photo](#4-retrouver-une-photo--search)

</div>

Chaque étape dit ce qu'elle risque : <span class="mh-badge mh-safe">🔒 Photos intactes</span>
<span class="mh-badge mh-undo">↩️ Annulable</span>. <span class="mh-badge mh-ai">🤖 IA
locale</span> marque la seule partie qui demande un modèle de vision sur votre ordinateur : sans
lui, tout le reste fonctionne.

## 0. Avant de commencer

<span class="mh-badge mh-once">⏱ Une fois</span>

`search` retrouve ce que l'audit a lu. Écrivez `mh` une fois ([nettoyer en bref, étape
0](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh)), puis auditez vos dossiers :

```powershell
mh audit
```

Dans un nouveau terminal, rechargez `mh` : `. "$HOME\media-hygiene\mh.ps1"`. Mieux encore,
nettoyez d'abord les doublons ([nettoyer en bref](../clean/quick-guide.md)) : sinon chaque photo
est trouvée deux fois.

**Perdu ?** Tapez `mh` seul : chaque étape des guides avec sa commande, la prochaine proposée ;
Entrée la lance. Plus : [`menu`](../commands/menu.md).

## 1. Nommer les personnes (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Pour retrouver les photos de quelqu'un par son nom, nommez une fois les visages. Aucune IA à
installer. Trouver les visages prend du temps la première fois : mesurez d'abord, puis lancez la
page.

```powershell
mh people --sample 200
mh people
```

Ouvrez `http://127.0.0.1:8088/` : les visages qui se ressemblent sont regroupés, les plus grands
groupes d'abord. **Tapez un nom** sur un groupe, Entrée : il est écrit dans `config.toml`. Nommer
les dix plus grands groupes suffit souvent.

![La page des personnes : le plus grand groupe nommé Chloé, le nom relu dans config.toml en haut de la page, ses sept visages en dessous ; puis le groupe 2 et le groupe 3, pas encore nommés, chacun avec son champ pour taper un nom et ses boutons pour nommer, nommer avec d'autres ou ignorer le groupe](../images/people.webp)

??? info "Détails"

    L'outil apporte ses propres modèles de visages (39 Mo, téléchargés une fois). Les visages
    restent dans le cache, jamais envoyés ; `mh people --forget` les supprime tous. Plus : [les
    personnes](../reference-people.md).

## 2. Nommer vos lieux (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Les téléphones récents écrivent où chaque photo a été prise. Sans rien faire, les photos
reçoivent déjà le nom de la ville la plus proche et de son pays. Pour les retrouver par **vos**
noms (« Maison », « Chez papy »), nommez vos lieux sur une carte :

```powershell
mh places
```

Ouvrez `http://127.0.0.1:8088/`, cliquez sur un cercle, nommez-le, **Enregistrer**.

![La carte des lieux : les tuiles OpenStreetMap du parc du Cinquantenaire à Bruxelles, le cercle des photos prises là, le cercle vert du lieu Parc du Cinquantenaire qui vient d'être enregistré, et à gauche la liste des lieux et des plus grands groupes sans nom](../images/places.webp)

??? info "Détails"

    Les villes sont nommées hors ligne : aucune position ne quitte votre ordinateur. Un village
    ou un parc entier ? **Chercher sur OpenStreetMap** prend son contour. Plus : [lieux et
    voyages grâce au GPS](../sort/09-places-from-gps.md).

## 3. Donner des mots à vos photos

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

```powershell
mh tags
```

En quelques secondes, chaque photo et vidéo reçoit les mots de ses dossiers et de son nom
(`2022/Durbuy - ours` donne `Durbuy`, `ours`), de sa date (année, mois, saison, Noël) et de son
lieu (votre lieu, la ville et le pays les plus proches). Ils restent dans le cache, jamais dans
vos photos.

??? tip "🤖 Avec une IA locale : ce que montre chaque photo"

    Avec [Ollama](https://ollama.com) et un modèle de vision indiqué dans `[classify.ai]` de
    `config.toml` ([comment](../sort/08-subjects-from-a-local-model.md)), la même commande ajoute
    aussi ce que **montre** chaque photo (« montagne », « neige », « gâteau »). Environ
    2 secondes par photo, donc souvent une nuit ou plus : mesurez d'abord.

    ```powershell
    mh tags --sample 20
    mh tags
    ```

    Ctrl+C arrête, le suivant reprend, les plus récentes d'abord. Sans modèle, `tags` le dit en
    une ligne et s'en tient aux dossiers, noms, dates et lieux. Plus : [les
    tags](../reference-tags.md).

## 4. Retrouver une photo : `search`

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

```powershell
mh search
```

Ouvrez `http://127.0.0.1:8088/` : tapez ce dont vous vous souvenez, la grille montre les photos,
les meilleures d'abord ; Entrée en agrandit une.

![La page de recherche : anniversaire tapé dans le champ Mots, à côté les filtres d'année, de chemin et de source, 8 fichiers trouvés ; une grille de photos d'anniversaire, chacune avec son nom, son dossier, sa date et ses mots Anniversaire, 2022, mai, printemps](../images/search.webp)

| Vous tapez | Elle trouve |
|---|---|
| `Chloé montagne` | Chloé (étape 1) sur une photo où « montagne » vient d'un dossier ou d'un nom (`Vacances montagne`), ou, 🤖 avec une IA locale, de ce que montre la photo. |
| `person:"Mamie Jeanne"` | Le nom parmi les personnes seulement. |
| `neige 2008` | La neige de 2008 : l'année est un mot de la date. |
| `place:durbuy` | Le mot parmi les lieux seulement. |
| `anniv*`, `"bord de mer"` | Un début de mot, une expression. |

??? info "Détails"

    Filtres à côté du champ : années, une partie du chemin, une source de mots. Sans navigateur,
    `mh search Chloé montagne` affiche les premiers résultats en tableau. Plus :
    [`search`](../commands/search.md).

## 5. Emporter les mots dans un autre logiciel photo (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-undo">↩️ Annulable</span>

Vous voulez les mêmes mots dans digiKam, darktable, Lightroom ou Immich ? La première ligne
montre ce qu'il écrirait, la seconde écrit un fichier compagnon `.xmp` à côté de chaque photo
(`IMG_1.jpg.xmp`) :

```powershell
mh xmp
mh xmp --apply
```

??? info "Détails"

    La photo elle-même n'est jamais modifiée ; un `.xmp` déjà là est complété, jamais remplacé.
    Les noms des personnes n'y vont que si vous ajoutez `person` à `[tags] xmp_sources`.
    `mh undo` retire ce qu'il a écrit. Plus : [emporter les mots avec les
    photos](../reference-tags.md#emporter-les-mots-avec-les-photos--xmp).

## 6. Répondre à vos propres questions dans Excel (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

```powershell
mh inventory
```

Un classeur `inventory.xlsx`, dans vos rapports : chaque photo et vidéo avec sa date, son
appareil, sa position, sa taille, des mots de qualité (*flou*, *petit*), d'exposition (*sombre*,
*clair*) et ses mots de `tags`. Filtrez, triez, comptez.

??? info "Détails"

    Lu depuis le cache seul, en secondes. `--format csv` pour un fichier CSV. Plus : [le classeur
    d'inventaire](../reference-inventory.md).

## Plus tard : de nouvelles photos

`mh audit` (avec `--people` pour chercher en même temps les visages des nouvelles photos), puis
`mh tags` : grâce au cache, seules les nouvelles photos sont lues. Perdu ? `mh status` dit où vous
en êtes.

## Vous avez fait le tour

Chaque commande de la recherche, et l'étape de cette page qui la montre :

| Commande | Étape | Ce qu'elle fait |
|---|---|---|
| [`audit`](../commands/audit.md) | 0, Plus tard | Lit vos dossiers dans le cache, sans rien modifier. |
| [`people`](../commands/people.md) | 1 | Trouve et nomme les visages ; `--forget` les supprime. |
| [`places`](../commands/places.md) | 2 | Nomme vos lieux sur une carte. |
| [`tags`](../commands/tags.md) | 3 | Donne des mots à chaque photo et vidéo ; 🤖 ce qu'elles montrent, avec une IA locale seulement. |
| [`search`](../commands/search.md) | 4 | Retrouve une photo par un mot, un lieu, une année, une personne. |
| [`xmp`](../commands/xmp.md) | 5 | Écrit les mots dans des fichiers compagnons `.xmp`. |
| [`undo`](../commands/undo.md) | 5 | Retire les fichiers `.xmp` écrits. |
| [`inventory`](../commands/inventory.md) | 6 | Chaque photo et vidéo dans un classeur Excel. |
| [`status`](../commands/status.md) | Plus tard | Dit où vous en êtes et la prochaine étape. |
| [`menu`](../commands/menu.md) | Plus tard | Liste chaque étape avec sa commande ; Entrée lance la prochaine. |

Pour donner à vos photos une arborescence bien rangée (`classify`, `sort`, `album`) : **[trier en
bref](../sort/quick-guide.md)**. Pour nettoyer les doublons : **[nettoyer en
bref](../clean/quick-guide.md)**. Un mot vous échappe ? [Les mots de ce
guide](../reference-glossary.md). Un message d'erreur ? [Dépannage](../reference-troubleshooting.md).

??? note "Sans `mh` : les commandes complètes"

    Pour celles qui ne modifient rien (`audit`, `tags`, `inventory`, et `xmp` sans `--apply`), en
    lecture seule ; ajoutez `-p 127.0.0.1:8088:8088` après `-it` pour celles qui ouvrent une page
    (`people`, `places`, `search`) :

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      cavo789/media-hygiene --locale fr tags
    ```

    Pour `xmp --apply` et `undo` : `:ro` est retiré, `/journal` et `/quarantine` sont ajoutés :

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      -v "$HOME\media-hygiene\journal:/journal" `
      -v "$HOME\media-hygiene\quarantine:/quarantine" `
      cavo789/media-hygiene --locale fr xmp --apply
    ```

---

[Documentation](../README.md) · En détail : **[Les tags](../reference-tags.md)**, **[Les personnes](../reference-people.md)** →
