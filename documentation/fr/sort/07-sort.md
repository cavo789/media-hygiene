# 7. Trier : appliquer le classeur

[Documentation](../README.md) › Trier, étape 7 · 🇬🇧 [English](../../en/sort/07-sort.md)

Vous avez revu la proposition et modifié le classeur ([étape 5](05-review-the-proposal.md)).
`sort` déplace maintenant les fichiers là où le classeur les met. Comme pour `clean`, chaque
déplacement est journalisé et `undo` remet tout en place.

## Le lancer

Enregistrez et fermez d'abord le classeur. Lancez ensuite `sort` : `mh` monte pour lui vos
dossiers **sans** `:ro`, avec le journal, la quarantaine et le dossier de rapports de `classify` :

```powershell
mh sort
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr sort
```

</details>

Sans argument, `sort` prend le classeur du dernier `classify`. Pour en appliquer un autre, donnez
son chemin : `sort "C:\Users\moi\Bureau\classify.xlsx"` (dans un dossier monté). Une copie
modifiée ailleurs convient : son `plan.json` est retrouvé dans `/reports` grâce à l'identifiant
que le classeur contient.

Avant de déplacer quoi que ce soit, `sort` dit ce qu'il a lu et ce qu'il va faire, puis demande :

<!-- capture: sort.txt|re:^─+ Tri|❓ -->
```text
───────────────────────────────────── Tri ──────────────────────────────────────
Classeur :
C:\Users\you\media-hygiene\reports\20261025-085021-classify\classify.xlsx
0 modification lue ; classeur enregistré le 25 octobre 2026 à 08:50.
Tri
┌────────────────────────────────┬────────┐
│ Fichiers à déplacer            │      8 │
│ Dans des dossiers              │      4 │
│ Taille                         │ 6,6 Mo │
│ Déjà à leur place              │     40 │
│ Restent où ils sont            │      0 │
│ Vers un dossier « à vérifier » │      0 │
│ Vers un dossier « à trier »    │      4 │
│ Dossiers sources supprimés     │      3 │
└────────────────────────────────┴────────┘
🛟 Chaque fichier est déplacé, jamais par-dessus un autre ni supprimé ;
l'exécution est journalisée : 'undo' remet tout en place.
❓ Déplacer 8 fichiers dans 4 dossiers ? [o/N] o
```

- *modifications lues* compte les cellules que vous avez remplies ; vérifiez la date : un classeur
  modifié mais **pas enregistré** montre son ancienne date, et `sort` prévient quand Excel ou
  LibreOffice l'a encore ouvert.
- Les choix faits dans [la page du navigateur](11-name-events-in-the-browser.md#où-vont-vos-choix),
  s'il y en a, sont appliqués par-dessus le classeur, et comptés sur une ligne à part.
- *Déjà à leur place* : des fichiers comptés, pas déplacés.
- *Dossiers sources supprimés* : les dossiers que le tri laisse vides (voir plus bas).

Ajoutez `--yes` pour ne pas être interrogé, ou mettez `confirm = false` dans la section `[sort]`
de `config.toml`.

## Ce qui est vérifié d'abord

Tout le classeur est comparé à son `plan.json`, **tout ou rien** : les noms des feuilles et leur
ordre, les lignes d'en-tête, les lignes (chaque identifiant exactement une fois) et chaque cellule
verrouillée. La première différence refuse tout le fichier, en nommant la cellule, la valeur
attendue et la valeur trouvée :

```text
❌ Fichiers!J2 : attendu « 2016/2016-07/Kermesse », trouvé « Ailleurs ».
💡 Annulez la modification dans Excel (Ctrl+Z), restaurez une copie du classeur,
ou relancez 'classify' : vos modifications sont reprises dans son nouveau
classeur.
```

Puis les cellules jaunes : un nom que Windows refuse (`CON`, `a:b`, un point final), un dossier
qui sort de la cible (`..`) ou un chemin plus long que ce que Windows accepte est refusé avec sa
cellule.

Les montages sont vérifiés comme pour `clean` : un journal est obligatoire, et les dossiers en
lecture seule sont refusés. La cible doit être un dossier monté (un dossier du conteneur lui-même
disparaîtrait avec lui) et ne peut pas se trouver dans un dossier protégé. Les fichiers des
dossiers protégés ne bougent jamais.

## Comment les fichiers bougent

- Chaque fichier est revérifié juste avant d'être déplacé : un fichier modifié ou supprimé depuis
  `classify` est passé et listé. Les fichiers absents du plan ne sont jamais touchés.
- Sur le même disque, un fichier est renommé (avec Docker Desktop sous Windows, il reçoit son
  nouveau nom puis perd l'ancien, ce qui revient au même) : instantané. D'un disque à l'autre (deux options
  `-v` sont deux disques, même sur le même lecteur), il est copié, comparé à l'original, et
  seulement ensuite supprimé.
- Un fichier existant n'est jamais écrasé : `IMG_1.jpg` devient `IMG_1 (2).jpg`.
- **Les compagnons voyagent ensemble** : une Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), un fichier
  RAW et son JPEG, et leurs [fichiers annexes](../reference-sidecars.md) vont dans le même
  dossier, sous le même nom. Leur dossier est le dossier final tapé sur l'une de leurs lignes de
  la feuille Fichiers ; sinon une modification d'événement ou de catégorie qui atteint l'un d'eux
  (celle de la photo d'abord, puis du RAW, puis de la vidéo : `sort` dit « IMG_1.MOV suit
  IMG_1.HEIC » quand leurs modifications donnaient des dossiers différents) ; sinon la
  proposition de la photo. Deux dossiers finaux différents tapés pour les mêmes compagnons (ou un
  dossier et *(rester où il est)*) font refuser le classeur par `sort` avant tout déplacement, en
  nommant les deux cellules : donnez-leur le même dossier, ou videz-les toutes sauf une.
