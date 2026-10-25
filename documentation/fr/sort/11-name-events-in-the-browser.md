# 11. Nommer les événements dans le navigateur

[Documentation](../README.md) › Trier, étape 11 · 🇬🇧 [English](../../en/sort/11-name-events-in-the-browser.md)

**Pourquoi nommer un événement ?** Un [événement](../reference-glossary.md#événement), ce sont les
photos d'un même moment (une kermesse, un week-end), réunies par `classify` d'un dossier ou d'un
téléphone à l'autre. Son nom devient **le dossier où `sort` range toutes ses photos** : nommé
`Kermesse`, il va dans `2016/Kermesse` ; sans nom, dans `2016/À trier/2016-07-14`. Ce qui bouge
sur le disque, nom ou catégorie : [`review-sort`, à quoi ça sert](../commands/review-sort.md#à-quoi-ça-sert).

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
| <kbd>Entrée</kbd> | Enregistrer le dossier, puis passer à l'événement suivant à décider. |
| <kbd>N</kbd> / <kbd>P</kbd> (ou Page suivante / Page précédente) | Événement suivant ou précédent, sans décider. |
| <kbd>U</kbd> | Événement suivant à décider. |
| <kbd>V</kbd> | Accepter d'un coup toutes les propositions sûres (voir plus bas). |
| <kbd>Maj</kbd>+<kbd>Z</kbd> | Reprendre ce lot. |
| <kbd>F</kbd> / <kbd>E</kbd> | Taper le dossier / changer le nom de l'événement ; <kbd>Échap</kbd> abandonne ce qui est tapé et non enregistré. |
| <kbd>Maj</kbd>+<kbd>S</kbd> | Laisser tout l'événement où il est (« (rester où il est) »). |
| <kbd>←</kbd> <kbd>→</kbd> | Passer d'une photo à l'autre. |
| <kbd>Espace</kbd> | Sélectionner la photo (ou cliquer dessus). |
| <kbd>O</kbd> | Envoyer les photos sélectionnées (sinon la photo courante) dans une autre catégorie : tapez-la, <kbd>Entrée</kbd>. |
| <kbd>S</kbd> | Laisser les photos sélectionnées (sinon la photo courante) où elles sont. |
| <kbd>Suppr</kbd> | Reprendre le choix fait ici : des photos sélectionnées, sinon de l'événement. Le classeur décide à nouveau. |
| <kbd>Z</kbd> | Agrandir la photo courante ; <kbd>Échap</kbd> la referme. |

Une photo envoyée dans une autre catégorie reçoit le dossier que la disposition donne à cette
catégorie, comme si vous l'aviez tapé dans sa cellule **Dossier final** : `2016/Best of` avec
`layout = "{year}/{category}"`.

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
