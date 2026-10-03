# Comment vos photos restent en sécurité

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-safety.md)

Avant de toucher à des photos de famille, tout le monde se pose la même question : *puis-je en
perdre une ?* Cette page y répond simplement : quelles commandes ne touchent jamais à vos photos,
lesquelles agissent et comment elles restent réversibles, et la seule commande qui efface.

## Notre promesse : ces commandes ne modifient jamais vos photos

Nous le garantissons : quand vous lancez l'une de ces commandes, vos photos et vidéos ne sont
**jamais modifiées, déplacées ni supprimées**.

| Commande | Ce qu'elle écrit, et où |
|---|---|
| `audit`, `crosscheck` | Le rapport HTML (`/reports`) et le cache (`/cache`). |
| `classify` | La proposition et son classeur (`/reports`), le cache. |
| `review`, `review-sort` | Vos choix, dans un petit fichier `.json` à côté du rapport (`/reports`). |
| `places` | Les lieux que vous nommez, dans `config.toml` (`/config`). |
| `inventory` | Le classeur (`/reports`), lu dans le cache seul. |
| `history`, `reports`, `config` | Rien dans vos dossiers (`reports --prune` ne supprime que d'anciens rapports). |

Toutes fonctionnent avec vos dossiers de photos montés **en lecture seule** : ajoutez `:ro` à
leur `-v` (`-v "C:\Photos:/data/c/Photos:ro"`). Ce n'est alors plus seulement notre promesse : le
système lui-même refuse toute modification. Leur `--help` commence par *Lecture seule*, et celles qui
lisent vos photos le disent avec 🔒 en démarrant.

## Rien n'est effacé tant que vous ne lancez pas `purge`

Les commandes qui agissent sur vos fichiers n'effacent jamais rien, et chacune peut être annulée :

- **`sort`** déplace les fichiers là où le classeur le dit. Sur un même disque, un déplacement
  est un simple renommage : rien n'est copié, aucune place n'est prise.
- **`album`** ne fait qu'ajouter des seconds noms (liens physiques) ; aucune photo n'est copiée,
  déplacée ni supprimée.
- **`clean`** déplace les copies en trop en quarantaine, chacune comparée octet par octet avec la
  copie gardée juste avant. Leur place est libérée par `purge`, une fois que vous avez vérifié.
- **`undo`** remet les fichiers d'une exécution là où ils étaient.

**`purge` est la seule commande qui efface** : elle vide la quarantaine, pour de bon, après vous
avoir dit combien de fichiers et quelle place, et vous l'avoir demandé. D'ici là, `undo` remet
tout en place.

Besoin de la place tout de suite ? `clean --delete` supprime les copies en trop au lieu de les
déplacer, après la même comparaison octet par octet. La copie gardée reste, donc rien n'est
perdu : `undo` reconstruit chaque copie supprimée à partir d'elle. Les fichiers vides (0 octet)
sont supprimés aussi : ils ne contiennent rien.

## Les filets de sécurité, toujours actifs, sans coût en place

- **Les commandes en lecture seule**, et `:ro`, imposé par le système.
- **Jamais par-dessus un autre fichier.** Un déplacement, une copie ou une annulation ne remplace
  jamais un fichier : si un fichier est apparu à la destination entre-temps, l'action est refusée,
  et les deux fichiers restent tels quels.
- **Vérifié deux fois.** Une copie est comparée à la copie gardée juste avant d'être mise de
  côté ; un déplacement d'un disque à l'autre est copié, prouvé identique (SHA-256), et seulement
  alors retiré de son ancien emplacement.
- **Le journal.** Chaque action est notée *avant* et *après* : une interruption ne fait jamais
  perdre le fil, et `undo` annule n'importe quelle exécution.
- **La quarantaine.** Ce que `clean` met de côté y attend, intact, jusqu'à votre `purge`.
- **Les dossiers de l'outil restent hors de vos photos.** Un dossier de quarantaine, de journal,
  de cache ou de rapports placé dans un dossier de photos (ou autour) est refusé, avec la façon
  de le monter autrement.

## Les bonnes habitudes

- **Commencez petit.** Analysez un sous-dossier, regardez le rapport, puis élargissez.
- **Lisez le rapport avant `clean`** : les paires de dossiers d'abord, puis quelques groupes.
- **Mettez en pause la synchronisation cloud** (OneDrive, Google Drive, Dropbox, iCloud) pendant
  un nettoyage ou un tri : sinon chaque changement est recopié dans le cloud et sur vos autres
  appareils.
- **Gardez le dossier du journal** : `undo` en a besoin. Ne lancez `purge` qu'après avoir vérifié.

Si vous le pouvez, une **sauvegarde sur un disque externe** est le filet de plus contre ce
qu'aucun logiciel ne peut empêcher : un disque qui lâche, une erreur faite en dehors de l'outil.
Elle est bienvenue, pas obligatoire.

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
| `audit` et les autres [commandes en lecture seule](#notre-promesse--ces-commandes-ne-modifient-jamais-vos-photos) | Montez vos dossiers avec `:ro` et le système lui-même interdit toute écriture. |
| Copie gardée | Choix déterministe : les [règles de choix](clean/05-choose-the-kept-copy.md#comment-loutil-choisit) donnent toujours le même résultat, et le rapport indique la règle qui a décidé. Vos [décisions dans le rapport](clean/12-decide-pair-by-pair.md) passent par-dessus. |
| Un fichier, deux chemins | Un dossier monté deux fois est refusé ; un fichier accessible par deux chemins (lien physique) n'est analysé qu'une fois, jamais comme doublon de lui-même. |
| Avant de mettre chaque copie de côté | La copie gardée doit encore exister, être un autre fichier (pas le même fichier vu par deux chemins) et être identique octet par octet ; sinon, la copie est ignorée. |
| Chaque action | Écrite dans le journal *avant* (`pending`) et *après* (`done`) : une interruption ne fait jamais perdre le fil. |
| Doublons | Déplacés en quarantaine ; `undo` les remet en place, `purge` libère leur place. Avec `clean --delete`, supprimés tout de suite ; `undo` les reconstruit depuis la copie gardée, date comprise, même d'un disque à l'autre. |
| Fichiers illisibles | Déplacés en quarantaine, jamais supprimés directement ; `purge` les supprime définitivement quand vous êtes sûr·e. |
| Déplacements | Jamais par-dessus un autre fichier : un renommage atomique qui refuse un nom déjà pris, ou, d'un disque à l'autre, une copie dans un nouveau fichier, prouvée identique, avant que l'original ne parte. |
| Quasi-doublons | Photos et [vidéos réencodées](clean/11-near-duplicates.md#les-vidéos-aussi--les-copies-réencodées). Jamais touchés par défaut. Avec `--tier near`, déplacés en quarantaine (jamais supprimés) après vérification : la photo ou la vidéo gardée existe toujours, la copie est bien le fichier vu par l'audit. `undo` les remet en place. |
| Rafales | Jamais touchées par défaut. Les photos que vous [écartez avec `review`](clean/10-review-bursts.md) sont déplacées en quarantaine (jamais supprimées) par `clean --decisions`, après vérification : une photo gardée est toujours là, la photo écartée est bien le fichier montré par le tri. `undo` les remet en place. |
| Autres types de fichiers | Seulement s'ils sont demandés avec `--ext` : leurs copies sont déplacées en quarantaine (jamais supprimées), et les dossiers de logiciels (`.git`, `node_modules`, `AppData`, …) sont ignorés. |
| Fichiers compagnons | Jamais touchés à côté de leur photo. Un orphelin est déplacé en quarantaine (jamais supprimé) après vérification : inchangé depuis l'audit, et aucun fichier du même nom à côté de lui. `undo` le remet en place. |
| Albums | [`album`](sort/11-albums.md) ne fait qu'ajouter des liens physiques (des seconds noms) dans son propre dossier, journalisés, jamais par-dessus un fichier ; toutes les analyses ignorent ce dossier. `undo` ne retire un nom de l'album que si l'original qu'il désigne est toujours là et est bien le même fichier ; sinon le nom reste, et `undo` dit pourquoi. |
| Fichiers inutiles de `sort` | Seuls les noms de `[sort] junk_files` (`Thumbs.db`, …) vont en quarantaine avec un dossier vidé ; un nom de photo, de vidéo ou de fichier compagnon y est refusé. |
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

- **Vérifiez quelle copie reste.** Le fichier gardé conserve son nom et son dossier ; le nom d'une
  copie mise de côté est perdu une fois la quarantaine vidée. Ce n'est pas celle que vous voulez ?
  [Choisissez-la](clean/05-choose-the-kept-copy.md), puis relancez l'audit.
- Lisez aussi la [page de dépannage](reference-troubleshooting.md) : une vraie sauvegarde doit
  être exclue, et chaque dossier ne doit être monté qu'une fois.
