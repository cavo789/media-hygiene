# `shrink` : alléger les vidéos lourdes

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `shrink` · 🇬🇧 [English](../../en/commands/shrink.md)

## En bref

**Récupérer la place des clips des anciens appareils : environ quatre fois plus légers, l'image
gardée.**

Les anciens appareils enregistraient chaque image d'une vidéo comme un JPEG à part (MJPEG) : une
minute prend une centaine de mégaoctets. `shrink` liste ces vidéos, d'après ce que le dernier
[`audit`](audit.md) a appris, avec la place que chacune libérerait. Avec `--apply`, il les
réencode en H.264, le format que lisent tous les ordinateurs, téléphones et télévisions, vérifie
chaque résultat, et déplace l'original en [quarantaine](../reference-glossary.md#quarantaine).

**Plus léger, même qualité visible, jamais « sans perte »** : un réencodage laisse toujours
tomber des détails que l'œil ne voit pas. C'est pourquoi l'original part en quarantaine, pas à
la corbeille : regardez-en quelques-unes, puis [`purge`](purge.md) libère la place, ou
[`undo`](undo.md) ramène tout.

**Quand** : après un [`clean`](clean.md), quand le disque est encore plein. **⚖ Fichiers les
plus lourds** dans [`browse`](browse.md) montre où va la place.

**Essayer** (liste seulement, ne change rien) :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr shrink
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit avec `--apply` seulement : chaque vidéo choisie est remplacée par un `.mp4` plus léger, son original déplacé en quarantaine. |
| Il faut | `/cache` (ce que l'audit a appris) ; avec `--apply`, vos dossiers **sans** `:ro`, `/journal` et `/quarantine`. |
| Écrit | Les vidéos allégées, le journal ; les originaux en quarantaine. |
| Annuler | [`undo <exécution>`](undo.md) retire chaque vidéo allégée (tant qu'elle n'a pas changé) et ramène son original. |
| Avec `mh` | `mh shrink`, puis `mh shrink --try` (l'action de la page d'accueil) ou `mh shrink --apply`. |

## Le lancer

D'abord la liste (les dossiers peuvent rester en `:ro`), puis ajoutez `--apply` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr shrink --apply
```

La liste dit ce qu'est chaque vidéo et ce qu'elle pèserait après, une **estimation** : seul
l'encodage le dira.

```text
3 vidéos à alléger : 1,9 Go aujourd'hui, environ 240 Mo après (estimé : seul l'encodage le dira).
   C:\Photos\2009\Zoo\MVI_0042.AVI — mjpeg, 640×480, 4 min : 812 Mo → ~95 Mo
```

## Essayer d'abord : avant et après dans le navigateur

`--try` encode les `try_count` premières vidéos de la liste (10 par défaut, les plus gros gains
d'abord ; ou celles sous `--folder`) en **brouillons**, une à la fois en arrière-plan, avec les
mêmes réglages que `--apply`, et ouvre une page qui montre chacune dès qu'elle est prête :

- **B, le brouillon**, se lit dans la page, avec sa taille, son gain en % et son temps
  d'encodage ;
- **A, l'original** : le MJPEG et le PCM des anciens appareils ne se lisent dans aucun
  navigateur, la page montre donc des images de l'original et du brouillon prises aux mêmes
  instants (10, 50 et 90 % du film), à 100 % ; la touche `B` inverse A et B. `←` / `→` passent
  d'une vidéo à l'autre.
- **Alléger celle-ci** (`L`) ou **Choisir tous les brouillons affichés** (`A`) : chaque choix
  est enregistré dans `shrink-decisions.json` et montré tel que relu sur le disque. **Alléger
  maintenant celles choisies** (`Entrée`) passe la main au terminal, qui pose la question
  habituelle, puis les allège comme `--apply` (originaux en quarantaine, journalisé,
  annulable), **en réutilisant chaque brouillon** : rien n'est encodé deux fois. Une vidéo
  déplacée, renommée ou modifiée depuis la page est sautée, avec une ligne.

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene shrink --try
```

