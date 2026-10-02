# 10. Nommer les événements dans le navigateur

[Documentation](../README.md) › Trier, étape 10 · 🇬🇧 [English](../../en/sort/10-name-events-in-the-browser.md)

Le classeur de l'[étape 5](05-review-the-proposal.md) est fait pour renommer en masse, pas pour
*regarder* les photos : nommer un événement, c'est lire le rapport dans une fenêtre et taper dans
l'autre. Avec des centaines d'événements, cela fait des centaines d'allers-retours.
`review-sort` réunit les deux dans une page de votre navigateur : **un événement à la fois, ses
photos, sa proposition, et un champ pour le nommer**, le tout au clavier.

C'est facultatif : le classeur seul suffit, et les deux s'utilisent ensemble. La page ne touche
ni aux photos ni au classeur ; c'est `sort` ([étape 7](07-sort.md)) qui applique vos choix.

## Lancer la page

Lancez d'abord `classify` ([étape 4](04-classify.md)). Montez ensuite les mêmes dossiers et le
même dossier de rapports (la lecture seule suffit pour les photos : la page ne fait que les
montrer) :

```powershell
docker run --rm -it --name media-hygiene-review -p 127.0.0.1::8080 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

Comme pour [le tri des rafales](../clean/10-review-bursts.md#étape-1--lancer-le-tri),
`-p 127.0.0.1::8080` ouvre la page à votre ordinateur seulement, sur un port choisi par Docker. La
page lit le classeur du dernier `classify`, celui qu'applique `sort` ; nommez-en un autre après la
commande : `review-sort "C:\Photos triées\reports\20261002-123210-classify\classify.xlsx"`.

```text
✅ Revue prête sur le port 8080 : chaque choix est enregistré aussitôt dans
C:\Users\vous\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
Ctrl+C arrête la revue.
💡 Son adresse sur votre ordinateur : lancez 'docker port 11f20c1a9952 8080'
dans un autre terminal, puis ouvrez http://<cette adresse> dans votre
navigateur.
```

Dans une autre fenêtre, `docker port media-hygiene-review 8080` donne l'adresse à ouvrir, par
exemple `http://127.0.0.1:49153`.

## Lire la page

Les événements arrivent **dans l'ordre de la feuille Événements** : ceux qui restent à décider
d'abord, les plus grands d'abord. La page s'ouvre sur le premier qui reste à décider (ou là où
vous vous étiez arrêté). Pour chaque événement :

- **en haut** : son nom (ou ses dates), son nombre de fichiers et combien restent à vérifier ou à
  trier, et la part du travail que couvre le fait de nommer les événements jusqu'à celui-ci ;
- **Depuis** : les dossiers d'où viennent ses photos ;
- **Proposé** : le dossier que propose `classify`, sa bande et pourquoi ;
- **Classeur** : ce qu'en dit la feuille Événements, si vous y avez tapé quelque chose ;
- **Choisi ici** : votre choix dans la page ;
- **les photos**, par date, chacune avec sa date. Une photo dont le dossier proposé diffère de
  celui de l'événement l'affiche (→ …) ; une photo envoyée ailleurs est encadrée en vert ; 🔒
  marque un fichier laissé tel quel (dossier protégé ou `leave`), qu'aucun choix ne déplace.

Le champ **Nom** est le nom de l'événement, comme dans la feuille Événements : il devient son
dossier, sauf si vous donnez une **Catégorie**. Le champ catégorie est rempli avec la proposition
et se complète avec les catégories déjà utilisées.

## Les touches

| Touche | Ce qu'elle fait |
|---|---|
| <kbd>Entrée</kbd> | Accepter le nom et la catégorie, puis passer à l'événement suivant à décider. |
| <kbd>N</kbd> / <kbd>P</kbd> (ou Page suivante / Page précédente) | Événement suivant ou précédent, sans décider. |
| <kbd>U</kbd> | Événement suivant à décider. |
| <kbd>E</kbd> / <kbd>C</kbd> | Taper dans le champ nom / catégorie ; <kbd>Échap</kbd> en sort. |
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

← [9. Lieux et voyages grâce au GPS](09-places-from-gps.md) · [Documentation](../README.md)
