# 7. Trier : appliquer le classeur

[Documentation](../README.md) › Trier, étape 7 · 🇬🇧 [English](../../en/sort/07-sort.md)

Vous avez revu la proposition et modifié le classeur ([étape 5](05-review-the-proposal.md)).
`sort` déplace maintenant les fichiers là où le classeur les met. Comme pour `clean`, chaque
déplacement est journalisé et `undo` remet tout en place.

## Le lancer

Enregistrez et fermez d'abord le classeur. Montez ensuite vos dossiers **sans** `:ro`, avec le
journal, la quarantaine et le dossier de rapports de `classify` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr sort
```

Sans argument, `sort` prend le classeur du dernier `classify`. Pour en appliquer un autre, donnez
son chemin : `sort "C:\Users\moi\Bureau\classify.xlsx"` (dans un dossier monté). Une copie
modifiée ailleurs convient : son `plan.json` est retrouvé dans `/reports` grâce à l'identifiant
que le classeur contient.

Avant de déplacer quoi que ce soit, `sort` dit ce qu'il a lu et ce qu'il va faire, puis demande :

<!-- capture: sort.txt|re:^─+ Tri|❓ -->
```text
───────────────────────────────────── Tri ──────────────────────────────────────
Classeur : /reports/20260930-182311-classify/classify.xlsx
0 modification lue ; classeur enregistré le 30 septembre 2026 à 18:23.
Tri
┌────────────────────────────────┬────────┐
│ Fichiers à déplacer            │      4 │
│ Dans des dossiers              │      2 │
│ Taille                         │ 5,9 Mo │
│ Déjà à leur place              │     40 │
│ Restent où ils sont            │      0 │
│ Vers un dossier « à vérifier » │      0 │
│ Vers un dossier « à trier »    │      1 │
│ Dossiers sources supprimés     │      2 │
└────────────────────────────────┴────────┘
❓ Déplacer 4 fichiers dans 2 dossiers ? [o/N] o
```

- *modifications lues* compte les cellules que vous avez remplies ; vérifiez la date : un classeur
  modifié mais **pas enregistré** montre son ancienne date, et `sort` prévient quand Excel ou
  LibreOffice l'a encore ouvert.
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
❌ Fichiers!J2 : attendu « 2016/À trier/2016-07-14 », trouvé « Ailleurs ».
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
- Sur le même disque, un fichier est renommé : instantané. D'un disque à l'autre (deux options
  `-v` sont deux disques, même sur le même lecteur), il est copié, comparé à l'original, et
  seulement ensuite supprimé.
- Un fichier existant n'est jamais écrasé : `IMG_1.jpg` devient `IMG_1 (2).jpg`.
- **Les compagnons voyagent ensemble** : une Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), un fichier
  RAW et son JPEG, et leurs [fichiers annexes](../reference-sidecars.md) vont dans le même
  dossier, sous le même nom.
- Le cache suit : le prochain `audit` ne relit pas les fichiers déplacés.

## Les dossiers laissés vides

Un dossier source laissé vide est supprimé, le plus profond d'abord, pour qu'un tri sur place ne
laisse pas derrière lui des centaines de dossiers `Juillet 2016` vides. Un dossier qui ne contient
plus que `Thumbs.db`, `desktop.ini` ou `.DS_Store` compte comme vide : ces fichiers partent
d'abord en quarantaine (la liste est `junk_files` dans `[sort]`). Un dossier qui contient autre
chose reste, et `sort` dit combien restent et pourquoi. Vos dossiers montés, les dossiers protégés
et exclus ne sont jamais supprimés. `--keep-empty-folders` les garde tous.

## Rien de perdu, preuve à l'appui

Les fichiers des dossiers sources et de la cible sont comptés avant les déplacements puis après :
les nombres et les tailles doivent être égaux. Chaque déplacement est vérifié (fichier à sa
cible, même taille, même SHA-256 quand il a changé de disque) :

<!-- capture: sort.txt|re:^Tri \d| -->
```text
Tri 20260930-182313
┌───────────────────────────┬────────┐
│ Fichiers traités          │      4 │
│ Taille                    │ 5,9 Mo │
│ Ignorés (laissés intacts) │      0 │
│ En échec                  │      0 │
│ Durée                     │    0 s │
└───────────────────────────┴────────┘
Dossiers sources supprimés : 2.
✅ Rien de perdu : 46 fichiers (17,6 Mo) avant et après ; 4 déplacements
vérifiés sur 4.
Manifeste : /reports/20260930-182313-sort/manifest.json
💡 Vous changez d'avis ? 'media-hygiene undo 20260930-182313' remet tout en
place.
```

La preuve est écrite dans `/reports/<passage>-sort/manifest.json`.

## Arrêté en plein milieu

70 000 déplacements prennent du temps, et un portable se met en veille. Ctrl+C termine le fichier
en cours, ferme le journal et dit ce qui a été fait. Relancez la même commande : les fichiers déjà
déplacés par ce classeur comptent comme faits, et le tri continue.

## Changer d'avis

Un tri s'annule comme un nettoyage ([undo](../clean/09-undo-history-purge.md)) : les fichiers
reviennent, les dossiers supprimés reviennent, les dossiers créés par le tri s'en vont.

<!-- capture: undo-sort.txt -->
```text
──────────────── Annulation de l'exécution sort 20260930-182313 ────────────────
Annulation de l'exécution sort
20260930-182313
┌───────────────────────────┬────────┐
│ Fichiers traités          │      4 │
│ Taille                    │ 5,9 Mo │
│ Ignorés (laissés intacts) │      0 │
│ En échec                  │      0 │
│ Durée                     │    0 s │
└───────────────────────────┴────────┘
```

Un tri repris après une interruption forme plusieurs passages : annulez-les un par un, le plus
récent d'abord (`history` les liste).

---

← [6. Écrire ce que vous savez](06-write-down-what-you-know.md) · [Documentation](../README.md)
