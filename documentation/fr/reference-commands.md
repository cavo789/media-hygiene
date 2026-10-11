# Commandes et options

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-commands.md)

Chaque commande, chaque option. Le [guide](README.md#pour-commencer) les présente une à une ;
cette page les rassemble. Les commandes dont l'aide commence par *Lecture seule* ne modifient jamais vos photos
([comment vos photos restent en sécurité](reference-safety.md)).

## Commandes

| Commande | Rôle | Guide |
|---|---|---|
| `audit` | Trouve les doublons exacts et les fichiers cassés. N'écrit jamais dans vos dossiers. | [1](start/01-first-audit.md) |
| `review` | Analyse, puis trie les rafales dans votre navigateur, une à la fois, au clavier ; `--near` : décider les quasi-doublons groupe par groupe. N'écrit jamais dans vos dossiers. | [10](clean/10-review-bursts.md), [11](clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near) |
| `clean` | Audite, demande confirmation, puis déplace en quarantaine les copies en double, les fichiers illisibles et les fichiers compagnons orphelins, et supprime les fichiers vides ; `--delete` supprime les copies à la place. | [8](clean/08-clean.md) |
| `undo [EXÉCUTION]` | Restaure chaque fichier d'une exécution (la plus récente par défaut) ; pour un album, supprime ses liens. | [9](clean/09-undo-history-purge.md) |
| `status` | Où en suis-je ? Le dernier audit, la quarantaine, les exécutions encore annulables, les tris pas appliqués, la dernière proposition pas triée ; puis une étape suivante en commande complète. Ne lit que les dossiers de l'outil, sans analyse. | [9](clean/09-undo-history-purge.md#où-en-suis-je--status) |
| `history` | Liste les exécutions : leur commande, fichiers supprimés, espace libéré, quarantaine, restaurations. | [9](clean/09-undo-history-purge.md) |
| `purge [EXÉCUTION]` | Efface pour de bon la quarantaine d'une exécution (de toutes par défaut) : la seule commande qui efface du contenu, avec `clean --delete`. | [9](clean/09-undo-history-purge.md) |
| `reports [--prune N]` | Liste les rapports et régénère `index.html` ; `--prune N` garde les N plus récents. | [4](clean/04-html-report.md) |
| `crosscheck` | Refait l'audit, puis le compare aux résultats de Czkawka, un détecteur de doublons indépendant. | [13](clean/13-second-opinion.md) |
| `classify` | Propose où ranger chaque photo et vidéo : année, événement, catégorie. N'écrit jamais dans vos dossiers ; écrit un classeur à modifier et un rapport dans `/reports`. | [4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md), [8](sort/08-subjects-from-a-local-model.md) |
| `sort [CLASSEUR]` | Vérifier le classeur modifié de `classify`, confirmer, puis déplacer les fichiers là où il le dit ; journalisé, annulable, prouvé. | [7](sort/07-sort.md) |
| `album NOM` | Rassemble une sélection du plan de `classify` (une catégorie, un événement, une règle, les étoiles) dans un dossier de liens physiques : rien de copié ni de déplacé, aucune place prise. Montre la sélection ; `--apply` crée les liens, journalisés et annulables. | [Trier, étape 11](sort/11-albums.md) |
| `inventory [--format xlsx\|csv]` | Exporte chaque photo et vidéo avec ce que les audits en ont appris vers un classeur Excel (ou un fichier CSV), depuis le cache seul : aucun fichier n'est lu. | [Référence](reference-inventory.md) |
| `tags` | Donne à chaque photo des mots pour la retrouver : les mots parlants de ses dossiers, sa date (année, mois, saison, fêtes), son lieu, et ce qu'y voit un modèle de vision local (facultatif). Gardés dans le cache, jamais écrits dans les photos. | [Référence](reference-tags.md) |
| `xmp` | Écrit les mots de `tags` dans des fichiers compagnons `.xmp` à côté des photos, pour digiKam, darktable, Lightroom ou Immich ; jamais dans une photo. Montre ce qu'il écrirait ; `--apply` écrit, journalisé et annulable. | [Référence](reference-tags.md#emporter-les-mots-avec-les-photos--xmp) |
| `search [MOTS]` | Retrouve des photos par leurs mots (ceux de `tags`) dans votre navigateur, avec filtres et aperçus ; avec des mots, affiche les premiers résultats en tableau. N'écrit jamais dans vos dossiers. | [Référence](reference-tags.md#retrouver-une-photo-par-ses-mots--search) |
| `people` | Trouve les visages des photos, regroupe ceux qui se ressemblent, et montre les groupes dans votre navigateur. Les visages restent dans le cache, jamais envoyés nulle part ; `--forget` les supprime tous. N'écrit jamais dans vos dossiers. | [Référence](reference-people.md) |
| `launcher [--shell powershell\|bash]` | Affiche le script de `mh`, une commande courte qui retient les dossiers de cette exécution : `mh audit`, `mh clean`… avec les bons montages pour chaque commande. À rediriger vers un fichier (`> mh.ps1`), sans `-it`. | [3](start/03-several-folders.md#écrire-vos-dossiers-une-fois--mh) |
| `config` | Affiche chaque réglage, son origine, et l'état de chaque point de montage. | [7](clean/07-configuration-file.md) |
| `review-sort [CLASSEUR]` | Montre les événements de la proposition de `classify` un par un dans votre navigateur, avec leurs photos, et les nomme au clavier ; enregistré à côté de `plan.json`, appliqué par `sort`. N'écrit jamais dans vos dossiers ni dans le classeur. | [Trier, étape 10](sort/10-name-events-in-the-browser.md) |
| `places` | Montre sur une carte dans votre navigateur où les photos ont été prises, et nomme vos lieux ; enregistrés dans `config.toml`. N'écrit jamais dans vos dossiers. | [Trier, étape 9](sort/09-places-from-gps.md) |

## Options

Les options globales se placent **avant** la commande : `cavo789/media-hygiene --locale fr audit`.
Les autres se placent **après** : `cavo789/media-hygiene audit --prefer "C:\Photos\Famille"`.

| Option | Commandes | Rôle |
|---|---|---|
| `--locale en\|fr` | globale | Langue de l'interface (anglais par défaut) ; les nombres et tailles la suivent : `67,947` et `44.3 GB`, ou `67.947` et `44,3 Go`. |
| `--verbosity error\|warning\|info\|verbose\|debug` | globale | Niveau de détail des journaux. `verbose` : `info`, plus toutes les astuces d'une commande (pas seulement les deux plus utiles) et l'inventaire après un audit. |
| `--color auto\|always\|never` | globale | Couleurs ANSI (`NO_COLOR` est respecté). |
| `--version` | globale | Affiche la version. |
| `--prefer CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier dont les copies sont gardées en priorité ; répétable, l'ordre compte. [Étape 5](clean/05-choose-the-kept-copy.md#préférer-un-dossier) |
| `--protect CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais modifié ; ses fichiers sont les copies gardées. [Étape 5](clean/05-choose-the-kept-copy.md#protéger-un-dossier) |
| `--exclude CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais analysé. [Étape 5](clean/05-choose-the-kept-copy.md#exclure-un-dossier) |
| `--exclude-name NOM` | `audit`, `clean`, `crosscheck` | Nom de dossier jamais analysé, où qu'il soit (casse ignorée, `*` et `?` permis : `--exclude-name Thumbnails,.Trash-*`) ; s'ajoute aux dossiers système et corbeilles toujours ignorés. [Étape 5](clean/05-choose-the-kept-copy.md#ignorer-un-nom-de-dossier-sur-tous-les-disques) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | N'analyse que ces catégories ou extensions (`--ext photo,video`, `--ext png,webp`) ; catégories intégrées `photo`, `raw`, `video`, `media`, plus celles de `[scan.categories]` ; `media` (toutes les photos, RAW et vidéos) par défaut. D'autres types aussi (`--ext pdf,docx`). [Étape 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge`, `classify`, `tags` | Ne pas demander de confirmation (`undo` ne demande qu'avant d'annuler plusieurs passages d'un tri ; `classify` et `tags`, avant de décrire beaucoup de photos avec un modèle local). |
| `--tier exact\|near\|near-all` | `clean` | `exact` (par défaut) : seulement les copies identiques octet par octet. `near` : déplace aussi en quarantaine les quasi-doublons sûrs, et ceux décidés avec `review --near`. `near-all` : tous les quasi-doublons. [Étape 11](clean/11-near-duplicates.md#les-groupes-sûrs-et-ceux-à-vérifier) |
| `--near` | `review` | Décider les quasi-doublons groupe par groupe (comme prévu, garder l'autre version, laisser tel quel) au lieu de trier les rafales. [Étape 11](clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near) |
| `--delete` | `clean` | Supprime pour de bon les copies exactes, après une comparaison octet par octet, au lieu de les déplacer en quarantaine ; `undo` les reconstruit depuis la copie gardée. [Étape 8](clean/08-clean.md#besoin-de-la-place-tout-de-suite----delete) |
| `--decisions FICHIER` | `clean`, `review` | `clean` : applique les décisions sur les paires de dossiers d'un rapport, les photos de rafale écartées avec `review` et les groupes de quasi-doublons décidés avec `review --near` (avec `--tier near`). `review` : le fichier où les choix sont enregistrés, `decisions.json` par défaut. Un chemin relatif est lu dans `/reports`. Une fois appliqué par `clean`, le fichier est renommé `decisions.applied-<run>.json`. [Étape 10](clean/10-review-bursts.md), [étape 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review`, `review-sort`, `places`, `search`, `people` | Port de la page, `8088` par défaut ; publiez le même : `-p 127.0.0.1:8088:8088`. |
| `--prune N` | `reports` | Garde les N rapports les plus récents, supprime les autres. |
| `--shell powershell\|bash` | `launcher` | Le shell du script `mh` ; deviné par défaut d'après les dossiers montés (un dossier Windows : PowerShell). [Étape 3](start/03-several-folders.md#écrire-vos-dossiers-une-fois--mh) |
| `--year ANNÉE[-ANNÉE]` | `classify` | Seulement les fichiers de cette année ou de ces années. [Trier, étape 4](sort/04-classify.md#votre-propre-structure) |
| `--layout DISPOSITION` | `classify` | Où vont les fichiers sûrs, par exemple `{year}/{month}`. [Trier, étape 4](sort/04-classify.md#votre-propre-structure) |
| `--target CHEMIN` | `classify` | Dossier qui reçoit l'arborescence ; chaque dossier monté, sur place, par défaut. |
| `--leave CHEMIN` | `classify` | Dossier jamais trié ; toujours analysé et nettoyé. |
| `--carry-over CHEMIN` | `classify` | Classeur dont les modifications sont reprises ; celui du dernier `classify` par défaut. [Trier, étape 5](sort/05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail) |
| `--no-carry-over` | `classify` | Repartir de zéro : ne reprendre aucune modification d'un classeur précédent. |
| `--sample N` | `classify` | Décrire N photos prises au hasard avec le modèle local, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Trier, étape 8](sort/08-subjects-from-a-local-model.md#mesurer-dabord----sample) |
| `--no-describe` | `classify` | Ne rien demander de nouveau au modèle local : les règles `subject` lisent les descriptions déjà dans le cache. [Trier, étape 8](sort/08-subjects-from-a-local-model.md#la-longue-exécution-jamais-une-surprise) |
| `--sample N` | `tags` | Décrire N photos prises au hasard avec le modèle local, afficher leurs mots, le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Tags](reference-tags.md#mesurer-dabord----sample) |
| `--no-describe` | `tags` | Ne rien demander de nouveau au modèle local : les mots des dossiers, des dates et des lieux, et les descriptions déjà dans le cache. [Tags](reference-tags.md#les-mots-dun-modèle-de-vision-local) |
| `--path CHEMIN` | `tags`, `xmp`, `people` | Seulement les photos sous ce dossier (chemin de l'hôte) ; à répéter pour plusieurs. [Tags](reference-tags.md#un-dossier-dabord----path) |
| `--sample N` | `people` | Analyser N photos prises au hasard, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Personnes](reference-people.md#mesurer-dabord----sample) |
| `--forget` | `people` | Supprimer tous les visages du cache, puis montrer qu'il n'en reste aucun. [Personnes](reference-people.md#votre-vie-privée) |
| `--limit N` | `search` | Avec des mots : lister au plus N fichiers (20 par défaut). [Tags](reference-tags.md#retrouver-une-photo-par-ses-mots--search) |
| `--format xlsx\|csv` | `inventory` | `xlsx` (par défaut) : un classeur avec les feuilles Fichiers et Résumé. `csv` : la feuille Fichiers seule, comme `plan.csv`. [Inventaire](reference-inventory.md#un-fichier-csv-à-la-place) |
| `--keep-empty-folders` | `sort` | Garder les dossiers sources que le tri laisse vides. [Trier, étape 7](sort/07-sort.md#les-dossiers-laissés-vides) |
| `--category NOM` | `album` | Les fichiers de cette catégorie, d'après le classeur modifié (un événement nommé dans le classeur donne son nom). [Trier, étape 11](sort/11-albums.md#choisir-ce-que-lalbum-rassemble) |
| `--event ÉVÉNEMENT` | `album` | Les fichiers de cet événement : son identifiant (feuille Événements) ou son nom. |
| `--rule NOM` | `album` | Les fichiers que l'entrée `[[classify.rules]]` de ce nom a décidés. |
| `--rating N` | `album` | Les fichiers qui ont au moins N étoiles (1 à 5) dans Windows, telles que l'audit les a lues (demande `/cache`). |
| `--workbook CHEMIN` | `album` | Le classeur de `classify` à lire ; celui du dernier `classify` par défaut. |
| `--apply` | `album`, `xmp` | Crée les liens, écrit les fichiers compagnons ; sans cette option, `album` et `xmp` montrent seulement ce qu'ils feraient. |

La plupart des options ont leur équivalent dans `config.toml` ([étape 7](clean/07-configuration-file.md)) ;
la ligne de commande l'emporte. Les règles de `classify` (`[[classify.rules]]`) n'ont pas
d'option : elles s'écrivent dans `config.toml` seulement ([trier, étape 6](sort/06-write-down-what-you-know.md)).

## L'aide intégrée

`cavo789/media-hygiene --help` et `cavo789/media-hygiene <commande> --help` documentent tout, dans
les deux langues (`--locale fr --help`). Une commande de plus de quatre options montre d'abord celles
d'usage courant, sous **Options** (`clean --tier`, `review --near`, `classify --year`…) ; les autres
suivent, sous **Options avancées** et, pour les dossiers et l'analyse, sous
**Avancé : dossiers** et **Avancé : analyse** (elles remplacent `config.toml`). Voici ce qu'elles
affichent :

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
│ classify     Propose où ranger chaque photo et vidéo : année, événement,     │
│              catégorie.                                                      │
│ config       Affiche chaque réglage, son origine, et les points de montage.  │
│ crosscheck   Compare un nouvel audit aux résultats de Czkawka : un second    │
│              avis, indépendant.                                              │
│ history      Liste les exécutions et ce qu'elles ont fait.                   │
│ inventory    Exporter vers Excel chaque photo et vidéo avec ce que les       │
│              audits en ont appris, depuis le cache seul : aucun fichier      │
│              n'est lu.                                                       │
│ launcher     Écrit 'mh', une commande courte qui retient vos dossiers : mh   │
│              audit, mh clean.                                                │
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
│ status       Où en suis-je ? Le dernier audit, la quarantaine, ce qu'il      │
│              reste : sans analyse.                                           │
│ tags         Donner à chaque photo des mots pour la retrouver : ses          │
│              dossiers, sa date, son lieu, et ce qu'y voit un modèle de       │
│              vision local. Gardés dans le cache, jamais dans les photos.     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Agir : déplace, écrit ou supprime des fichiers ─────────────────────────────╮
│ album        Rassemble une sélection du plan de classify dans un dossier de  │
│              liens physiques : rien n'est copié ni déplacé (journalisé,      │
│              annulable).                                                     │
│ clean        Analyser, confirmer, puis déplacer les copies en double en      │
│              quarantaine, après une comparaison octet par octet (journalisé, │
│              annulable) ; --delete les supprime pour de bon.                 │
│ purge        Effacer pour de bon la quarantaine d'une exécution : avec       │
│              'clean --delete', la seule façon dont l'outil supprime du       │
│              contenu.                                                        │
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

 Commandes complètes (rapports, journal, WSL) : voir README_FR.md.
```

</details>

<details>
<summary><code>audit --help</code></summary>

<!-- capture: help-audit.txt -->
```text
 Utilisation : media-hygiene audit [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Trouver les doublons exacts
 et les fichiers cassés.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : analyse (remplace scan.* de config.toml) ──────────────────────────╮
│ --ext                 <str>  N'analyse que ces catégories ou extensions, p.  │
│                              ex. --ext photo,video ou --ext png,webp         │
│                              (répétable). Catégories : photo, raw, video,    │
│                              media et celles de scan.categories dans         │
│                              config.toml. D'autres types aussi, comme --ext  │
│                              pdf,docx : leurs copies sont déplacées en       │
│                              quarantaine. Par défaut : media (toutes les     │
│                              photos, RAW et vidéos).                         │
│ --exclude-name        <str>  Nom de dossier jamais analysé, où qu'il soit,   │
│                              sans tenir compte de la casse ; * et ? permis,  │
│                              p. ex. --exclude-name Thumbnails,.Trash-*       │
│                              (répétable). S'ajoute aux dossiers système déjà │
│                              ignorés. Pour un dossier précis, utilisez       │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>review --help</code></summary>

<!-- capture: help-review.txt -->
```text
 Utilisation : media-hygiene review [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Écarter des photos de rafale,
 une série à la fois, au clavier dans votre navigateur ; 'clean --decisions'
 les déplace ensuite.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --near            Passer en revue les quasi-doublons et les vidéos           │
│                   réencodées groupe par groupe au lieu des rafales : comme   │
│                   prévu, garder l'autre version, ou laisser tel quel ; «     │
│                   clean --tier near --decisions » l'applique.                │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --decisions        <path>              Fichier où les décisions sont         │
│                                        enregistrées, et repris au lancement  │
│                                        suivant. Un chemin relatif se trouve  │
│                                        dans le dossier monté sur /reports.   │
│                                        Par défaut : decisions.json.          │
│ --port             <int range> [x>=1]  Port de la page. docker run le publie │
│                                        sous le même numéro sur votre         │
│                                        ordinateur, par exemple -p            │
│                                        127.0.0.1:9000:9000 pour --port 9000. │
│                                        Par défaut : 8088.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>clean --help</code></summary>

<!-- capture: help-clean.txt -->
```text
 Utilisation : media-hygiene clean [OPTIONS]

 Analyser, confirmer, puis déplacer les copies en double en quarantaine, après
 une comparaison octet par octet (journalisé, annulable) ; --delete les
 supprime pour de bon.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --tier               <exact|near|near-all>  Jusqu'où nettoyer. exact (par    │
│                                             défaut) : seulement les copies   │
│                                             identiques octet par octet. near │
│                                             : aussi les copies réduites      │
│                                             (envoyées par WhatsApp ou par    │
│                                             e-mail, redimensionnées,         │
│                                             recompressées) et les vidéos     │
│                                             réencodées qui sont sûres ; les  │
│                                             groupes à vérifier restent en    │
│                                             place. near-all : tous les       │
│                                             quasi-doublons ; vérifiez-les    │
│                                             d'abord dans le rapport. Les     │
│                                             quasi-doublons partent en        │
│                                             quarantaine, jamais supprimés.   │
│ --decisions          <path>                 Appliquer les choix faits dans   │
│                                             le navigateur : decisions.json   │
│                                             téléchargé depuis un rapport     │
│                                             d'audit (paires de dossiers      │
│                                             inversées ou laissées telles     │
│                                             quelles) ou écrit par 'review'   │
│                                             (photos de rafale écartées,      │
│                                             quasi-doublons décidés). Un      │
│                                             chemin relatif est lu dans le    │
│                                             dossier monté sur /reports. Le   │
│                                             fichier est refusé si les        │
│                                             dossiers, les paires ou les      │
│                                             séries ont changé. Seul,         │
│                                             --decisions lit decisions.json.  │
│ --yes        -y                             Ne pas demander de confirmation  │
│                                             (remplace clean.confirm).        │
│ --help       -h                             Affiche ce message et quitte.    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --delete          Libérer l'espace tout de suite : supprimer pour de bon les │
│                   copies exactes, après une comparaison octet par octet avec │
│                   la copie gardée, au lieu de les déplacer en quarantaine ;  │
│                   'undo' les reconstruit à partir de la copie gardée.        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : analyse (remplace scan.* de config.toml) ──────────────────────────╮
│ --ext                 <str>  N'analyse que ces catégories ou extensions, p.  │
│                              ex. --ext photo,video ou --ext png,webp         │
│                              (répétable). Catégories : photo, raw, video,    │
│                              media et celles de scan.categories dans         │
│                              config.toml. D'autres types aussi, comme --ext  │
│                              pdf,docx : leurs copies sont déplacées en       │
│                              quarantaine. Par défaut : media (toutes les     │
│                              photos, RAW et vidéos).                         │
│ --exclude-name        <str>  Nom de dossier jamais analysé, où qu'il soit,   │
│                              sans tenir compte de la casse ; * et ? permis,  │
│                              p. ex. --exclude-name Thumbnails,.Trash-*       │
│                              (répétable). S'ajoute aux dossiers système déjà │
│                              ignorés. Pour un dossier précis, utilisez       │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Utilisation : media-hygiene undo [OPTIONS] [run_id]

 Restaure chaque fichier d'une exécution, depuis la copie conservée, la
 quarantaine ou là où il a été déplacé ; supprime les liens d'un album.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution à annuler (voir 'history') ; la plus récente  │
│                      par défaut. Pour un tri, tous les passages du même      │
│                      classeur.                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Ne pas demander de confirmation avant d'annuler plusieurs  │
│                   passages d'un tri (remplace sort.confirm).                 │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>history --help</code></summary>

<!-- capture: help-history.txt -->
```text
 Utilisation : media-hygiene history [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Liste les exécutions et ce
 qu'elles ont fait.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>purge --help</code></summary>

<!-- capture: help-purge.txt -->
```text
 Utilisation : media-hygiene purge [OPTIONS] [run_id]

 Effacer pour de bon la quarantaine d'une exécution : avec 'clean --delete', la
 seule façon dont l'outil supprime du contenu.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution dont la quarantaine est effacée ; toutes par  │
│                      défaut.                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Ne pas demander de confirmation (remplace clean.confirm).  │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>reports --help</code></summary>

<!-- capture: help-reports.txt -->
```text
 Utilisation : media-hygiene reports [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Liste les rapports HTML des
 audits et nettoyages précédents.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --prune          <int range> [x>=0]  Supprime tous les rapports sauf les N   │
│                                      plus récents.                           │
│ --help   -h                          Affiche ce message et quitte.           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Utilisation : media-hygiene crosscheck [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Compare un nouvel audit aux
 résultats de Czkawka : un second avis, indépendant.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : analyse (remplace scan.* de config.toml) ──────────────────────────╮
│ --ext                 <str>  N'analyse que ces catégories ou extensions, p.  │
│                              ex. --ext photo,video ou --ext png,webp         │
│                              (répétable). Catégories : photo, raw, video,    │
│                              media et celles de scan.categories dans         │
│                              config.toml. D'autres types aussi, comme --ext  │
│                              pdf,docx : leurs copies sont déplacées en       │
│                              quarantaine. Par défaut : media (toutes les     │
│                              photos, RAW et vidéos).                         │
│ --exclude-name        <str>  Nom de dossier jamais analysé, où qu'il soit,   │
│                              sans tenir compte de la casse ; * et ? permis,  │
│                              p. ex. --exclude-name Thumbnails,.Trash-*       │
│                              (répétable). S'ajoute aux dossiers système déjà │
│                              ignorés. Pour un dossier précis, utilisez       │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>classify --help</code></summary>

<!-- capture: help-classify.txt -->
```text
 Utilisation : media-hygiene classify [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Propose où ranger chaque
 photo et vidéo : année, événement, catégorie.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year            <str>  Seulement les fichiers de cette année, ou de ces    │
│                          années : 2016 ou 2015-2017.                         │
│ --layout          <str>  Où vont les fichiers sûrs, par exemple              │
│                          '{year}/{month} - {month_name}'.                    │
│ --target          <str>  Dossier de l'hôte qui reçoit l'arborescence ; sur   │
│                          place par défaut.                                   │
│ --help    -h             Affiche ce message et quitte.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --leave                  <str>               Dossier de l'hôte jamais trié   │
│                                              (analysé et nettoyé comme       │
│                                              d'habitude).                    │
│ --carry-over             <str>               Classeur dont les modifications │
│                                              sont reprises ; celui du        │
│                                              dernier classify par défaut.    │
│ --no-carry-over                              Repartir de zéro : ne reprendre │
│                                              aucune modification d'un        │
│                                              classeur précédent.             │
│ --sample                 <int range> [x>=0]  Estimer d'abord une exécution   │
│                                              complète : décrire ce nombre de │
│                                              photos prises au hasard avec le │
│                                              modèle local, afficher le temps │
│                                              par photo et l'estimation d'une │
│                                              exécution complète, puis        │
│                                              s'arrêter.                      │
│ --no-describe                                Ne rien demander de nouveau au  │
│                                              modèle local : les règles       │
│                                              subject lisent les descriptions │
│                                              déjà dans le cache.             │
│ --yes            -y                          Décrire les photos sans         │
│                                              demander, quel que soit leur    │
│                                              nombre.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>sort --help</code></summary>

<!-- capture: help-sort.txt -->
```text
 Utilisation : media-hygiene sort [OPTIONS] [workbook]

 Déplacer les photos et vidéos comme le dit le classeur de classify modifié
 (journalisé, annulable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  Le classeur de classify, modifié ; celui du dernier   │
│                        classify par défaut.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes                 -y        Ne pas demander de confirmation (remplace    │
│                                 sort.confirm).                               │
│ --keep-empty-folders            Garder les dossiers sources que le tri       │
│                                 laisse vides.                                │
│ --help                -h        Affiche ce message et quitte.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>album --help</code></summary>

<!-- capture: help-album.txt -->
```text
 Utilisation : media-hygiene album [OPTIONS] {name}

 Rassemble une sélection du plan de classify dans un dossier de liens physiques
 : rien n'est copié ni déplacé (journalisé, annulable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    name      <str>  Le nom de l'album : le dossier qui contient ses liens. │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --category          <str>  Les fichiers de cette catégorie, d'après le       │
│                            classeur modifié.                                 │
│ --event             <str>  Les fichiers de cet événement : son identifiant   │
│                            ou son nom.                                       │
│ --apply                    Crée les liens ; sans cette option, montre        │
│                            seulement ce que l'album rassemble.               │
│ --help      -h             Affiche ce message et quitte.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --rule            <str>                  Les fichiers que la règle de        │
│                                          classify de ce nom a décidés.       │
│ --rating          <int range> [1<=x<=5]  Les fichiers qui ont au moins ces   │
│                                          étoiles dans Windows (1 à 5).       │
│ --workbook        <str>                  Le classeur de classify à lire ;    │
│                                          celui du dernier classify par       │
│                                          défaut.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>inventory --help</code></summary>

<!-- capture: help-inventory.txt -->
```text
 Utilisation : media-hygiene inventory [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Exporter vers Excel chaque
 photo et vidéo avec ce que les audits en ont appris, depuis le cache seul :
 aucun fichier n'est lu.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --format          <xlsx|csv>  xlsx : un classeur Excel (feuilles Fichiers et │
│                               Résumé). csv : la feuille Fichiers seule,      │
│                               comme plan.csv. Par défaut : xlsx.             │
│ --help    -h                  Affiche ce message et quitte.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Utilisation : media-hygiene config [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Affiche chaque réglage, son
 origine, et les points de montage.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>places --help</code></summary>

<!-- capture: help-places.txt -->
```text
 Utilisation : media-hygiene places [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Nommer vos lieux sur une
 carte des endroits où les photos ont été prises ; enregistrés dans config.toml
 pour les règles 'place' et 'trip'.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut : 8088.                       │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
