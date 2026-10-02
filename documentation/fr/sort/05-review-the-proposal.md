# 5. Revoir la proposition : le classeur et le rapport

[Documentation](../README.md) › Trier, étape 5 · 🇬🇧 [English](../../en/sort/05-review-the-proposal.md)

`classify` a proposé une place pour chaque fichier ([étape 4](04-classify.md)). Avant que rien ne
bouge, vous corrigez cette proposition là où elle se trompe, et vous nommez ce que l'outil ne
pouvait pas nommer : un voyage, une fête. Deux fenêtres côte à côte :

- **un classeur**, `classify.xlsx`, ouvert dans Excel ou LibreOffice : c'est là que vous
  **modifiez** ;
- **un rapport**, `report.html`, ouvert dans votre navigateur : c'est là que vous **regardez** les
  photos.

## Obtenir les deux fichiers

Montez un dossier de rapports, comme pour [les rapports HTML](../clean/04-html-report.md) :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr classify
```

La fin de l'affichage dit où sont les fichiers :

<!-- capture: classify.txt|Classeur à modifier| -->
```text
✅ Classeur à modifier : /reports/20261002-152701-classify/classify.xlsx
✅ Rapport avec les photos : /reports/20261002-152701-classify/report.html
💡 Modifiez les cellules jaunes et enregistrez : rien ne bouge avant 'sort'.
```

Chaque exécution écrit un nouveau dossier, `<date>-classify`, avec trois fichiers :

| Fichier | Ce que c'est |
|---|---|
| `classify.xlsx` | Le classeur que vous modifiez. |
| `report.html` | Le rapport, avec une page par année et les aperçus. |
| `plan.json` | Toute la proposition, fichier par fichier. Le classeur lui appartient : gardez-les ensemble, et ne le modifiez pas. |

Sans dossier de rapports, la proposition reste seulement à l'écran : un classeur modifié dans un
dossier que le conteneur oublie serait du travail perdu.

## Le rapport : regarder les photos

La première page donne l'avancement, le travail restant, les années, **par où commencer** (les
événements qui concentrent l'essentiel du travail) et **la collection une fois triée** : les
dossiers proposés avec leur nombre de fichiers, avant que rien ne bouge.

![La première page du rapport de classify : quatre compteurs (fichiers, déjà à leur place, à vérifier ou à trier, événements), un tableau des années avec des liens vers leurs pages, les événements par où commencer avec leur part du travail, puis l'arborescence proposée avec le nombre de fichiers de chaque dossier](../images/classify-report.webp)

Chaque année a sa propre page : des dizaines de milliers d'aperçus ne tiennent pas sur une seule.
Elle liste d'abord les événements, **avec les identifiants et l'ordre de la feuille Événements du
classeur**, puis les fichiers hors de tout événement, regroupés par dossier proposé. Chaque groupe
montre ses dates, ses fichiers, les dossiers d'où ils viennent, le dossier proposé et pourquoi, et
jusqu'à 8 aperçus répartis sur sa durée. Cliquez sur un aperçu pour ouvrir le fichier ; *Tous les
fichiers* les liste tous.

![Une page d'année du rapport de classify : un événement de vacances avec son identifiant, son nombre de fichiers dont quelques-uns à vérifier ou à trier, la part cumulée du travail, le dossier proposé marqué Sûr, les dossiers d'où viennent ses photos, puis huit aperçus répartis sur ses jours avec leurs noms et leurs heures, et un lien vers tous les fichiers](../images/classify-year.webp)

## Le classeur : modifier les cellules jaunes

Seules les cellules jaunes peuvent être modifiées ; le reste est verrouillé, pour qu'une fausse
manœuvre ne casse pas le fichier. Chaque feuille a une colonne **Notes** libre, pour vous : elle
n'est jamais lue.

| Feuille | Une ligne par | Ce que vous pouvez changer |
|---|---|---|
| Résumé | — | Rien : l'avancement, les fichiers par bande, année, catégorie, raison et source de la date. |
| Catégories | catégorie proposée | **Nouveau nom** : renommer la catégorie partout. **Confirmer les fichiers à vérifier** : `oui` rend sûrs, d'un coup, ses fichiers « à vérifier ». |
| Événements | événement | **Nom** : le nom de l'événement (`Italie 2023`), qui devient son dossier. **Catégorie** : le dossier, choisi dans la liste ou tapé. |
| Fichiers | photo ou vidéo | **Dossier final** : le dossier de ce fichier, relatif à la cible (`2016/Kermesse`). |

**Commencez par la feuille Événements.** C'est une liste de travail : les événements pas encore
décidés viennent d'abord, les plus grands d'abord, et la colonne *Part du travail, cumulée* dit
quelle part du travail couvre le fait de nommer les lignes au-dessus. Le plus souvent, nommer les
dix premières lignes règle l'essentiel de la collection : un seul nom couvre quelques centaines de
photos. Les événements déjà décidés (un dossier que vous aviez nommé, des fichiers déjà à leur
place) viennent en dernier.

Quelques règles :

- **La modification la plus précise l'emporte** : le dossier final d'un fichier, sinon celui de
  son événement, sinon celui de sa catégorie.
- **Les compagnons suivent un seul dossier** : une Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`) ou un
  fichier RAW et son JPEG ont une ligne chacun, mais se déplacent ensemble. Un dossier final tapé
  sur **n'importe laquelle** de leurs lignes décide pour tous ; deux de leurs lignes avec des
  dossiers finaux différents sont refusées par `sort`, qui nomme les deux cellules
  ([étape 7](07-sort.md#comment-les-fichiers-bougent)).
- **Votre modification est sûre** : un fichier que vous placez vous-même quitte la bande « à
  vérifier ».
- **(rester où il est)** est une valeur de chaque liste : le fichier, l'événement ou la catégorie
  est laissé où il est.
- Les dossiers s'écrivent relativement à la cible, avec `/` ou `\` : `2016/Kermesse`. Un nom que
  Windows refuse, ou un dossier qui sort de la cible (`..`), est refusé avec sa cellule.
- Excel ne peut pas trier des cellules verrouillées : les feuilles arrivent déjà triées dans leur
  ordre le plus utile. Utilisez les **filtres** de la ligne d'en-tête pour restreindre une feuille.
- Enregistrez le classeur là où il est, sous son nom, au format `.xlsx`.

## Améliorer la proposition sans perdre votre travail

Changez un réglage (`merge_gap_hours`, une règle de l'[étape 6](06-write-down-what-you-know.md)),
ajoutez de nouvelles photos, et relancez `classify` : **vos modifications sont reprises** dans le
nouveau classeur. Il lit le classeur du dernier `classify`, celui que `sort` appliquerait, et
remplit les cellules jaunes du nouveau avec ce que vous aviez saisi, notes comprises :

```text
✅ 412 modifications reprises du classeur enregistré le 2 octobre 2026 à 14:32 :
C:\Photos triées\reports\20261002-123210-classify\classify.xlsx
```

- **Un fichier garde sa modification** même s'il a été renommé ou déplacé entre-temps : il est
  reconnu par son contenu (le SHA-256 de l'audit), par son chemin seulement quand le contenu
  n'est pas connu.
- **Un événement garde son nom** dans le nouvel événement qui contient la plupart de ses
  fichiers. Un événement coupé en deux donne son nom aux deux parties, et `classify` le dit.
- **Une catégorie garde son nouveau nom** et son « confirmer » tant qu'elle est encore proposée.
- Une modification reprise est la vôtre : le fichier est sûr, avec la raison `carried-over`, et
  vous pouvez changer la cellule jaune à nouveau.
- **Rien n'est abandonné en silence** : une modification dont le fichier a disparu, dont la
  catégorie n'est plus proposée, ou dont l'événement a fusionné avec un autre événement nommé,
  est listée à l'écran et dans le rapport, pour la saisir à nouveau là où elle va.
- Les modifications qu'un `sort` a déjà appliquées ne sont pas reprises : ces fichiers sont à
  leur place, et `classify` les y voit.

`--carry-over <classeur>` reprend les modifications d'un autre classeur (une copie gardée, une
exécution plus ancienne) ; `--no-carry-over` repart de zéro. Un classeur que `sort` refuse (une
colonne supprimée, une feuille renommée) est quand même lu, aussi loin que ses identifiants et ses
cellules jaunes peuvent être trouvés : relancer `classify` est la porte de sortie. Si le dernier
classeur ne peut pas être ouvert du tout, `classify` s'arrête avant d'écrire quoi que ce soit, pour
que vos modifications ne soient pas enfouies sous un classeur plus récent et vide.

Des centaines d'événements à nommer ? L'[étape 10](10-name-events-in-the-browser.md) les montre un
par un dans votre navigateur, avec leurs photos et un champ pour les nommer, sans changer de
fenêtre.

Rien ne bouge encore : appliquer le classeur à vos dossiers est le rôle de `sort`
([étape 7](07-sort.md)). Il vérifie à nouveau le classeur avant de déplacer quoi que ce soit : un
classeur d'une autre exécution, ou dont des lignes, des feuilles ou des cellules verrouillées ont
été changées, est refusé.

---

← [4. Proposer une arborescence](04-classify.md) · [Documentation](../README.md) · Suivant : **[6. Écrire ce que vous savez](06-write-down-what-you-know.md)** →