**Les brouillons sont toujours supprimés** : ils ne sont écrits que dans `/cache/shrink-try/`
(le volume du cache, jamais à côté de vos photos), et supprimés quand la page se ferme, sur
Ctrl+C ou quand le conteneur est arrêté. Si l'ordinateur a été éteint en cours de route, le
`shrink` suivant les supprime et le dit en une ligne. Sans montage de `/cache`, `--try` refuse
(avec la ligne à ajouter) ; un seul `--try` à la fois. Avant chaque brouillon, `/cache` doit
avoir deux fois sa taille estimée de libre, sinon les brouillons s'arrêtent là : un brouillon
pèse environ 29 % de son original (mesuré sur un clip Panasonic), les 10 clips les plus lourds
d'une grande collection peuvent donc prendre 1 à 2 Go un moment.

Temps estimé : environ 8 s d'encodage par minute de film sur un PC à 32 processeurs, donc
environ 30 s pour un clip de 3 minutes, et 5 minutes pour 10 d'entre eux : le premier brouillon
s'affiche bien avant le dernier.

## Quelles vidéos

- **Les codecs des anciens appareils et des années 2000** : MJPEG, DV, MPEG-4 partie 2 (DivX,
  Xvid), Windows Media, MPEG-1 et 2 (`codecs` dans la section `[shrink]` de `config.toml`).
- **Toute vidéo qui dépense bien trop de bits pour son image** : plus de `bits_per_pixel` (0,5)
  bits par pixel et par image. Le H.264 d'un téléphone en dépense environ 0,1 à 0,3 : il est
  **laissé tel quel**, car une seconde génération avec perte se voit et gagne peu.
