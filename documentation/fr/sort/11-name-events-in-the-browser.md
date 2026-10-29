# 11. Nommer les événements dans le navigateur

[Documentation](../README.md) › Trier, étape 11 · 🇬🇧 [English](../../en/sort/11-name-events-in-the-browser.md)

**Pourquoi nommer un événement ?** Un [événement](../reference-glossary.md#événement), ce sont les
photos d'un même moment (une kermesse, un week-end), réunies par `classify` d'un dossier ou d'un
téléphone à l'autre. Son nom devient **le dossier où `sort` range toutes ses photos** : nommé
`Kermesse`, il va dans `2016/2016-07/Kermesse` ; sans nom, ses fichiers restent où ils sont. Ce qui bouge
sur le disque, nom ou catégorie : [`review-sort`, à quoi ça sert](../commands/search.md#les-événements-du-dernier-classify).

Le classeur de l'[étape 5](05-review-the-proposal.md) est fait pour renommer en masse, pas pour
*regarder* les photos : nommer un événement, c'est lire le rapport dans une fenêtre et taper dans
l'autre. Avec des centaines d'événements, cela fait des centaines d'allers-retours.
`review-sort` réunit les deux dans une page de votre navigateur : **un événement à la fois, ses
photos, sa proposition, et un champ pour le nommer**, le tout au clavier.

C'est facultatif : le classeur seul suffit, et les deux s'utilisent ensemble. La page ne touche
ni aux photos ni au classeur ; c'est `sort` ([étape 7](07-sort.md)) qui applique vos choix.

## Lancer la page

Lancez d'abord `classify` ([étape 4](04-classify.md)). Lancez ensuite la page avec les mêmes
dossiers et le même dossier de rapports, que `mh` monte (la lecture seule suffit pour les photos :
la page ne fait que les montrer) :

```powershell
mh review-sort
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

</details>

Comme pour [le tri des rafales](../clean/10-review-bursts.md#étape-1--lancer-le-tri),
`mh` ouvre la page à votre ordinateur seulement, sur le port 8088 (`-p 127.0.0.1:8088:8088` dans
la commande complète). La page
lit le classeur du dernier `classify`, celui qu'applique `sort` ; nommez-en un autre après la
commande : `review-sort "C:\Photos triées\reports\20261002-123210-classify\classify.xlsx"`.

```text
412 événements à décider : 260 avec une proposition sûre (un clic), 152 à regarder.
✅ Revue prête, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Chaque
choix est enregistré aussitôt dans
C:\Users\vous\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
Ctrl+C arrête la revue.
💡 La page ne s'ouvre pas ? docker run doit publier le même port des deux côtés,
avec -p 127.0.0.1:8088:8088.
```

Ctrl+clic sur l'adresse pour ouvrir la page.

## Lire la page

Les événements arrivent **dans l'ordre de la feuille Événements** : ceux qui restent à décider
d'abord, les plus grands d'abord. La page s'ouvre sur le premier qui reste à décider (ou là où
vous vous étiez arrêté). Pour chaque événement :

- **en haut** : son nom (ou ses dates), son nombre de fichiers et combien restent à vérifier ou à
  trier, et la part du travail que couvre le fait de nommer les événements jusqu'à celui-ci ;
- **Depuis** : les dossiers d'où viennent ses photos ;
- **État** : une ligne : « proposé par classify (sa bande, pourquoi), pas encore validé »,
  « modifié, pas encore enregistré : Entrée l'enregistre, Échap l'abandonne », « validé ici à
  14:32 » (l'heure que contient `sort-decisions.json`, relue sur le disque), ou ce qu'a décidé le
  classeur (en rouge quand il dit autre chose que la page) ;
- **les photos**, par date, chacune avec sa date. Une photo dont le dossier proposé diffère de
  celui de l'événement l'affiche (→ …) ; une photo envoyée ailleurs est encadrée en vert ; 🔒
  marque un fichier laissé tel quel (dossier protégé ou `leave`), qu'aucun choix ne déplace.

Le champ **Dossier** contient le dossier de l'événement sous son année (`2011/`, affiché devant
le champ) : `Fêtes/Communions/Communion de Manon` donne `2011/Fêtes/Communions/Communion de
Manon`. Il est rempli avec la proposition et se complète avec les dossiers déjà utilisés. La
ligne en dessous dit, pendant que vous tapez, où vont les fichiers, calculé comme le fera
`sort` : « → 212 fichiers vont dans C:\Photos\2011\Fêtes\Communions\Communion de Manon · 40
fichiers gardent leur propre dossier (Budva…) ». Le **nom** de l'événement (les albums
l'utilisent) est le dernier dossier ; changez-le sous *Nom de l'événement* (<kbd>E</kbd>). Un
dossier tapé et non enregistré n'est jamais perdu en silence : passer à un autre événement
demande s'il faut l'enregistrer, fermer l'onglet prévient.

## Les touches

| Touche | Ce qu'elle fait |
|---|---|
| <kbd>Entrée</kbd> | Aucune photo encadrée : enregistrer le dossier, puis passer à l'événement suivant à décider. |
| <kbd>N</kbd> / <kbd>P</kbd> (ou Page suivante / Page précédente) | Événement suivant ou précédent, sans décider : les boutons ← → autour de *Événement 1 sur 1137* dans la barre. |
| <kbd>U</kbd> | Événement suivant à décider. |
| <kbd>V</kbd> | Accepter d'un coup toutes les propositions sûres (voir plus bas). |
| <kbd>Maj</kbd>+<kbd>Z</kbd> | Reprendre ce lot. |
| <kbd>F</kbd> / <kbd>E</kbd> | Taper le dossier / changer le nom de l'événement ; <kbd>Échap</kbd> abandonne ce qui est tapé et non enregistré. |
| <kbd>Maj</kbd>+<kbd>S</kbd> | Laisser tout l'événement où il est (« (rester où il est) »). |
| <kbd>O</kbd> | Envoyer les photos choisies (sinon celle encadrée) dans un autre dossier : tapez-le, <kbd>Entrée</kbd>. |
| <kbd>S</kbd> | Laisser les photos choisies (sinon celle encadrée) où elles sont. |
| <kbd>Suppr</kbd> | Reprendre le choix fait ici : des photos choisies, sinon de l'événement. Le classeur décide à nouveau. |

Les photos se choisissent comme dans [les dossiers de `search`](../commands/search.md#parcourir-vos-dossiers) : un clic choisit une
photo ; la case ☑ de chaque vignette (ou Ctrl+clic) en ajoute ou en retire une ; Maj+clic choisit
toutes les photos depuis la dernière cliquée ; un rectangle tiré à la souris sur la grille choisit
ce qu'il touche (avec Ctrl, il s'ajoute au choix) ; Ctrl+A toutes les photos de l'événement.
**Inverser la sélection** (ou I) choisit les autres. Les flèches déplacent le cadre, Espace
choisit la photo encadrée, Entrée (ou un double clic) l'ouvre en grand : ← → y passent d'une photo
à l'autre, F plein écran, Échap referme. Une fois des photos choisies, la barre propose **Envoyer
dans un autre dossier (O)**, **Laisser où elles sont (S)**, et **Reprendre le choix fait ici**
quand l'une d'elles a été choisie ici. Une photo choisie ici porte l'étiquette verte *choisi ici*.

Une photo envoyée dans un autre dossier reçoit le dossier que la disposition lui donne, comme si
vous l'aviez tapé dans sa cellule **Dossier final** : `2016/2016-07/Best of` avec la disposition
par défaut.

## Accepter d'un coup les propositions sûres

Sur une grande collection, beaucoup d'événements ont une proposition **sûre** : la plupart de
leurs photos viennent d'une règle forte (bande *Sûrs*), et les quelques-unes qui restent à
vérifier ou à trier proposent la même catégorie, ou aucune. Un tel événement affiche `✔ sûre`
après sa proposition ; un coup d'œil suffit.

Le bouton **✔ Accepter N propositions sûres (M fichiers)** en haut (ou <kbd>V</kbd>) les
accepte toutes, après une confirmation qui donne les chiffres et **liste les événements** :
chacun avec les fichiers qui bougent et son dossier ; un clic sur l'un d'eux l'affiche dans la
page, pour regarder avant d'accepter. Chacune est enregistrée exactement
comme <kbd>Entrée</kbd> l'enregistrerait sur cet événement laissé tel quel (sa catégorie
proposée, sans nom), avec ce qu'en disait le classeur, comme tout autre choix. La confirmation
compte les fichiers qui bougent, et ceux qui gardent un dossier que vous aviez nommé : ceux-là ne
sont jamais aplatis dans le dossier proposé. Rien n'est imposé : un événement déjà choisi, ici ou dans le classeur, n'est pas touché, et une
modification ultérieure du même événement dans le classeur reste un conflit, jamais réglé en
silence.

Le lot est **une seule écriture** de `sort-decisions.json`, relue sur le disque avant que la page ne
l'affiche : la ligne d'état donne l'heure à laquelle le disque la contient. **↶ Reprendre le lot**
(ou <kbd>Maj</kbd>+<kbd>Z</kbd>) oublie tout le lot, lui aussi en une seule écriture (un événement
choisi à nouveau depuis garde votre nouveau choix).

Cochez **Seulement les événements à décider** pour que <kbd>N</kbd>, <kbd>P</kbd> et <kbd>U</kbd>
sautent les événements déjà choisis et ceux dont la proposition est sûre : il ne reste que ceux
qui ont besoin de vous. Cochez plutôt **Seulement les propositions sûres** pour parcourir les
sûres une par une avant de les accepter. Une case à la fois ; le navigateur s'en souvient pour la
prochaine ouverture de la page.

## Retenir un événement comme règle

Un choix fait ici vaut pour cette proposition ; une **règle** vaut pour chaque `classify`
suivant, les photos ajoutées plus tard comprises (une nouvelle copie du téléphone, le dossier
d'une personne des mêmes jours). **📌 Retenir comme règle** (ou <kbd>R</kbd>) écrit l'événement
affiché comme une règle `date_range` ([étape 6](06-write-down-what-you-know.md#les-dates)) : son
nom (le dernier dossier), ses jours (ceux de l'événement, que vous pouvez élargir), son dossier,
et `keep_folders = true` pour que vos propres dossiers restent en dessous. Avant
d'enregistrer, la boîte dit ce que la règle prendrait sur cette proposition : « 236 fichiers : 6
de cet événement, 230 d'autres événements ou dossiers les mêmes jours. Ailleurs : Photos Chloé
(230) », et les règles dont elle partage des jours (la première listée l'emporte ces jours-là).
Enregistrée, la règle est écrite dans `config.toml` juste au-dessus de *Dossiers existants*,
vos commentaires conservés, relue sur le disque et annoncée avec son heure ; le dossier de
l'événement est choisi en même temps, si bien que *Trier cet événement maintenant* marche tout
de suite. La colonne de gauche nomme ensuite la règle qui décide les fichiers de l'événement :
*Règle : Montenegro (2019-07-12..2019-07-19)*.

## Trier un événement maintenant

**Trier cet événement maintenant** (ou <kbd>M</kbd>) range la collection événement par
événement : il enregistre le dossier au besoin, montre où vont les fichiers (la ligne sous le
champ) et demande, puis déplace les fichiers de cet événement seulement, comme le fait
[`sort --event`](../commands/sort.md) : notés au journal, chaque exécution avec son propre
`undo`. La ligne d'état donne ce que contient le disque après l'exécution : les fichiers
déplacés et vérifiés à leur nouvelle place. L'événement s'affiche ensuite *trié*, et <kbd>U</kbd>
et *Seulement les événements à décider* le sautent ; un `sort` ultérieur de tout le classeur
saute ses fichiers. Les photos doivent être montées sans `:ro`, avec un `/journal`
(`mh review-sort` le fait) : sinon la page dit ce qui manque, et rien ne bouge.

**Vérifier d'abord, puis GO.** Chaque photo de l'événement dit où elle est et où elle va, tel
que `sort` la déplacera. Avant de déplacer, *Vérifier, puis trier* les liste par dossier
(*14 → …\Mariage d'Hervé et Magda*, à part les fichiers qui restent) ; **J'ai vérifié : trier
ces N fichiers** est le GO. Pour laisser des photos de côté, choisissez-les et appuyez d'abord sur
<kbd>S</kbd>. Commencez par un petit événement : vous voyez ce que fait l'outil, fichier par
fichier, avant de lui en confier plus. Une période ou une règle se trie de la même façon depuis
la page de recherche ([`search`](../commands/search.md#faire-dune-période-une-règle)).

## Suivre l'avancement

En triant un événement à la fois, la colonne de gauche dit où vous en êtes, d'après le plan et le
journal : *Triés : 23 événements, 1 840 fichiers (10,8 %) · déjà en place : 35 000 fichiers ·
restent : 1 114 événements, 15 216 fichiers à déplacer* — relu après chaque GO. Chaque
événement dit son état : *trié* (ses fichiers ont bougé), *en place* (rien à déplacer), *validé
ici* (choisi, pas encore trié) ou *proposé par classify* (à décider). **Seulement les événements
pas encore triés**, à côté des deux autres filtres (un seul à la fois), garde ceux qui ont encore
des fichiers à déplacer : <kbd>N</kbd>, <kbd>P</kbd> et <kbd>U</kbd> ne parcourent alors
qu'eux.

*Les tris de ce plan*, en dessous, liste chaque tri, le plus récent d'abord : *25/10 14:32 ·
Mariage d'Hervé et Magda · 14 fichiers · undo 20261025-143212* ; un tri repris par `undo` est
barré. Rien n'est déplacé pour suivre l'avancement : pas de dossier *À trier* à vider, vos propres
dossiers restent tels quels jusqu'à ce que vous décidiez.

Cette page compte le travail du plan en cours. **Ce qui est trié pour de bon** se lit dans
l'arborescence elle-même, sans plan ni journal, par `mh status` et l'espace *Trier* de la page
d'accueil : *Trié 62 % · rien de spécial 9 % · reste 16 400 fichiers* — un fichier dans
`année/année-mois/<nom>` est trié, quoi qui l'ait déplacé ([`status`](../commands/status.md)).

## Où vont vos choix

Chaque choix est enregistré aussitôt dans `sort-decisions.json`, **à côté de `plan.json`**, dans
le dossier de l'exécution de `classify`. Le classeur n'est jamais modifié (Excel peut l'avoir
ouvert). Arrêtez la page avec <kbd>Ctrl</kbd>+<kbd>C</kbd>, relancez-la : elle reprend.

```text
✅ Revue arrêtée — événements choisis : 37, photos choisies une à une : 12.
Vos choix sont dans C:\Users\vous\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
```

`sort` lit les deux, les choix de la page **par-dessus** le classeur, et le dit :

```text
12 modifications lues ; classeur enregistré le 2 octobre 2026 à 14:32.
49 choix de la page de revue appliqués par-dessus le classeur (3 remplaçant une modification du
classeur, 0 identiques aux deux endroits).
```

Vous pouvez continuer à modifier le classeur : une seule source de vérité, le plan, et jamais de
conflit silencieux. Chaque choix de la page retient ce que le classeur disait de cet événement ou
de ce fichier au moment où vous l'avez fait :

- **le classeur dit toujours la même chose** : votre choix dans la page est le plus récent, il
  l'emporte ;
- **le classeur dit ce que vous avez choisi** : rien à régler ;
- **le classeur a été modifié depuis, sur le même événement ou fichier, autrement** : personne ne
  peut savoir lequel vous vouliez. `sort` refuse de déplacer quoi que ce soit et les liste, avec
  les deux valeurs ; la page les montre en rouge. Choisissez à nouveau dans la page (elle montre
  les deux), ou appuyez sur <kbd>Suppr</kbd> pour laisser décider le classeur, ou remettez la
  cellule du classeur comme avant.

Les autres règles de l'[étape 5](05-review-the-proposal.md#le-classeur--modifier-les-cellules-jaunes)
restent vraies : le choix le plus précis l'emporte (un fichier, sinon son événement, sinon sa
catégorie), et les compagnons (une Live Photo, un fichier RAW et son JPEG) suivent un seul dossier.

**Relancez `classify`** et vos choix de la page sont repris comme vos modifications
([étape 5](05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail)) : ils
arrivent dans les cellules jaunes du nouveau classeur, et la nouvelle exécution commence avec un
`sort-decisions.json` vide. Un choix que le classeur contredit depuis n'est pas repris : c'est la
valeur du classeur qui l'est, et celle de la page est listée parmi les modifications laissées de
côté.

---

← [10. Trier par personne](10-sort-by-person.md) · [Documentation](../README.md) · Suite : **[12. Albums](12-albums.md)** →
