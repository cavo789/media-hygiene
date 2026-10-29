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
| Vos photos | 🔒 Rien ne bouge sans votre GO : *J'ai vérifié : trier ces N fichiers* déplace les fichiers d'une règle vérifiés sur la page, notés au journal ; `undo` les remet. `mh search` les monte accessibles en écriture, avec `/journal` ; montées en `:ro`, la page reste en lecture seule et le GO est refusé. |
| Il faut | `/cache` (les mots de `tags`), vos dossiers (pour montrer les photos), et `-p 127.0.0.1:8088:8088` pour la page ; `/reports` pour mettre des photos de côté. |
| Écrit | Les petits aperçus de la grille, dans le cache ; les photos mises de côté, dans `decisions.json` des rapports ; vos albums, dans `albums.json` à côté. |
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

Ouvrez <http://127.0.0.1:8088/>. La page montre le champ de recherche et ses filtres (une période, une partie du chemin, les mots
d'une seule source) dans la colonne de gauche, les touches ⌨ en dessous, une seule barre au-dessus
de la grille, puis les photos trouvées. **🔎 Mots** vient d'abord, **📁 Dossiers** ensuite : il
ouvre [vos dossiers](#parcourir-vos-dossiers). Ctrl+C, ou fermer son onglet, arrête la page.

**Chemin contient** prend une partie du chemin, sans tenir compte des majuscules. `*` remplace
n'importe quels caractères et `?` un seul : `*.mov` trouve tous les fichiers `.mov` (`.MOV`
aussi). Entre deux barres obliques, c'est une expression régulière : `/\.(mov|mp4)$/`. Tout le
reste est lu tel quel : `Vacances (2019)` ou `a+b` n'ont pas besoin d'échappement. Une expression
régulière invalide est signalée sous le champ.

- **⚖ Fichiers les plus lourds** (au-dessus des dossiers) : tous les dossiers, sans mot, les
  vidéos d'abord sauf si **Afficher** dit autre chose, les plus grosses d'abord — ou **Trier par :
  débit**, les vidéos les moins bien compressées pour leur durée (les meilleures à alléger avec
  [`shrink`](shrink.md)). La vignette d'une vidéo dit sa durée, son débit et son codec. Arrivé au
  bas de la grille, les fichiers suivants se chargent d'eux-mêmes.
- **Dans un dossier** : sous le formulaire, l'arbre de vos dossiers, comme sur la vue des dossiers
  (ouvert à la demande). Un clic limite la recherche à ce dossier et en dessous, **sans taper de
  mot** : des mots vides listent tout le dossier ; ✕ à côté de son nom recherche à nouveau dans
  tous les dossiers.

- **Chercher** : tapez les mots, puis Entrée ; les touches vont alors à la grille, `/` revient au
  champ. *Comment écrire une recherche* rappelle les expressions ("bord de mer"), les débuts de
  mots (anniv\*) et les mots d'une seule source (place:durbuy).
- **Suivre un mot** : un clic sur un mot sous une photo (*Mechelen*, *2026*, le nom d'une
  personne) le cherche comme expression dans toutes les sources, les filtres vidés : d'une photo à
  toutes les autres qui ont ce mot. Il ne choisit jamais la photo.
- **Choisir**, comme sur toute page de photos : un clic choisit un fichier ; la case ☑ (ou Ctrl+clic) en
  ajoute ou en retire un ; Maj+clic choisit tous les fichiers depuis le dernier cliqué ; un
  rectangle tracé à la souris choisit ce qu'il touche (avec Ctrl, il ajoute) ; Ctrl+A tous les
  fichiers affichés, puis **Choisir les N fichiers trouvés** dans la barre prend tous les fichiers
  que la recherche trouve, pas seulement les 240 affichés ; **🔀 Inverser la sélection** (ou I)
  choisit les autres.