- Jamais une vidéo d'un dossier protégé, exclu ou de sauvegarde, ni une de moins d'une seconde.
- **Jamais une vidéo qu'il a déjà allégée** : chaque vidéo allégée porte une marque dans le
  fichier (l'étiquette `media_hygiene`, `media-hygiene shrink crf=23` ; le commentaire de
  l'appareil reste). Renommée, déplacée par `sort` ou dans l'Explorateur, copiée ailleurs, même
  sans les journaux : elle n'est plus jamais proposée.
- **Pas rentable** : un résultat qui n'est pas au moins `min_gain_percent` (30) % plus léger est
  jeté, l'original reste, et la vidéo n'est plus essayée tant qu'elle ne change pas.

## Deux niveaux

| | Ce qu'il fait | Pour |
|---|---|---|
| *(par défaut)* | Même taille et même cadence, x264 en CRF 23 : visuellement identique. | Tout ce qui mérite d'être gardé tel quel. |
| `--lighter` | 720 lignes au plus sur le petit côté : plus léger encore pour une image plus grande (un clip de 720 lignes reste comme par défaut). | Les clips dont la qualité compte moins (les premières vidéos des enfants). Choisissez-les avec `--folder`. |

Mesuré sur deux clips MJPEG d'un appareil Panasonic (1280×720, 43 s et 3 min 35 s) : le CRF 23 a
gardé 26 et 29 % de leur taille, le CRF 18 66 et 69 %, sans différence visible entre eux ni avec
l'original ; les deux lus dans Windows et sur un téléphone, avec leur date. D'où le CRF 23 par
défaut (`same_crf` dans `config.toml` : 18 pour l'image la plus fine).
L'encodage a pris 8 à 11 secondes par minute de film sur un PC à 32 processeurs (16 utilisés).
Autre appareil, autre sujet : autres chiffres ; la liste donne son estimation, et le gain réel
est dit après chaque vidéo.

## Ce qui est gardé, et vérifié

- **Gardé** : la date de prise de vue (`creation_time`, et la date locale d'un iPhone), le lieu,
  chaque piste son (en AAC), l'image remise droite, la date du fichier (sa date de
  modification) : `classify` et `sort` trouvent la même date.
- **Vérifié avant que l'original parte** : la vidéo allégée dure autant (à une demi-seconde
  près), a autant de pistes son, dit la même date et le même lieu, et ses images se décodent.
  Sinon elle est jetée et l'original n'est pas touché.
- **Le nom** : `clip.avi` devient `clip.mp4` ; un fichier compagnon `clip.avi.xmp` suit en
  `clip.mp4.xmp`. Un fichier déjà nommé `clip.mp4` à côté n'est jamais remplacé : cette vidéo
  est sautée.
- **Jamais réimporté** : l'original est retenu comme tout fichier que vous avez mis de côté. Si un
  téléphone ou une sauvegarde le garde encore, `mh import --phone` ne l'importe pas à nouveau, et le
  `clean` suivant remet de côté une copie revenue.

## Options

| Option | Ce qu'elle fait |
|---|---|
| `--folder CHEMIN` | Seulement les vidéos sous ce dossier (chemin de l'hôte) ; répétez-la pour plusieurs. |
| `--lighter` | 720 lignes au plus, une compression plus forte. |
| `--try` | Des brouillons des `try_count` premières, comparés dans le navigateur ; alléger depuis la page. |
| `--apply` | Les alléger ; sans elle, seulement les lister. |
| `--yes`, `-y` | Ne pas demander d'abord. |

## Bon à savoir

- **Lent** : un réencodage prend à peu près la durée du film, ou plus sur un petit ordinateur ;
  une vidéo à la fois, sur la moitié des processeurs (`threads`), pour que l'ordinateur reste
  utilisable. Ctrl+C arrête après la vidéo en cours ; retapez la commande pour le reste.
- **Lancé depuis la page d'accueil** : le réencodage tourne dans la fenêtre de `mh` (le serveur
  de la page n'écrit jamais vos photos) ; la page reste ouverte et montre où il en est (vidéos
  faites, celle en cours), puis son nouvel état.
- **La place revient avec `purge`** : d'ici là, les originaux sont en quarantaine.
- **Une vidéo renommée (`.avi` → `.mp4`) garde ses liens** : `albums.json`, `decisions.json` et
  les vidéos choisies avec `--try` nomment le nouveau `.mp4`, relu sur le disque ; `undo` leur
  rend le nom de l'original.
- **Réglages** : la section `[shrink]` de `config.toml` (`codecs`, `bits_per_pixel`,
  `min_gain_percent`, `same_crf`, `lighter_crf`, `lighter_lines`, `preset`, `threads`,
  `try_count` : les brouillons de `--try`, 10 par défaut).
- **Changer seulement le conteneur (`.mov` → `.mp4` sans réencoder) ne libère rien** : ce n'est
  pas proposé.

## Pour aller plus loin

- [Nettoyer en bref](../clean/quick-guide.md)
- [Annuler, historique et purge](../clean/09-undo-history-purge.md)

## L'aide intégrée

<details>
<summary><code>shrink --help</code></summary>

<!-- capture: help-shrink.txt -->
```text
 Utilisation : media-hygiene shrink [OPTIONS]

 Lister les vidéos lourdes qui gagnent à être allégées (anciens appareils,
 MJPEG) ; avec --apply, les réencoder en H.264, chacune vérifiée, l'original en
 quarantaine (journalisé, annulable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --folder           <str>  Seulement les vidéos sous ce dossier (chemin de    │
│                           l'hôte, tel que vous l'avez monté) ; répétez-la    │
│                           pour plusieurs. Par défaut : tous les dossiers     │
│                           montés.                                            │
│ --lighter                 Plus léger encore pour une grande image : 720      │
│                           lignes au plus (lighter_lines dans config.toml).   │
│                           Pour les clips dont la qualité compte moins.       │
│ --apply                   Les alléger ; sans cette option, seulement les     │
│                           lister avec le gain attendu.                       │
│ --try                     Encoder les premières (try_count dans config.toml) │
│                           en brouillons, dans /cache seulement, et comparer  │
│                           avant et après dans le navigateur ; alléger depuis │
│                           la page. Les brouillons sont supprimés quand la    │
│                           page se ferme.                                     │
│ --yes      -y             Alléger sans demander d'abord.                     │
│ --help     -h             Affiche ce message et quitte.                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
