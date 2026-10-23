# Commandes et options

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-commands.md)

Chaque commande, chaque option. Le [guide](README.md#pour-commencer) les présente une à une ;
cette page les rassemble. Les commandes dont l'aide commence par *Lecture seule* ne modifient jamais vos photos
([comment vos photos restent en sécurité](reference-safety.md)).

## Quelle commande ?

| Je veux… | Commande |
|---|---|
| savoir, sans aucun risque, combien de copies contiennent mes dossiers et quelle place elles prennent | [`audit`](commands/audit.md) |
| savoir en une seconde où j'en suis après quelques jours, et la prochaine étape | [`status`](commands/status.md) |
| ne retenir aucune commande : voir chaque étape, lancer la prochaine avec Entrée | [`menu`](commands/menu.md) (`mh menu` ; `mh` seul : la [page d'accueil](commands/home.md)) |
| cliquer plutôt que taper : où j'en suis, l'étape suivante en bouton, mes rapports, l'audit lancé dans la page | [`home`](commands/home.md) |
| libérer la place que prennent mes photos en double, en sécurité : mises de côté, jamais effacées | [`clean`](commands/clean.md) |
| ne garder que les meilleures photos de mes rafales, trancher les quasi-doublons | [`review`](commands/review.md), puis `clean --decisions` |
| voir ce que chaque exécution a fait | [`history`](commands/history.md) |
| remettre chaque fichier d'une exécution exactement où il était | [`undo`](commands/undo.md) |
| récupérer la place pour de bon, une fois la quarantaine vérifiée | [`purge`](commands/purge.md) |
| être sûr des doublons avant de supprimer des photos de famille | [`crosscheck`](commands/crosscheck.md) |
| retrouver tous les rapports, supprimer les anciens | [`reports`](commands/reports.md) |
| obtenir une arborescence bien rangée, par année, événement, lieu ou personne, et la corriger d'abord | [`classify`](commands/classify.md) |
| nommer mes événements en regardant leurs photos | [`review-sort`](commands/review-sort.md) |
| déplacer mes photos dans l'arborescence approuvée, de façon annulable | [`sort`](commands/sort.md) |
| faire d'un album un dossier de l'Explorateur, sans copie | [`album`](commands/album.md) |
| nommer mes lieux sur une carte, pour trier par lieu et par voyage | [`places`](commands/places.md), puis `classify` |
| retrouver les photos de quelqu'un par son nom, les ranger selon qui y figure | [`people`](commands/people.md), puis `search` ou `classify` |
| donner à mes photos et vidéos des mots pour les retrouver | [`tags`](commands/tags.md) |
| retrouver une photo par un mot, un lieu, une année, une personne | [`search`](commands/search.md) |
| parcourir mes dossiers et retirer des photos, sans l'Explorateur, de façon annulable | [`browse`](commands/browse.md), puis `clean --decisions` |
| montrer les photos des vacances sur la télé, en choisissant la suivante depuis mon téléphone | [`slideshow`](commands/slideshow.md) |
| envoyer un album par mail ou sur un réseau social, réduit et sans la position GPS | [`share`](commands/share.md) |
| voir mes mots dans digiKam, darktable, Lightroom ou Immich | [`xmp`](commands/xmp.md) |
| récupérer les photos que seul mon NAS a encore, pas celles que j'ai supprimées | [`import`](commands/import.md) |
| récupérer la place des vidéos de mes anciens appareils, l'image gardée | [`shrink`](commands/shrink.md) |
| sauvegarder mes photos sur mon NAS, seulement ce qui lui manque | [`backup`](commands/backup.md) |
| répondre à mes propres questions sur mes photos avec Excel | [`inventory`](commands/inventory.md) |
| taper `mh audit` au lieu d'un long `docker run` | [`launcher`](commands/launcher.md) |
| vérifier chaque réglage et chaque dossier avant que l'outil agisse | [`config`](commands/config.md) |

## Commandes

Chaque commande a sa propre page. Elle commence par **En bref** : ce que la commande vous apporte,
quand l'utiliser et la commande à essayer ; puis les dossiers dont elle a besoin, ses options, des
exemples et son `--help`.

**🔒 Analyser : lecture seule, ne modifie jamais vos photos**

| Commande | Rôle | Guide |
|---|---|---|
| [`audit`](commands/audit.md) | Trouve les doublons exacts et les fichiers cassés. N'écrit jamais dans vos dossiers. | [1](start/01-first-audit.md) |
| [`status`](commands/status.md) | Où en suis-je ? Le dernier audit, la quarantaine, les exécutions encore annulables, les tris pas appliqués, la dernière proposition pas triée ; puis une étape suivante en commande complète. Ne lit que les dossiers de l'outil, sans analyse. | [Nettoyer, 9](clean/09-undo-history-purge.md#où-en-suis-je--status) |
| [`menu`](commands/menu.md) | Ce que montre `mh menu` dans le terminal : chaque étape des trois guides avec sa commande `mh` complète, celle que donnerait `status` proposée ; Entrée la lance par `mh`, un numéro en lance une autre. Ne lit que les dossiers de l'outil, sans analyse. | [Nettoyer en bref](clean/quick-guide.md) |
| [`home`](commands/home.md) | La page d'accueil dans votre navigateur : ce que dit `status`, l'étape suivante en gros bouton, chaque étape des guides numérotée comme dans `mh menu`, les rapports et quelques aperçus ; lance l'audit dans la page, sa progression affichée. Le bouton d'une étape la confie à `mh` dans le terminal. N'écrit jamais dans vos dossiers. | [Commandes](commands/home.md) |
| [`review`](commands/review.md) | Analyse, puis trie les rafales dans votre navigateur, une à la fois, au clavier ; `--near` : décider les quasi-doublons groupe par groupe. N'écrit jamais dans vos dossiers. | [Nettoyer, 10](clean/10-review-bursts.md), [11](clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near) |
| [`history`](commands/history.md) | Liste les exécutions : leur commande, fichiers supprimés, espace libéré, quarantaine, restaurations. | [Nettoyer, 9](clean/09-undo-history-purge.md) |
| [`reports`](commands/reports.md) | Liste les rapports et régénère `index.html` ; `--prune N` garde les N plus récents. | [Nettoyer, 4](clean/04-html-report.md) |
| [`crosscheck`](commands/crosscheck.md) | Refait l'audit, lance Czkawka, un détecteur de doublons indépendant, puis compare les deux. | [Nettoyer, 13](clean/13-second-opinion.md) |
| [`config`](commands/config.md) | Affiche chaque réglage, son origine, et l'état de chaque point de montage ; crée un `config.toml` commenté la première fois. | [Nettoyer, 7](clean/07-configuration-file.md) |
| [`launcher`](commands/launcher.md) | Affiche le script de `mh`, une commande courte qui retient les dossiers de cette exécution : `mh audit`, `mh clean`… avec les bons montages pour chaque commande. À rediriger vers un fichier (`> mh.ps1`), sans `-it`. | [3](start/01-first-audit.md#écrire-mh-une-fois) |
| [`classify`](commands/classify.md) | Propose où ranger chaque photo et vidéo : année, événement, catégorie. N'écrit jamais dans vos dossiers ; écrit un classeur à modifier et un rapport dans `/reports`. | [Trier, 4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md), [8](sort/08-subjects-from-a-local-model.md), [10](sort/10-sort-by-person.md) |
| [`review-sort`](commands/review-sort.md) | Montre les événements de la proposition de `classify` un par un dans votre navigateur, avec leurs photos, et les nomme au clavier ; enregistré à côté de `plan.json`, appliqué par `sort`. N'écrit jamais dans vos dossiers ni dans le classeur. | [Trier, 11](sort/11-name-events-in-the-browser.md) |
| [`places`](commands/places.md) | Montre sur une carte dans votre navigateur où les photos ont été prises, et nomme vos lieux ; enregistrés dans `config.toml`. N'écrit jamais dans vos dossiers. | [Trier, 9](sort/09-places-from-gps.md) |
| [`inventory`](commands/inventory.md) | Exporte chaque photo et vidéo avec ce que les audits en ont appris vers un classeur Excel (ou un fichier CSV), depuis le cache seul : aucun fichier n'est lu. | [Référence](reference-inventory.md) |
| [`tags`](commands/tags.md) | Donne à chaque photo et vidéo des mots pour la retrouver : les mots parlants de ses dossiers et de son nom de fichier, sa date (année, mois, saison, fêtes), son lieu, et ce qu'y voit un modèle de vision local (facultatif ; une vidéo par l'image du milieu). Gardés dans le cache, jamais écrits dans les photos. | [Référence](reference-tags.md) |
| [`search`](commands/search.md) | Retrouve des photos par leurs mots (ceux de `tags`) et les noms donnés dans `people` (`person:"…"`) dans votre navigateur, avec filtres et aperçus ; avec des mots, affiche les premiers résultats en tableau. Les photos choisies peuvent être mises de côté pour `clean --decisions`. N'écrit jamais dans vos dossiers. | [Référence](reference-tags.md#retrouver-une-photo-par-ses-mots--search) |
| [`browse`](commands/browse.md) | Parcourt vos dossiers dans votre navigateur, comme dans l'Explorateur : l'arborescence avec ses nombres, les photos et vidéos d'un dossier, en grand avec ←/→ ; met de côté celles choisies pour `clean --decisions`. N'écrit jamais dans vos dossiers. | [Retrouver en bref](find/quick-guide.md) |
| [`slideshow`](commands/slideshow.md) | Montre les photos d'un dossier, d'une recherche ou les fichiers mis de côté sur la télé (son navigateur, ou celui d'un Chromecast), le téléphone comme télécommande : suivante, précédente, une photo touchée, lecture et pause, « ne pas montrer ». Avec `mh slideshow --lan`, pour le réseau de la maison seulement, la télé appairée par un code qu'elle affiche. N'écrit jamais dans vos dossiers. | [Commandes](commands/slideshow.md) |
| [`share`](commands/share.md) | Prépare un album pour l'envoyer : une copie de chaque photo, redressée, son grand côté à 2048 pixels, sans sa position GPS (`--keep-gps` la garde), dans un dossier au nom de l'album et son zip, dans `media-hygiene\Shares` ; les vidéos sont laissées de côté et comptées. N'écrit jamais dans vos dossiers. | [Commandes](commands/share.md) |
| [`people`](commands/people.md) | Trouve les visages des photos, regroupe ceux qui se ressemblent, et vous les fait nommer dans votre navigateur (les noms vont dans `config.toml` ; `search` les retrouve). Les visages restent dans le cache, jamais envoyés nulle part ; `--forget` les supprime tous. N'écrit jamais dans vos dossiers. | [Référence](reference-people.md), [Trier, 10](sort/10-sort-by-person.md) |

**Agir : déplace, écrit ou supprime des fichiers** (journalisé, annulable)

| Commande | Rôle | Guide |
|---|---|---|
| [`clean`](commands/clean.md) | Audite, demande confirmation, puis déplace en quarantaine les copies en double, les fichiers illisibles et les fichiers compagnons orphelins, et supprime les fichiers vides ; `--delete` supprime les copies à la place. | [Nettoyer, 8](clean/08-clean.md) |
| [`undo [EXÉCUTION]`](commands/undo.md) | Restaure chaque fichier d'une exécution (la plus récente par défaut) ; pour un album, supprime ses liens ; pour `xmp`, ses fichiers compagnons. | [Nettoyer, 9](clean/09-undo-history-purge.md) |
| [`purge [EXÉCUTION]`](commands/purge.md) | Efface pour de bon la quarantaine d'une exécution (de toutes par défaut) : la seule commande qui efface du contenu, avec `clean --delete`. | [Nettoyer, 9](clean/09-undo-history-purge.md) |
| [`sort [CLASSEUR]`](commands/sort.md) | Vérifie le classeur modifié de `classify`, demande confirmation, puis déplace les fichiers là où il le dit ; journalisé, annulable, prouvé. | [Trier, 7](sort/07-sort.md) |
| [`album NOM`](commands/album.md) | Crée le dossier d'un album (enregistré dans `search`, `browse` ou la revue des rafales) en liens physiques : rien de copié ni de déplacé, aucune place prise. `--category`, `--event`, `--rule`, `--rating` rassemblent plutôt une sélection du plan de `classify`. Montre l'album ; `--apply` crée les liens. | [Trier, 12](sort/12-albums.md) |
| [`xmp`](commands/xmp.md) | Écrit les mots de `tags` dans des fichiers compagnons `.xmp` à côté des photos, pour digiKam, darktable, Lightroom ou Immich ; jamais dans une photo. Montre ce qu'il écrirait ; `--apply` écrit. | [Référence](reference-tags.md#emporter-les-mots-avec-les-photos--xmp) |
| [`import`](commands/import.md) | Copie dans vos photos ce qu'une sauvegarde (un NAS) est seule à contenir, jamais ce que vous avez mis de côté ou supprimé avant ; les quasi-copies listées à part ; chaque copie prouvée ; la sauvegarde seulement lue. | [Commandes](commands/import.md) |
| [`shrink`](commands/shrink.md) | Liste les vidéos lourdes qui gagnent à être allégées (anciens appareils, MJPEG), avec la place que chacune libérerait ; `--apply` les réencode en H.264, chacune vérifiée (durée, son, date, lieu), l'original en quarantaine. | [Commandes](commands/shrink.md) |
| [`backup`](commands/backup.md) | Windows seulement (`mh backup`) : copier vos dossiers de photos dans un dossier rien qu'à eux sur le NAS, seulement ce qui lui manque ; une photo déplacée y est renommée, une suppression par erreur n'y est jamais reportée ; annuler avec `--undo`. | [Commandes](commands/backup.md) |

## Options

Les options globales se placent **avant** la commande : `cavo789/media-hygiene --locale fr audit`.
Les autres se placent **après** : `cavo789/media-hygiene audit --prefer "C:\Photos\Famille"`.

| Option | Commandes | Rôle |
|---|---|---|
| `--locale en\|fr` | globale | Langue de l'interface (anglais par défaut) ; les nombres et tailles la suivent : `67,947` et `44.3 GB`, ou `67.947` et `44,3 Go`. |
| `--verbosity error\|warning\|info\|verbose\|debug` | globale | Niveau de détail des journaux. `verbose` : `info`, plus toutes les astuces d'une commande (pas seulement les deux plus utiles) et l'inventaire après un audit. |
| `--color auto\|always\|never` | globale | Couleurs ANSI (`NO_COLOR` est respecté). |
| `--version` | globale | Affiche la version. |
| `--prefer CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier dont les copies sont gardées en priorité ; répétable, l'ordre compte. [Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#préférer-un-dossier) |
| `--protect CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais modifié ; ses fichiers sont les copies gardées. [Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#protéger-un-dossier) |
| `--exclude CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais analysé. [Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#exclure-un-dossier) |
| `--backup CHEMIN` | `audit`, `review`, `clean`, `crosscheck`, `import` ; `undo`, `sort`, `album`, `xmp` | Une sauvegarde ou un ancien disque : comparé, jamais modifié ; l'audit dit ce qui lui manque et ce que lui seul contient. Les commandes qui modifient des fichiers la laissent intacte, sans la refuser parce qu'elle est en lecture seule ; `mh` passe vos sauvegardes à chacune. [Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque) |
| `--exclude-name NOM` | `audit`, `clean`, `crosscheck` | Nom de dossier jamais analysé, où qu'il soit (casse ignorée, `*` et `?` permis : `--exclude-name Thumbnails,.Trash-*`) ; s'ajoute aux dossiers système et corbeilles toujours ignorés. [Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#ignorer-un-nom-de-dossier-sur-tous-les-disques) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | N'analyse que ces catégories ou extensions (`--ext photo,video`, `--ext png,webp`) ; catégories intégrées `photo`, `raw`, `video`, `media`, plus celles de `[scan.categories]` ; `media` (toutes les photos, RAW et vidéos) par défaut. D'autres types aussi (`--ext pdf,docx`). [Étape 6 du nettoyage](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge`, `classify`, `tags`, `audit`, `import` | Ne pas demander de confirmation (`undo` ne demande qu'avant d'annuler plusieurs passages d'un tri ; `classify` et `tags`, avant de décrire beaucoup de photos avec un modèle local ; `audit`, avant de chercher les visages avec `--people`). |
| `--people` | `audit` | Chercher ensuite les visages des photos pas encore examinées, après avoir dit combien de temps cela prend et demandé. [Personnes](reference-people.md#pendant-laudit--audit---people) |
| `--tier exact\|near\|near-all` | `clean` | `exact` (par défaut) : seulement les copies identiques octet par octet. `near` : déplace aussi en quarantaine les quasi-doublons sûrs, et ceux décidés avec `review --near`. `near-all` : tous les quasi-doublons. [Étape 11 du nettoyage](clean/11-near-duplicates.md#les-groupes-sûrs-et-ceux-à-vérifier) |
| `--near` | `review` | Décider les quasi-doublons groupe par groupe (comme prévu, garder l'autre version, laisser tel quel, n'en garder aucune) au lieu de trier les rafales. [Étape 11 du nettoyage](clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near) |
| `--delete` | `clean` | Supprime pour de bon les copies exactes, après une comparaison octet par octet, au lieu de les déplacer en quarantaine ; `undo` les reconstruit depuis la copie gardée. [Étape 8 du nettoyage](clean/08-clean.md#besoin-de-la-place-tout-de-suite----delete) |
| `--decisions FICHIER` | `clean`, `review` | `clean` : applique les décisions sur les paires de dossiers d'un rapport, les photos de rafale écartées avec `review` et les groupes de quasi-doublons décidés avec `review --near` (avec `--tier near`). `review` : le fichier où les choix sont enregistrés, `decisions.json` par défaut. Un chemin relatif est lu dans `/reports`. Une fois appliqué par `clean`, le fichier est renommé `decisions.applied-<run>.json`. [Étape 10 du nettoyage](clean/10-review-bursts.md), [étape 12 du nettoyage](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review`, `review-sort`, `places`, `search`, `browse`, `people`, `home`, `slideshow` | Port de la page, `[review] port` de `config.toml` par défaut (`8088`) ; publiez le même : `-p 127.0.0.1:8088:8088`. |
| `--prune N` | `reports` | Garde les N rapports les plus récents, supprime les autres. |
| `--photos "C:\Photos"` | `launcher` | Un dossier de photos et vidéos, tel que l'Explorateur le montre ; répétez-la pour plusieurs dossiers. Pas besoin de `-v`. [Nettoyer en bref, 0](clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh) |
| `--quarantine "D:\quarantaine"` | `launcher` | Où vont les copies mises de côté ; de préférence sur le disque des photos. Par défaut : `$HOME\media-hygiene\quarantine`. |
| `--shell powershell\|bash` | `launcher` | Le shell du script `mh` ; deviné par défaut d'après les dossiers montés (un dossier Windows : PowerShell). [Étape 3](start/01-first-audit.md#écrire-mh-une-fois) |
| `--year ANNÉE[-ANNÉE]` | `classify` | Seulement les fichiers de cette année ou de ces années. [Étape 4 du tri](sort/04-classify.md#votre-propre-structure) |
| `--layout DISPOSITION` | `classify` | Où vont les fichiers sûrs, par exemple `{year}/{month}`. [Étape 4 du tri](sort/04-classify.md#votre-propre-structure) |
| `--target CHEMIN` | `classify` | Dossier qui reçoit l'arborescence ; chaque dossier monté, sur place, par défaut. |
| `--leave CHEMIN` | `classify` | Dossier jamais trié ; toujours analysé et nettoyé. |
| `--carry-over CHEMIN` | `classify` | Classeur dont les modifications sont reprises ; celui du dernier `classify` par défaut. [Étape 5 du tri](sort/05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail) |
| `--no-carry-over` | `classify` | Repartir de zéro : ne reprendre aucune modification d'un classeur précédent. |
| `--sample N` | `classify` | Décrire N photos prises au hasard avec le modèle local, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Étape 8 du tri](sort/08-subjects-from-a-local-model.md#mesurer-dabord----sample) |
| `--no-describe` | `classify` | Ne rien demander de nouveau au modèle local : les règles `subject` lisent les descriptions déjà dans le cache. [Étape 8 du tri](sort/08-subjects-from-a-local-model.md#la-longue-exécution-jamais-une-surprise) |
| `--sample N` | `tags` | Décrire N photos prises au hasard avec le modèle local, afficher leurs mots, le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Tags](reference-tags.md#mesurer-dabord----sample) |
| `--no-describe` | `tags` | Ne rien demander de nouveau au modèle local : les mots des dossiers, des noms, des dates et des lieux, et les descriptions déjà dans le cache. [Tags](reference-tags.md#les-mots-dun-modèle-de-vision-local) |
| `--path CHEMIN` | `tags`, `xmp`, `people` | Seulement les photos sous ce dossier (chemin de l'hôte) ; à répéter pour plusieurs. [Tags](reference-tags.md#un-dossier-dabord----path) |
| `--sample N` | `people` | Analyser N photos prises au hasard, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Personnes](reference-people.md#mesurer-dabord----sample) |
| `--forget` | `people` | Supprimer tous les visages du cache, puis montrer qu'il n'en reste aucun ; demande avant de supprimer aussi les noms de `config.toml`. [Personnes](reference-people.md#votre-vie-privée) |
| `--limit N` | `search` | Avec des mots : lister au plus N fichiers (20 par défaut). [Tags](reference-tags.md#retrouver-une-photo-par-ses-mots--search) |
| `--format xlsx\|csv` | `inventory` | `xlsx` (par défaut) : un classeur avec les feuilles Fichiers et Résumé. `csv` : la feuille Fichiers seule, comme `plan.csv`. [Inventaire](reference-inventory.md#un-fichier-csv-à-la-place) |
| `--keep-empty-folders` | `sort` | Garder les dossiers sources que le tri laisse vides. [Étape 7 du tri](sort/07-sort.md#les-dossiers-laissés-vides) |
| `--category NOM` | `album` | Au lieu d'un album enregistré : les fichiers de cette catégorie, d'après le classeur modifié (un événement nommé dans le classeur donne son nom). [Étape 12 du tri](sort/12-albums.md#choisir-ce-que-lalbum-rassemble) |
| `--event ÉVÉNEMENT` | `album` | Les fichiers de cet événement : son identifiant (feuille Événements) ou son nom. |
| `--rule NOM` | `album` | Les fichiers que l'entrée `[[classify.rules]]` de ce nom a décidés. |
| `--rating N` | `album` | Les fichiers qui ont au moins N étoiles (1 à 5) dans Windows, telles que l'audit les a lues (demande `/cache`). |
| `--workbook CHEMIN` | `album` | Le classeur de `classify` à lire ; celui du dernier `classify` par défaut. |
| `--apply` | `album`, `xmp` | Crée les liens, écrit les fichiers compagnons ; sans cette option, `album` et `xmp` montrent seulement ce qu'ils feraient. |

La plupart des options ont leur équivalent dans `config.toml` ([étape 7 du nettoyage](clean/07-configuration-file.md)) ;
la ligne de commande l'emporte. Les règles de `classify` (`[[classify.rules]]`) n'ont pas
d'option : elles s'écrivent dans `config.toml` seulement ([étape 6 du tri](sort/06-write-down-what-you-know.md)).

## L'aide intégrée

`cavo789/media-hygiene --help` et `cavo789/media-hygiene <commande> --help` documentent tout, dans
les deux langues (`--locale fr --help`). Une commande de plus de quatre options montre d'abord celles
d'usage courant, sous **Options** (`clean --tier`, `review --near`, `classify --year`…) ; les autres
suivent, sous **Options avancées** et, pour les dossiers et l'analyse, sous
**Avancé : dossiers** et **Avancé : analyse** (elles remplacent `config.toml`). La page de chaque
commande montre son propre `--help` ; voici la liste des commandes :

<details>
<summary><code>--help</code></summary>

<!-- capture: help.txt -->
```text
 Utilisation : media-hygiene [OPTIONS] COMMANDE [ARGS]...

 Trouve et nettoie en toute sécurité les photos et vidéos en double, entre
 dossiers et disques. Commencez par 'audit' (lecture seule), puis 'clean'.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --version            Affiche la version et quitte.                           │
│ --help     -h        Affiche ce message et quitte.                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Affichage (remplace general.* de config.toml) ──────────────────────────────╮
│ --locale           <en|fr>                      Langue de l'interface.       │
│ --verbosity        <error|warning|info|verbose  Niveau de détail des         │
│                    |debug>                      journaux.                    │
│ --color            <auto|always|never>          Quand utiliser les couleurs  │
│                                                 (NO_COLOR est aussi          │
│                                                 respecté).                   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🔒 Analyser : lecture seule, ne modifie jamais vos photos ──────────────────╮
│ audit        Trouver les doublons exacts et les fichiers cassés.             │
│ browse       Parcourir vos dossiers dans votre navigateur, comme dans        │
│              l'Explorateur, et mettre des photos de côté ; 'clean            │
│              --decisions' les déplace ensuite.                               │
│ classify     Propose où ranger chaque photo et vidéo : année, événement,     │
│              catégorie, et ce que montrent les photos isolées avec une IA    │
│              locale facultative 🤖                                           │
│ config       Affiche chaque réglage, son origine, et les points de montage.  │
│ crosscheck   Lance Czkawka, un détecteur de doublons indépendant, puis       │
│              compare ses groupes à un nouvel audit : un second avis.         │
│ history      Liste les exécutions et ce qu'elles ont fait.                   │
│ home         La page d'accueil dans votre navigateur : où vous en êtes,      │
│              l'étape suivante en un bouton, toutes les étapes des guides,    │
│              les rapports.                                                   │
│ inventory    Exporter vers Excel chaque photo et vidéo avec ce que les       │
│              audits en ont appris, depuis le cache seul : aucun fichier      │
│              n'est lu.                                                       │
│ launcher     Écrit 'mh', une commande courte qui retient vos dossiers : mh   │
│              audit, mh clean.                                                │
│ menu         Chaque étape des guides avec sa commande, la prochaine en       │
│              premier : ce que montre 'mh' seul, Entrée la lance.             │
│ people       Trouver les visages des photos, regrouper ceux qui se           │
│              ressemblent et les nommer dans votre navigateur. Visages gardés │
│              dans le cache, jamais envoyés nulle part.                       │
│ places       Nommer vos lieux sur une carte des endroits où les photos ont   │
│              été prises ; enregistrés dans config.toml pour les règles       │
│              'place' et 'trip'.                                              │
│ reports      Liste les rapports HTML des audits et nettoyages précédents.    │
│ review       Écarter des photos de rafale, une série à la fois, au clavier   │
│              dans votre navigateur ; 'clean --decisions' les déplace         │
│              ensuite.                                                        │
│ review-sort  Nommer les événements de la proposition de classify un par un,  │
│              dans votre navigateur.                                          │
│ search       Retrouver des photos par leurs mots dans votre navigateur (ou   │
│              en tableau) : les mots que 'tags' leur a donnés.                │
│ share        Préparer un album pour l'envoyer : des copies réduites sans la  │
│              position GPS, un dossier et un zip, pour un mail ou un réseau   │
│              social.                                                         │
│ slideshow    Montrer des photos sur la télé, le téléphone choisissant la     │
│              suivante : un dossier, une recherche ou les fichiers mis de     │
│              côté.                                                           │
│ status       Où en suis-je ? Le dernier audit, la quarantaine, ce qu'il      │
│              reste : sans analyse.                                           │
│ tags         Donner à chaque photo des mots pour la retrouver, gardés dans   │
│              le cache, jamais dans les photos : ses dossiers, son nom, sa    │
│              date, son lieu, et ce qu'elle montre avec une IA locale         │
│              facultative 🤖                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Agir : déplace, écrit ou supprime des fichiers ─────────────────────────────╮
│ album        Rassemble une sélection du plan de classify dans un dossier de  │
│              liens physiques : rien n'est copié ni déplacé (journalisé,      │
│              annulable).                                                     │
│ backup       Windows seulement, en mh backup : copier vos dossiers de photos │
│              dans un dossier rien qu'à eux sur le NAS, seulement ce qui lui  │
│              manque ; une photo déplacée y est renommée, une suppression par │
│              erreur n'y est jamais reportée. Lancée ici, elle montre le      │
│              plan.                                                           │
│ clean        Analyser, confirmer, puis déplacer les copies en double en      │
│              quarantaine, après une comparaison octet par octet (journalisé, │
│              annulable) ; --delete les supprime pour de bon.                 │
│ import       Copie dans vos photos ce qu'une sauvegarde (un NAS) est seule à │
│              contenir, jamais ce que vous avez mis de côté ou supprimé avant │
│              ; chaque copie prouvée (journalisé, annulable).                 │
│ purge        Effacer pour de bon la quarantaine d'une exécution : avec       │
│              'clean --delete', la seule façon dont l'outil supprime du       │
│              contenu.                                                        │
│ shrink       Lister les vidéos lourdes qui gagnent à être allégées (anciens  │
│              appareils, MJPEG) ; avec --apply, les réencoder en H.264,       │
│              chacune vérifiée, l'original en quarantaine (journalisé,        │
│              annulable).                                                     │
│ sort         Déplacer les photos et vidéos comme le dit le classeur de       │
│              classify modifié (journalisé, annulable).                       │
│ undo         Restaure chaque fichier d'une exécution, depuis la copie        │
│              conservée, la quarantaine ou là où il a été déplacé ; supprime  │
│              les liens d'un album.                                           │
│ xmp          Écrire les mots de 'tags' dans des fichiers compagnons .xmp à   │
│              côté des photos, pour digiKam, darktable, Lightroom ou Immich ; │
│              jamais dans une photo (journalisé, annulable).                  │
╰──────────────────────────────────────────────────────────────────────────────╯


 Un dossier Windows (PowerShell) :
   docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" media-hygiene audit
 Le dossier courant (PowerShell, ou bash sous WSL, Linux, macOS) :
   docker run --rm -it -v "${PWD}:/data/current:ro" media-hygiene audit

 Guide pas à pas et toutes les commandes :
 https://cavo789.github.io/media-hygiene/fr/
```

</details>