- **La barre** a deux lignes qui ne bougent jamais, quoi qu'on choisisse ou trouve : en haut, où
  vous en êtes (le nombre), **📺 Sur la télé**, **Trier par** et la taille des vignettes **S**
  (les photos seules), **M**, **L** (tous les mots), gardée pour ce navigateur ; en dessous, que
  faire des fichiers choisis — grisé tant qu'aucun ne l'est : **🗑 Mettre de côté**,
  **🔀 Inverser**, l'album avec **➕** et **➖**, **📺 Partager**, **✉️ Envoyer**,
  **📂 Événement…**, puis ce qui est mis de côté et **✅ Appliquer**. Pointez un bouton pour son
  nom complet et sa touche. **✅ Appliquer** le rappelle aussi : 🔒 rien ne bouge sans votre GO ;
  chaque déplacement est journalisé, `undo` le défait. Sur une vignette, le nom, le dossier et la
  légende tiennent sur une ligne chacun (pointez-les pour le texte entier), les mots sur deux
  lignes puis *+N*.
- **⌨ Clavier** : le panneau liste les gestes principaux ; **Plus de touches** s'ouvre par-dessus
  la page (Échap le ferme), le formulaire au-dessus ne quitte donc jamais l'écran.
- **Regarder** : Entrée ou un double clic montre la photo en grand (avec un lien vers
  l'original) ; ← → (sur un téléphone, un glissement) la précédente ou la suivante, Suppr la met de côté puis montre la suivante, F
  plein écran, ? toutes les touches, Échap la ferme. **👤 Mettre une personne de côté** trouve
  toutes les photos de quelqu'un depuis celle qui est montrée
  ([`people`](people.md#depuis-nimporte-quelle-page--mettre-une-personne-de-côté)).

- **Une période** : *Du* et *Au* sont des calendriers, un jour chacun, inclus ; un seul est une
  période d'un jour. Le jour est celui de la prise de vue, tel que `classify` le date. *Du*
  choisi, *Au* prend le même jour s'il est vide ou plus tôt. À côté, le menu **📅 ▾** cherche
  **📍 Aujourd'hui**, **🗓️ Mois** (ce mois-ci), **📆 Année** (cette année) ; **✕ Effacer** vide les
  deux. **🔍 Chercher** reste en vue au bas du formulaire.
- **Trier par**, dans la barre comme sur la [vue des dossiers](#parcourir-vos-dossiers) :
  *meilleure correspondance* (par défaut ; la plus récente d'abord sans mots), *nom*, *date* (la
  plus ancienne d'abord) ou *taille* (la plus grande d'abord) ; **Afficher**, dans la colonne de
  gauche, garde **📷** les photos ou **🎬** les vidéos seulement. La recherche trie et filtre avant de montrer ses premiers fichiers :
  *Afficher : vidéos*, *Trier par : taille* donne les plus grosses vidéos trouvées. Chaque vignette
  dit sa date et sa taille.
- **🗑 mis de côté**, le quatrième choix d'**Afficher** (ou un clic sur le compteur *🗑 N mis de
  côté* de la barre) : la même grille liste seulement les fichiers mis de côté, avant que
  `clean --decisions` les envoie en quarantaine. Choisissez-en un ou plusieurs, puis *Retirer de
  la mise de côté* les remet : le fichier de décisions est relu sur le disque avant que le
  compteur change, et les vignettes restent en place. **✕** à côté de 🗑 quitte cette vue.
- **Quelle date** : `📷 2023-07-14` est le jour où la photo a été **prise**, écrit dans la photo
  elle-même (EXIF *DateTimeOriginal* ; la date d'enregistrement d'une vidéo) : c'est elle que
  *Du*, *Au* et les années trouvent. Ce n'est pas la *Date de modification* que l'Explorateur
  Windows montre par défaut : pointez la date pour voir les deux, avec l'heure de la prise.
  L'Explorateur montre la date de prise dans **Propriétés › Détails › Prise de vue** du fichier,
  ou en colonne *Prise de vue* (clic droit sur les en-têtes de colonnes). Un fichier qui ne la
  dit pas (un scan, une capture d'écran) affiche *pas de date de prise* : une recherche par date
  ne le trouve pas.
- **L'EXIF de la photo** : dans la grande vue, **I** liste ce que la photo dit d'elle-même :
  quand elle a été prise, l'appareil, l'objectif, l'exposition, sa taille en pixels et sa
  position GPS. En lecture seule : la photo n'est jamais modifiée.
- **La durée d'une vidéo** est dans le coin de son aperçu, comme sur les sites de vidéos :
  `▶ 1:45`. Sous 3 secondes, le badge est rouge : un clip si court vaut rarement d'être gardé (le
  mettre de côté reste votre choix).
- **Triées** : *Tout*, *pas encore* ou *triées* (année, puis année-mois), lu
  dans les dossiers seuls ([la convention](../sort/04-classify.md#la-convention--année-mois-événement)) :
  une photo dans `2009\2009-11\…` est triée, où que soit cette paire de dossiers et quoi qui l'y
  ait mise. *Pas encore*, puis choisir et **📂 Événement…** : la page
  devient le moyen de trier ce qui reste, dossier après dossier.

Sans navigateur (WSL, un script), donnez les mots : `search durbuy ours` affiche les 20 premiers
fichiers en tableau.

## Les événements du dernier classify

**🗂 Événements du dernier classify**, sous les dossiers de la colonne de gauche, liste les
événements du dernier plan de [`classify`](classify.md) (elle a repris `review-sort`, qui ne fait
plus que l'ouvrir) : la ligne de progression (triés, déjà en place, restants) et les passages de
`sort` de ce plan, chacun avec sa ligne d'annulation ; les trois filtres (*Seulement les
événements à décider*, *Seulement les propositions sûres*, *Seulement les événements pas encore
triés*) ; ✓ sur un événement déjà trié, ⚠ sur celui dont le classeur a changé un choix antérieur
depuis. Cliquez un événement : sa fiche s'affiche au-dessus de la liste, ses photos dans la
grille, chaque vignette disant où `sort` la mettra (*C:\Photos → 2016\2016-07\Fête*). L'adresse
`/events` (et `mh review-sort`) ouvre la page, liste ouverte.

Choisissez au clavier, comme dans l'ancienne page ; chaque choix est **enregistré aussitôt** dans
`sort-decisions.json` à côté du plan, relu sur le disque, avec ce que disait le classeur au moment
du choix (une modification ultérieure du même événement dans le classeur est un conflit, montré
en rouge, jamais tranché en silence). Le classeur lui-même n'est jamais modifié.

| Touche | Ce qu'elle fait |
|---|---|
| **F**, puis **Entrée** | taper le dossier de l'événement, l'enregistrer, puis l'événement suivant à décider |
| **E** | changer le nom de l'événement (par défaut, le dernier dossier) |
| **N** / **P**, **U** | événement suivant ou précédent, suivant à décider |
| **O** / **S** | les photos choisies : vers un autre dossier, ou laissées où elles sont |
| **Maj+S** | laisser tout l'événement où il est |
| **T** | reprendre le choix fait ici (des photos choisies, sinon de l'événement) |
| **V**, **Maj+Z** | accepter d'un coup toutes les propositions sûres, reprendre ce lot |
| **R** | *Retenir comme règle* : les jours et le dossier de l'événement écrits dans `config.toml` |
| **M** | *Trier cet événement maintenant* : où va chaque fichier, puis un seul GO ; journalisé, `undo` le remet |
| **Suppr**, **⌫** | mettre de côté les photos choisies, les en sortir (comme sur toute page de photos) |

**📌 Vos règles** liste chaque règle de `config.toml` avec les fichiers qu'elle a décidés :
retirez celles qui ne décident rien, changez une règle de nom de dossier en dates.

## Déplacer des photos vers un événement, sans règle

Pour un événement unique, une règle n'est pas nécessaire : cherchez ses jours (ou des mots),
**choisissez** les photos (comme partout : clic, Ctrl, Maj, un rectangle, Ctrl+A), puis
**📂 Événement…** dans la barre. Tapez le nom de l'événement, ou choisissez un
de vos dossiers d'événement que le champ liste (ceux déjà dans le mois où vont les photos,
les sous-dossiers écrits `France\Morzine`) ; `\` crée aussi des sous-dossiers d'un nouveau nom. La
ligne en dessous montre le dossier créé, tel que l'Explorateur le montrera, sous l'année
et le mois de la plus ancienne photo choisie (*→ C:\Photos\2009\2009-11\Anniversaire de Tom*,
[la convention](../sort/04-classify.md#la-convention--année-mois-événement)). Le nom proposé est
celui de **votre dossier qui contient le plus de photos choisies** : ses photos vont dans le
dossier du même nom sous la convention, jamais dans un second à côté.

Avant le déplacement, les photos sont listées **par dossier source**, une case chacun, avec leur
nombre. Un dossier que vous avez nommé d'après un **autre** événement (`Saint Nicolas 2009` : un
nom, une soirée) est **décoché** : ses photos restent où elles sont, sauf si vous le cochez. Un
dossier de dates, le dossier d'un membre de la famille, le `DCIM` d'un téléphone sont cochés.
**Déplacer ces N fichiers maintenant** déplace exactement ceux cochés, noté au journal, vérifié à
leur nouvelle place, dit tel que relu (*'mh undo …' les remet*). Aucune règle n'est écrite : le
prochain `classify` les trouve à leur place. Les photos ajoutées depuis le dernier `classify`
(un téléphone importé, puis audité) sont déplacées aussi : pas besoin d'un nouveau `classify`.

## Faire d'une période une règle

Une fois une période cherchée, **📌 En faire une règle** ouvre, à côté de la grille, la boîte de
*Retenir comme règle* de [`review-sort`](#les-événements-du-dernier-classify), remplie avec la période : tapez son nom
et son dossier (*Garder mes dossiers en dessous* est coché). Pendant que vous tapez, la grille montre
**les photos que la règle prendrait, chacune avec l'endroit où elle irait**
(*→ 2017\Fêtes\Mariages\Mariage d'Hervé et Magda*), calculé par le moteur de `classify` avec vos
règles et celle tapée (rien n'est écrit, rien ne bouge) ; puis les photos de ces jours qu'elle
laisse à une autre règle (une capture d'écran, une photo d'un autre événement), grisées, et dites
en mots au-dessus de la grille (*30 photos de ces jours restent avec la règle 'Anniversaire de Tom
2009'*). En les voyant, corrigez les jours (seulement le 5 août) ou le dossier, puis
**Enregistrer la règle** : elle est écrite dans `config.toml`, au-dessus de *Dossiers existants*,
relue sur le disque et affichée. Le prochain `classify` l'applique.

**Mettre à jour une règle…**, dans la même boîte, liste les règles de dates de `config.toml`, la
plus récente d'abord : en choisir une remplit la boîte, et l'enregistrer la remplace sur place (sa
place dans la liste, qui décide, est gardée). Échap ou *Annuler* ferme la boîte et remontre la
recherche.

Un fichier que la recherche ne connaît pas encore (aucun mot : lancez une fois
`mh tags --no-describe`) manque à la grille.

**Les trier maintenant, petit à petit.** Une fois vérifiées, **J'ai vérifié : trier ces N
fichiers** déplace exactement les photos que la règle prend, chacune vers le dossier affiché.
Pour en laisser de côté, choisissez-les et appuyez sur **Laisser les fichiers choisis où ils
sont** (grisées, barrées). Quand les photos viennent de plusieurs dossiers, elles sont listées par
dossier source, une case chacun, un dossier que vous avez nommé d'après un autre événement
décoché. **Dès qu'une photo est laissée de côté, *Enregistrer la règle* est désactivé** : une
sélection avec des exceptions est un déplacement, pas une règle (enregistrée, la règle les
reprendrait à chaque `classify`) ; la boîte dit combien ont été laissées. La page demande une fois (le nombre, les dossiers, la ligne
d'annulation), puis les écrit comme vos choix du dernier passage de `classify`
(`sort-decisions.json`) et lance `sort` limité à ces fichiers : noté au journal, vérifié à leur
nouvelle place, dit tel que relu sur le disque (*14 déplacés, 14 vérifiés à leur nouvelle place
(passage …) : 'mh undo …' les remet*) ; les vignettes montrent ensuite leur nouvelle place. Une
photo que le dernier `classify` ne connaît pas (ajoutée depuis) est laissée en place et comptée :
relancez `classify`. Rien ne bouge sans ce GO.

*Ces dossiers sont montés en lecture seule* : votre `mh` a été écrit avant que les pages puissent
trier (il les monte en `:ro`). Tapez une fois `mh update` : il réécrit `mh`, depuis votre image,
avec les mêmes dossiers.

## Parcourir vos dossiers

**📁 Dossiers**, en haut de la colonne de gauche, ouvre la page sur vos dossiers, comme dans
l'Explorateur (l'ancienne commande `browse` ne faisait que cela ; `/browse` ouvre toujours la
même page).

![La vue par dossiers : l'arbre des dossiers à gauche, les photos du dossier Anniversaire à droite dont deux marquées à mettre de côté et la ligne d'enregistrement](../images/browse.webp)

- **L'arborescence** : vos dossiers montés, ouverts ; les dossiers en dessous, fermés (▸ en ouvre
  un). Cliquez un dossier : ses photos et vidéos apparaissent, triées par nom, par date ou par
  taille, la plus grande d'abord (**Trier par**). **Afficher** garde les photos ou les vidéos
  seulement. Les deux choix sont gardés, dans ce navigateur, pour le dossier suivant.
- **⚖ Fichiers les plus lourds**, au-dessus des dossiers : les fichiers les plus lourds de tous
  les dossiers montés, les vidéos d'abord, 200 à la fois (**En montrer plus** en ajoute autant).
  La barre dit ce que pèse la liste : *200 fichiers, 61,4 Go, 25 % de votre photothèque*.
  **Trier par** *débit* met en tête les vidéos les moins bien compressées pour leur durée
  (anciens appareils, MJPEG) : celles qui gagnent le plus une fois allégées.
- Regarder, choisir et mettre de côté marchent comme partout sur cette page ; ouverte depuis la
  [page d'accueil](home.md), **Appliquer maintenant** lance `clean --decisions` pour vous.

## Mettre des photos de côté

Pour retirer toutes les photos de quelqu'un, la page
[`people`](people.md#retirer-toutes-les-photos-de-quelquun) le fait depuis son groupe de visages.
Pour celles d'un évènement, ou tout autre choix : cherchez-les (`person:"Anne"`, une année, un
mot), choisissez-les (Ctrl+A, puis **Choisir les N fichiers trouvés** : tous les fichiers que la
recherche trouve, pas seulement les 240 affichés), puis Suppr ou **Mettre de côté les fichiers
choisis**.

- Rien n'est supprimé depuis la page. Le choix est enregistré aussitôt dans `decisions.json` de
  vos rapports, relu sur le disque et affiché avec son nombre et sa taille : *37 fichiers mis de
  côté (412 Mo), enregistrés dans … : 'clean --decisions' les déplace en quarantaine, et s'en
  souvient : si l'un d'eux revient (une nouvelle copie depuis le téléphone), l'audit le propose à
  nouveau.* Les photos
  mises de côté portent une étiquette rouge *à mettre de côté*.
- **Retirer de la mise de côté**, affiché dès qu'un fichier choisi est mis de côté, en retire les
  fichiers choisis.
- Quand vous arrêtez la page, `search` propose l'étape suivante : `mh clean --decisions`. Il
  demande d'abord combien de fichiers et d'octets partent (à part des doublons), les déplace en
  quarantaine, journalisé ; [`undo`](undo.md) les remet, [`purge`](purge.md) libère la place.
- Un fichier modifié depuis votre choix (autre taille ou date) est laissé en place et listé dans
  le rapport du nettoyage ; un fichier d'un dossier protégé fait refuser tout le fichier, comme
  partout.
- Le même `decisions.json` garde ce que [`review`](review.md) a décidé : les deux sont gardés, et
  un seul `clean --decisions` applique tout.

## Un mauvais nom sous une photo

Le nom d'une personne sous une photo porte une **×** : cliquez-la quand cette personne n'est pas
sur la photo. Les visages de la photo qui ont donné ce nom vont dans la liste `rejected` de la
personne (dans son fichier sous `/config/people/`, relié depuis `config.toml`), exactement comme
la × de la page [`people`](people.md) ; un visage que vous aviez confirmé quitte aussi ses
`faces`. Le fichier est relu et la barre dit ce qu'il contient maintenant (*Enregistré dans
config.toml, relu : 1 visage de cette photo n'est pas Chloé.*), avec **Remettre** pour annuler.
La × ne choisit jamais la photo, et la carte reste à sa place. La grande vue montre les mêmes
noms, avec la même ×, sous ses informations (`I`).

`W` dans la grande vue ouvre **Pourquoi ce nom ?** : le visage
de la photo découpé et entouré sur la photo entière (utile quand elle compte plusieurs visages), comment il a reçu le nom (*confirmé par vous*, ou *proche d'un visage que
vous avez confirmé*, avec ce visage, son fichier et le score face à `[people] similarity`), et la
personne suivante quand elle est proche aussi. **Oui, c'est …** confirme ce visage, **Pas …**
retire le nom de ce visage seulement ; les deux sont enregistrés, relus et dits de la même façon.
Échap ferme le panneau et laisse la grande vue ouverte. Comment lire le score :
[Les personnes](../reference-people.md#les-retrouver--search).

Seule cette photo perd le nom dans cette recherche. Les autres photos nommées parce qu'elles
ressemblent à un visage que vous venez de retirer gardent le leur jusqu'à ce que vous le leur
retiriez aussi ; `classify`, l'inventaire et les fichiers XMP relisent les noms à leur prochaine
exécution. Sans `/config` accessible en écriture, rien n'est enregistré et la barre dit pourquoi.

## Mettre des photos dans un album

Pour montrer des photos à d'autres (sur la télé avec [`slideshow`](slideshow.md)), rassemblez-les
dans un **album** : une liste nommée, *Crète 2023*, de photos de n'importe quels dossiers. Tapez son
nom dans **Album** (les albums déjà faits sont proposés), choisissez les photos (ou **Choisir les N
fichiers trouvés**), puis **➕ Ajouter à l'album**.

- Un album est une liste de références, rien d'autre : aucune photo n'est copiée, déplacée ni
  modifiée. Il est enregistré aussitôt dans `albums.json` de vos rapports, à côté de
  `decisions.json` (pas dans le cache : supprimer le cache garde vos albums), relu sur le disque et
  affiché : *Crète 2023 : 42 fichiers, enregistrés dans …. Seul ce fichier a changé : aucune photo
  n'a été copiée ni déplacée.*
- Ce n'est **pas** la mise de côté : *Mettre de côté* prépare un retrait, *Ajouter à l'album* un
  partage. Aucun des deux ne touche jamais la liste de l'autre.
- **Retirer de l'album** retire les photos choisies de l'album tapé ; un album laissé vide est
  supprimé.
- Une photo déplacée depuis, par [`sort`](sort.md), par [`undo`](undo.md), ou dans un dossier
  renommé dans l'Explorateur (une fois qu'un audit l'a vu), est retrouvée par son contenu :
  l'album la suit. Une photo introuvable (supprimée, ou en quarantaine) reste dans l'album, listée
  comme manquante, jusqu'à ce qu'elle revienne.
- **📺 Partager sur la télé** donne la commande qui montre l'album tapé, copiée pour vous :
  arrêtez la page, puis `mh slideshow --album "Crète 2023" --lan` ([`slideshow`](slideshow.md)).
  Pour montrer des photos une fois, pas besoin d'album : **📺 Sur la télé** dans la barre (search
  ouvert depuis la page d'accueil) montre les fichiers choisis, ou tous ceux trouvés quand rien
  n'est choisi (3000 au plus), et ouvre la télécommande.
- **📨 Préparer pour l'envoi** donne la commande qui prépare l'album pour un mail : des copies
  réduites sans la position GPS, un dossier et un zip, `mh share --album "Crète 2023"`
  ([`share`](share.md)).
- Au plus 3 000 photos ajoutées d'un coup : affinez une recherche qui en trouve plus.

Un album peut aussi devenir un dossier de l'Explorateur : [`album "Crète 2023"`](album.md) le
crée, en seconds noms (liens physiques), sans copie.

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
| `Papy dans le jardin` | Une phrase : les petits mots s'en vont (`dans`, `le`, les mots vides de `[tags]`, comme dans l'index), et un nom qu'une personne porte sur une photo est cherché parmi les personnes : lu `Papy (personne) + jardin`, dit sous la recherche. Une expression entre guillemets est gardée telle quelle. |
| `Chloé montagne` | Les photos de Chloé avec « montagne » venu de n'importe quelle source, une fois son groupe nommé dans [`people`](people.md). |
| `person:chloe`, `person:"Mamie Jeanne"` | Le nom parmi les personnes seulement. Un nom que personne ne porte encore est signalé en une ligne. |
| `un chat sur un canapé` | Après [`tags --meaning`](tags.md) : les photos qui le montrent d'abord, même sans aucun de ces mots ([recherche par le sens](../reference-tags.md#retrouver-une-photo-par-ce-quelle-montre----meaning)). |
| `Chloé cuisine` | Après `tags --meaning` : les photos de Chloé seulement, les cuisines d'abord. |

## D'où vient chaque mot

Son préfixe devant un mot limite la recherche à une source : `place:durbuy`, `folder:durbuy`,
`name:anniv*`. Une source qui n'a encore aucun mot affiche *— aucun pour l'instant* dans
*Comment écrire une recherche*.

| Source | Préfixe | Ce qu'elle contient |
|---|---|---|
| toutes les sources | | N'importe laquelle (par défaut). |
| vus par le modèle | `vision:` | Les mots que le modèle de vision a donnés à ce que montre la photo (🤖 [`tags`](tags.md)). |
| la phrase du modèle | `caption:` | Sa phrase entière : pour une expression entre guillemets. |
| dossier | `folder:` | Les mots parlants des noms des dossiers. |
| nom du fichier | `name:` | Les mots d'un nom choisi par quelqu'un (aucun pour `IMG_1234`). |
| nom d'une copie retirée | `former:` | Les dossiers et le nom qu'avait un doublon avant que [`clean`](clean.md) ne le retire, gardés sur la copie restée. |
| date | `date:` | L'année, le mois, la saison et les fêtes de la date de prise de vue. |
| lieu | `place:` | La ville et vos propres lieux où la photo a été prise. |
| personne | `person:` | Les noms donnés aux visages sur la page [`people`](people.md). |
| description Google Photos | `takeout:` | La description tapée dans Google Photos (un export Takeout). |

## Conseils pour retrouver une photo

Tant que presque aucune photo n'est décrite, une ligne sous le champ le dit : *Ce que montrent
les photos n'est pas encore connu : 0 fichiers décrits sur 44 488…*, avec l'étape qui y remédie
(🤖 `tags`). Avant `tags`, une recherche ne trouve que les mots des dossiers, des noms, des
dates, des lieux et des personnes.

| Recherché | Ne trouve rien parce que | Essayez plutôt |
|---|---|---|
| `un vieil homme` | **Chaque mot doit être trouvé** : `un` et `vieil` et `homme` ; un petit mot compte aussi. | `homme`, puis moins de mots. |
| `vieil homme`, `grand-mère`, `femme` | **Le modèle n'écrit jamais d'âge, de sexe ni de lien de parenté** : pour les personnes, il n'écrit que *adulte*, *enfant*, *bébé* ou *groupe*. | `person:` et le nom de la personne (nommée sur la page [`people`](people.md)), ou `adulte`. |
| `un vieil homme dans un jardin` | **Une phrase entière demande la recherche par le sens** (`tags --meaning`) ; sans elle, des mots seulement. | `jardin` ; ou lancez une fois 🤖 `tags --meaning` : les phrases marchent alors. |
| `plage` pendant un `tags` | **Les mots du modèle arrivent dans la recherche à la fin du run** (ou après un seul Ctrl+C, qui écrit ceux des photos déjà décrites). | Attendez la fin de `tags`, ou un Ctrl+C. |

Rien trouvé ? Moins de mots, le début d'un mot (`anniv*`), le préfixe d'une autre source (`folder:`), ou
la recherche par le sens. La page garde ces conseils courts, dans *Comment écrire une
recherche*.

## Options

| Option | Rôle |
|---|---|
| `MOTS` | Les mots à trouver, affichés en tableau au lieu d'ouvrir la page. |
| `--limit N` | Avec des mots : combien de fichiers le tableau liste au plus (20 par défaut). |
| `--folder DOSSIER` | Sans mots : la page s'ouvre sur ce dossier, comme *Chemin contient* le prend (un dossier que `status` liste comme restant à trier). |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- **Pendant un `tags`**, une photo décrite il y a un instant apparaît à une recherche une
  vingtaine de secondes plus tard (la page relit les nouveaux mots au plus aussi souvent pendant
  que le modèle écrit ; un déplacement fait depuis la page elle-même apparaît aussitôt).
- **Ouverte depuis la page d'accueil** (`mh` seul) : la page s'ouvre aussitôt, dans le même onglet,
  servie par la page d'accueil elle-même : aucun autre conteneur ne démarre, l'index reste ouvert
  pour la session. *⌂ Retour à l'accueil* est un simple lien (le bouton Précédent du navigateur
  marche aussi). Tapée seule (`mh search`), elle démarre toujours sa propre page.
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
