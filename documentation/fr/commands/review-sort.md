# `review-sort` : nommer les événements dans votre navigateur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `review-sort` · 🇬🇧 [English](../../en/commands/review-sort.md)

> Le bouton de la page sur la [page d'accueil](home.md) (`mh` seul) l'ouvre ; la commande reste là pour un script ou sans la page d'accueil, mais `mh --help` ne la liste plus.

## En bref

**Donner un nom à chaque sortie, fête ou voyage de vos photos, en les regardant : ce nom devient
leur dossier quand [`sort`](sort.md) range votre collection.**

`review-sort` montre **un [événement](../reference-glossary.md#événement) à la fois** dans votre
navigateur, avec ses photos, la proposition de [`classify`](classify.md) et un champ pour le
nommer, au clavier. Rien ne bouge ici : vos choix sont enregistrés à côté de la proposition, et
c'est `sort` qui déplace les fichiers.

**Quand** : facultatif, entre `classify` et `sort`. La feuille Événements du
[classeur](../reference-glossary.md#classeur) fait le même travail, sans les photos sous les yeux ;
les deux peuvent servir ensemble.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

## À quoi ça sert

**Un événement, c'est un moment de votre vie vu par vos photos** : une kermesse, un week-end à la
mer, un Noël. `classify` les retrouve seul : des photos et des vidéos prises sans pause de plus de
6 heures (une nuit ne coupe pas un week-end en deux), au moins 5 fichiers, **d'un dossier ou d'un
téléphone à l'autre**. Les photos de la kermesse prises avec votre téléphone, celui de Julie et
l'appareil photo forment un seul événement, même si elles dorment dans trois dossiers.

Ce que `classify` ne sait pas, c'est **comment l'appeler**. Sans indice (un dossier que vous aviez
déjà nommé, une [règle](../sort/06-write-down-what-you-know.md)), il laisse ses fichiers où ils
sont. Nommez-le `Kermesse`, et `sort` met tous ses fichiers **dans un seul dossier**,
`2016/2016-07/Kermesse` :

```text
Avant, trois dossiers :
  C:\Photos\DCIM\100APPLE\IMG_4012.HEIC
  C:\Photos\Téléphone Julie\20160714_153201.jpg
  C:\Photos\Import 2016\DSC_0815.JPG

Après sort, un seul :
  C:\Photos\2016\2016-07\Kermesse\IMG_4012.HEIC
  C:\Photos\2016\2016-07\Kermesse\20160714_153201.jpg
  C:\Photos\2016\2016-07\Kermesse\DSC_0815.JPG
```

C'est donc bien une arborescence de dossiers sur votre disque : **chaque photo est déplacée dans
un seul dossier**, celui de son événement (sur le même disque, un simple renommage, et
[`undo`](undo.md) remet tout en place). Pour qu'une photo apparaisse aussi ailleurs (« tous les
Noëls », « Grand-mère »), sans copie : les [albums](../sort/12-albums.md).

- **Un seul champ, le dossier.** Tapez le nom de l'événement : `Kermesse` donne
  `2016/2016-07/Kermesse` ([la convention](../sort/04-classify.md#la-convention--année-mois-événement)).
  La ligne sous le champ dit, pendant que vous tapez, où vont les fichiers : « → 212 fichiers vont
  dans C:\Photos\2016\2016-07\Kermesse ». Le nom de l'événement (pour les albums) est le dernier
  dossier ; changez-le sous *Nom de l'événement* au besoin.
- **Tous ne demandent pas un nom.** Un événement dont les photos sont déjà dans un dossier nommé
  (`Vacances à la mer`) a une proposition marquée **sûre**. Regardez quand même où elle mène
  avant de la valider : seuls ses fichiers épars (le `DCIM` d'un téléphone, les fichiers à vérifier
  ou à trier) vont dans le dossier proposé.
- **Vos propres dossiers ne sont jamais aplatis.** Un événement qui réunit plusieurs dossiers que
  vous aviez nommés (un voyage : `Montenegro/Budva`, `Montenegro/Cetinje`…) les garde : accepté tel
  que proposé (avec <kbd>Entrée</kbd> ou <kbd>V</kbd>), chaque fichier reste dans son dossier ;
  avec un autre dossier (`Vacances au Monténégro`), celui-ci devient leur parent : `2019/Vacances
  au Monténégro/Budva`, `2019/Vacances au Monténégro/Cetinje`. La page le dit : « 3 fichiers
  gardent leur propre dossier (Budva, Cetinje) ».
- **Un événement que vous ne nommez pas** reste où il est, et dans la liste, jusqu'à ce que vous
  le nommiez : rien de non décidé ne bouge.

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Rien ne bouge sans votre GO, et le classeur n'est jamais modifié. Seul *Trier cet événement maintenant* déplace des fichiers, après *Vérifier, puis trier* : notés au journal, `undo` les remet. `mh review-sort` monte les photos accessibles en écriture, avec `/journal` ; montées en `:ro`, la page reste en lecture seule. |
| Il faut | `/reports` (l'exécution de `classify`), vos dossiers (pour montrer les photos), et `-p 127.0.0.1:8088:8088`. |
| Écrit | `sort-decisions.json`, à côté de `plan.json` dans le dossier de l'exécution de `classify`. |
| Annuler | `Suppr` dans la page reprend un choix ; le classeur décide alors à nouveau. |
| Avec `mh` | `mh review-sort` : le port est publié pour vous. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

Il compte les événements (*412 événements à décider : 260 avec une proposition sûre (un clic),
152 à regarder*), puis affiche l'adresse de la page : Ctrl+clic dessus. Ctrl+C, ou fermer son onglet, l'arrête ; la
fois suivante, il reprend.

## Les touches principales

La page : l'événement affiché à gauche (ses dates, ses dossiers, la proposition, ce que dit le
classeur), son dossier et l'endroit où vont ses fichiers dans la barre du haut, ses photos en
dessous. Les touches
restent en bas à gauche, sous ⌨ **Clavier** (les premières toujours visibles, les autres sous
*Plus de touches*), avec la ligne qui dit où chaque choix est enregistré.

| Touche | Rôle |
|---|---|
| `Entrée` | Aucune photo encadrée : enregistrer le dossier, puis passer à l'événement suivant encore à décider. |
| `N` / `P` | Événement suivant ou précédent, sans décider (les boutons ← → de la barre). `U` : événement suivant encore à décider. |
| `V` | Accepter d'un coup toutes les propositions sûres ; `Maj`+`Z` reprend ce lot. |
| `F` / `E` | Taper le dossier / changer le nom de l'événement ; `Échap` abandonne ce qui est tapé et non enregistré. |
| `Maj`+`S` | Laisser tout l'événement où il est. |
| clic, Ctrl, Maj, rectangle, `Ctrl`+`A`, `I` | Choisir des photos comme dans [`browse`](browse.md) ; puis `O` les envoie dans un autre dossier, `S` les laisse où elles sont. |
| `Suppr` | Reprendre le choix fait ici. |
| `Entrée` sur une photo, double clic | La grande vue. |

## Options

| Option | Rôle |
|---|---|
| `CLASSEUR` | Le classeur de `classify` ; celui du dernier `classify` par défaut. |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- **Trier cet événement maintenant** (<kbd>M</kbd>) déplace les fichiers de l'événement affiché,
  et eux seuls, comme `sort --event` : notés au journal, remis en place par `undo`. Il faut les
  photos montées sans `:ro` et un montage `/journal` ; sinon la page dit ce qui manque et rien ne
  bouge. L'événement s'affiche ensuite *trié*, et <kbd>U</kbd> le saute.
- **Vérifier, puis trier** : chaque photo dit où elle est et où elle va
  (*C:\Photos\2017\Août 2017\Mariage → C:\Photos\2017\Fêtes\Mariages\Mariage d'Hervé et
  Magda*), tel que `sort` la déplacera, recalculé pendant que vous tapez le dossier. *Trier cet
  événement maintenant* les liste d'abord par dossier (*14 → …*, à part les fichiers qui restent),
  puis **J'ai vérifié : trier ces N fichiers** est le GO ; le bouton attend pendant le calcul de
  la destination. Pour en laisser de côté, choisissez-les et appuyez sur <kbd>S</kbd> (laissées
  où elles sont). La réponse est relue sur le disque : *14 déplacés, 14 vérifiés à leur nouvelle
  place (passage …) : 'undo …' les remet*.
- **Règles** : *📌 Retenir comme règle* (<kbd>R</kbd>) écrit l'événement affiché comme une règle
  `date_range` de `config.toml` ; *📌 Vos règles* liste ce que chaque règle a décidé, supprime
  celles qui n'ont rien décidé et convertit une règle sur un nom de dossier en dates
  ([trier, étape 6](../sort/06-write-down-what-you-know.md#voir-ce-que-chaque-règle-a-fait)).
- **Le classeur n'est jamais modifié** (Excel l'a peut-être ouvert). Vous pouvez continuer à le
  modifier : chaque choix de la page retient ce que disait le classeur au moment où vous l'avez fait.
- **Un conflit n'est jamais réglé en silence** : si le classeur a été changé depuis, sur le même
  événement ou fichier, pour autre chose, `sort` refuse et liste les deux valeurs ; la page les
  montre en rouge.
- **Relancez `classify`** : vos choix de la page sont repris dans les cellules jaunes du nouveau
  classeur, comme vos modifications.

## Pour aller plus loin

- [Trier, étape 11 : nommer les événements dans votre navigateur](../sort/11-name-events-in-the-browser.md)
- Ensuite : [`sort`](sort.md).

## L'aide intégrée

<details>
<summary><code>review-sort --help</code></summary>

<!-- capture: help-review-sort.txt -->
```text
 Utilisation : media-hygiene review-sort [OPTIONS] [workbook]

 🔒 Lecture seule : ne modifie jamais vos photos. Nommer les événements de la
 proposition de classify un par un, dans votre navigateur.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  Le classeur de classify ; celui du dernier classify   │
│                        par défaut.                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut :  port dans config.toml,     │
│                                     8088.                                    │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
