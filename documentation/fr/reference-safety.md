# Comment vos photos restent en sécurité

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-safety.md)

Avant de supprimer des photos de famille, tout le monde se pose la même question : *est-ce
vraiment, vraiment des doublons ?* Cette page explique ce que l'outil appelle un doublon, ce qu'il
vérifie avant chaque action, et comment le vérifier vous-même.

## Qu'est-ce qu'un doublon ?

Uniquement des fichiers **identiques octet par octet**. L'outil compare d'abord les tailles, puis
une empreinte SHA-256 des premiers et derniers 64 Ko, puis une empreinte SHA-256 de tout le
contenu. En pratique, deux fichiers différents n'ont jamais le même SHA-256 : c'est bien moins
probable qu'une erreur de disque.

- **Le nom et la date ne comptent pas.** `IMG_1234.jpg` et `Marie et Paul.jpg` avec les mêmes
  octets sont des doublons. Deux `IMG_0001.jpg` au contenu différent n'en sont pas.
- **Se ressembler ne suffit pas.** Une copie redimensionnée, recompressée, pivotée ou dont les
  métadonnées ont changé est un autre fichier. L'audit la liste comme
  [quasi-doublon](clean/11-near-duplicates.md), mais `clean` n'y touche pas, sauf si vous le demandez
  avec `--tier near`, et alors il la déplace seulement en quarantaine.
- **Seuls les photos, fichiers RAW et vidéos** sont analysés, reconnus par leur extension. Les
  autres fichiers seulement si vous [les demandez](clean/06-file-types.md#autres-types-de-fichiers) avec
  `--ext`, et leurs copies sont alors déplacées en quarantaine, jamais supprimées.

## Chaque garantie, étape par étape

| Étape | Garantie |
|---|---|
| `audit` | Lecture seule : montez vos dossiers avec `:ro` et Docker lui-même interdit toute écriture. |
| Copie gardée | Choix déterministe : les [règles de choix](clean/05-choose-the-kept-copy.md#comment-loutil-choisit) donnent toujours le même résultat, et le rapport indique la règle qui a décidé. Vos [décisions dans le rapport](clean/12-decide-pair-by-pair.md) passent par-dessus. |
| Un fichier, deux chemins | Un dossier monté deux fois est refusé ; un fichier accessible par deux chemins (lien physique) n'est analysé qu'une fois, jamais comme doublon de lui-même. |
| Avant chaque suppression | La copie gardée doit encore exister, être un autre fichier et être identique octet par octet ; sinon, le fichier est ignoré. |
| Chaque action | Écrite dans le journal *avant* (`pending`) et *après* (`done`) : une interruption ne fait jamais perdre le fil. |
| Doublons | Réellement supprimés (l'espace est libéré tout de suite) ; `undo` les reconstruit depuis la copie gardée, date comprise, même d'un disque à l'autre. |
| Fichiers illisibles | Déplacés en quarantaine, jamais supprimés directement ; `purge` les supprime définitivement quand vous êtes sûr·e. |
| Quasi-doublons | Photos et [vidéos réencodées](clean/11-near-duplicates.md#les-vidéos-aussi--les-copies-réencodées). Jamais touchés par défaut. Avec `--tier near`, déplacés en quarantaine (jamais supprimés) après vérification : la photo ou la vidéo gardée existe toujours, la copie est bien le fichier vu par l'audit. `undo` les remet en place. |
| Rafales | Jamais touchées par défaut. Les photos que vous [écartez avec `review`](clean/10-review-bursts.md) sont déplacées en quarantaine (jamais supprimées) par `clean --decisions`, après vérification : une photo gardée est toujours là, la photo écartée est bien le fichier montré par le tri. `undo` les remet en place. |
| Autres types de fichiers | Seulement s'ils sont demandés avec `--ext` : leurs copies sont déplacées en quarantaine (jamais supprimées), et les dossiers de logiciels (`.git`, `node_modules`, `AppData`, …) sont ignorés. |
| Fichiers compagnons | Jamais touchés à côté de leur photo. Un orphelin est déplacé en quarantaine (jamais supprimé) après vérification : inchangé depuis l'audit, et aucun fichier du même nom à côté de lui. `undo` le remet en place. |
| Albums | [`album`](sort/11-albums.md) ne fait qu'ajouter des liens physiques (des seconds noms) dans son propre dossier, journalisés ; toutes les analyses ignorent ce dossier. `undo` ne supprime un lien que tant que la photo garde un autre nom. |
| Dossiers protégés | Jamais modifiés, quoi qu'il arrive. |
| Chaque groupe | Garde toujours au moins une copie. |

## Vérifiez vous-même

Le [rapport HTML](clean/04-html-report.md) est fait pour ça :

- Les **paires de dossiers** viennent en premier. Un badge signale un dossier qui est
  *entièrement une copie* d'un autre, et chaque paire a sa page qui liste toutes ses copies.
- Un **échantillon aléatoire** de groupes de photos est affiché avec des aperçus.
- **Vérifiez vous-même**, sur chaque groupe, donne une commande PowerShell `Get-FileHash`.
  Collez-la : chaque copie affiche le même SHA-256, calculé par Windows et non par media-hygiene.
- **`plan.csv`** liste chaque fichier du plan avec son SHA-256, prêt pour Excel.
- **[Un second avis](clean/13-second-opinion.md)** : Czkawka, un outil indépendant, compare ses
  résultats à ceux de media-hygiene, groupe par groupe.

## Recommandations

- **Commencez par un audit, puis lisez les paires de dossiers.** Ouvrez quelques paires et
  vérifiez vous-même quelques groupes.
- **Vérifiez quelle copie reste.** Le fichier gardé conserve son nom et son dossier ; le nom d'une
  copie supprimée est perdu. Ce n'est pas celle que vous voulez ?
  [Choisissez-la](clean/05-choose-the-kept-copy.md), puis relancez l'audit.
- **Sauvegardez vos photos avant le premier nettoyage**, par exemple sur un disque externe :
  l'outil garde un exemplaire de chaque photo, pas deux.
- **Mettez en pause la synchronisation cloud** (OneDrive, Google Drive, Dropbox, iCloud) pendant
  le nettoyage. Sinon, les suppressions sont recopiées dans le cloud et sur vos autres appareils.
- **Gardez le dossier du journal** : `undo` en a besoin. Ne lancez `purge` que si vous êtes sûr·e.
- Lisez aussi la [page de dépannage](reference-troubleshooting.md) : une vraie sauvegarde doit
  être exclue, et chaque dossier ne doit être monté qu'une fois.