- Le cache suit : le prochain `audit` ne relit pas les fichiers déplacés, et les noms donnés
  dans [`people`](../commands/people.md) restent sur leurs visages.

## Les dossiers laissés vides

Un dossier source laissé vide est supprimé, le plus profond d'abord, pour qu'un tri sur place ne
laisse pas derrière lui des centaines de dossiers `Juillet 2016` vides. Un dossier qui ne contient
plus que `Thumbs.db`, `desktop.ini` ou `.DS_Store` compte comme vide : ces fichiers partent
d'abord en quarantaine (la liste est `junk_files` dans `[sort]`). Un dossier qui contient autre
chose reste, et `sort` dit combien restent et pourquoi. Vos dossiers montés, les dossiers protégés
et exclus ne sont jamais supprimés. `--keep-empty-folders` les garde tous.

Trié, et toujours à court de place ? **⚖ Fichiers les plus lourds** dans
[les dossiers de `search`](../commands/search.md#parcourir-vos-dossiers) liste les fichiers les plus lourds de toute la photothèque, les
vidéos d'abord.

## Rien de perdu, preuve à l'appui

Les fichiers des dossiers sources et de la cible sont comptés avant les déplacements puis après :
les nombres et les tailles doivent être égaux. Chaque déplacement est vérifié (fichier à sa
cible, même taille, même SHA-256 quand il a changé de disque) :

<!-- capture: sort.txt|re:^Tri \d| -->
```text
Tri 20261025-085022
┌───────────────────────────┬────────┐
│ Fichiers traités          │      8 │
│ Taille                    │ 6,6 Mo │
│ Ignorés (laissés intacts) │      0 │
│ En échec                  │      0 │
│ Durée                     │    0 s │
└───────────────────────────┴────────┘
Dossiers sources supprimés : 3.
✅ Rien de perdu : 50 fichiers (18,3 Mo) avant et après ; 8 déplacements
vérifiés sur 8.
Manifeste :
C:\Users\you\media-hygiene\reports\20261025-085022-sort\manifest.json
💡 Vous changez d'avis ? 'media-hygiene undo 20261025-085022' remet tout en
place :
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "media-hygiene-cache:/cache" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr undo 20261025-085022
```

La preuve est écrite dans `/reports/<passage>-sort/manifest.json`.

## Relancer classify après un tri

Relancez `classify` après un tri (nouvelles photos, une règle changée) : les fichiers déjà triés
sont à leur place et ne sont pas proposés ailleurs. Avec la
[convention](04-classify.md#la-convention--année-mois-événement), l'arborescence le dit d'elle-même :
un fichier dans `année/année-mois/<nom>` est à sa place, quoi qui l'y ait mis (une règle, une
page, l'Explorateur), et un fichier posé directement dans son dossier `année/année-mois` aussi
(rien de spécial ce mois-là). Les suppositions et les fichiers que personne n'a décidés n'ont
jamais bougé : ils attendent là où ils étaient, jusqu'à ce que vous décidiez.

Avec les dispositions d'un `config.toml` plus ancien (dossiers *À vérifier* et *À trier*), les
**fichiers « à vérifier » que vous n'avez pas confirmés** restent dans leur dossier
`<année>/À vérifier/<catégorie>`, avec la raison `previous-guess`, et les **fichiers « à trier »**
d'un événement nommé d'après un dossier restent dans `<année>/À trier/<nom>` : ces noms sont ceux
de l'outil, donc une nouvelle exécution ne les déplace pas dans un sens puis dans l'autre.
Donnez-leur un dossier dans le classeur, ou sur une page, pour les déplacer.

## Arrêté en plein milieu

70 000 déplacements prennent du temps, et un portable se met en veille. `sort` déplace 4 fichiers
à la fois (`workers` dans la section `[clean]` de `config.toml`) ; Ctrl+C termine les fichiers en
cours, ferme le journal et dit ce qui a été fait. Relancez la même commande : les fichiers déjà
déplacés par ce classeur comptent comme faits, et le tri continue.

## Changer d'avis

Un tri s'annule comme un nettoyage ([undo](../clean/09-undo-history-purge.md)) : les fichiers
reviennent, les dossiers supprimés reviennent, les dossiers créés par le tri s'en vont.

<!-- capture: undo-sort.txt -->
```text
──────────────── Annulation de l'exécution sort 20261025-085022 ────────────────
🛟 Chaque fichier revient où il était, jamais par-dessus un autre ; ce qui ne
peut pas revenir intact est laissé tel quel, et signalé.

Annulation de l'exécution sort
20261025-085022
┌───────────────────────────┬────────┐
│ Fichiers traités          │      8 │
│ Taille                    │ 6,6 Mo │
│ Ignorés (laissés intacts) │      0 │
│ En échec                  │      0 │
│ Durée                     │    0 s │
└───────────────────────────┴────────┘
```

Un tri repris après une interruption forme plusieurs passages du même classeur, et une seule
opération : `undo` de l'un d'eux les annule tous, le plus récent d'abord, même si vous nommez un
passage antérieur (aucun déplacement plus récent ne reste par-dessus). Il les liste d'abord
(passage, début, fichiers déplacés) et demande une seule fois ; `--yes` saute la question, comme
pour `sort`. Un passage déjà annulé seul est laissé de côté, et c'est dit. `history` liste les
passages.

---

← [6. Écrire ce que vous savez](06-write-down-what-you-know.md) · [Documentation](../README.md) · Suivant : **[8. Nommer les sujets avec un modèle local](08-subjects-from-a-local-model.md)** →
