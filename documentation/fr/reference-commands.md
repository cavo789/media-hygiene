# Commandes et options

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-commands.md)

Chaque commande, chaque option. Le [guide](README.md#pour-commencer) les présente une à une ;
cette page les rassemble. Les commandes 🔒 ne modifient jamais vos photos
([comment vos photos restent en sécurité](reference-safety.md)).

## Commandes

| Commande | Rôle | Guide |
|---|---|---|
| `audit` | Trouve les doublons exacts et les fichiers cassés. N'écrit jamais dans vos dossiers. | [1](start/01-first-audit.md) |
| `review` | Analyse, puis trie les rafales dans votre navigateur, une à la fois, au clavier. N'écrit jamais dans vos dossiers. | [10](clean/10-review-bursts.md) |
| `clean` | Audite, demande confirmation, puis déplace en quarantaine les copies en double, les fichiers illisibles et les fichiers compagnons orphelins, et supprime les fichiers vides ; `--delete` supprime les copies à la place. | [8](clean/08-clean.md) |
| `undo [EXÉCUTION]` | Restaure chaque fichier d'une exécution (la plus récente par défaut) ; pour un album, supprime ses liens. | [9](clean/09-undo-history-purge.md) |
| `history` | Liste les exécutions : leur commande, fichiers supprimés, espace libéré, quarantaine, restaurations. | [9](clean/09-undo-history-purge.md) |
| `purge [EXÉCUTION]` | Efface pour de bon la quarantaine d'une exécution (de toutes par défaut) : la seule commande qui efface du contenu, avec `clean --delete`. | [9](clean/09-undo-history-purge.md) |
| `reports [--prune N]` | Liste les rapports et régénère `index.html` ; `--prune N` garde les N plus récents. | [4](clean/04-html-report.md) |
| `crosscheck` | Refait l'audit, puis le compare aux résultats de Czkawka, un détecteur de doublons indépendant. | [13](clean/13-second-opinion.md) |
| `classify` | Propose où ranger chaque photo et vidéo : année, événement, catégorie. N'écrit jamais dans vos dossiers ; écrit un classeur à modifier et un rapport dans `/reports`. | [4](sort/04-classify.md), [5](sort/05-review-the-proposal.md), [6](sort/06-write-down-what-you-know.md), [8](sort/08-subjects-from-a-local-model.md) |
| `sort [CLASSEUR]` | Vérifier le classeur modifié de `classify`, confirmer, puis déplacer les fichiers là où il le dit ; journalisé, annulable, prouvé. | [7](sort/07-sort.md) |
| `album NOM` | Rassemble une sélection du plan de `classify` (une catégorie, un événement, une règle, les étoiles) dans un dossier de liens physiques : rien de copié ni de déplacé, aucune place prise. Montre la sélection ; `--apply` crée les liens, journalisés et annulables. | [Trier, étape 11](sort/11-albums.md) |
| `inventory [--format xlsx\|csv]` | Exporte chaque photo et vidéo avec ce que les audits en ont appris vers un classeur Excel (ou un fichier CSV), depuis le cache seul : aucun fichier n'est lu. | [Référence](reference-inventory.md) |
| `config` | Affiche chaque réglage, son origine, et l'état de chaque point de montage. | [7](clean/07-configuration-file.md) |
| `review-sort [CLASSEUR]` | Montre les événements de la proposition de `classify` un par un dans votre navigateur, avec leurs photos, et les nomme au clavier ; enregistré à côté de `plan.json`, appliqué par `sort`. N'écrit jamais dans vos dossiers ni dans le classeur. | [Trier, étape 10](sort/10-name-events-in-the-browser.md) |
| `places` | Montre sur une carte dans votre navigateur où les photos ont été prises, et nomme vos lieux ; enregistrés dans `config.toml`. N'écrit jamais dans vos dossiers. | [Trier, étape 9](sort/09-places-from-gps.md) |

## Options

Les options globales se placent **avant** la commande : `cavo789/media-hygiene --locale fr audit`.
Les autres se placent **après** : `cavo789/media-hygiene audit --prefer "C:\Photos\Famille"`.

| Option | Commandes | Rôle |
|---|---|---|
| `--locale en\|fr` | globale | Langue de l'interface (anglais par défaut) ; les nombres et tailles la suivent : `67,947` et `44.3 GB`, ou `67.947` et `44,3 Go`. |
| `--verbosity error\|warning\|info\|debug` | globale | Niveau de détail des journaux. |
| `--color auto\|always\|never` | globale | Couleurs ANSI (`NO_COLOR` est respecté). |
| `--version` | globale | Affiche la version. |
| `--prefer CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier dont les copies sont gardées en priorité ; répétable, l'ordre compte. [Étape 5](clean/05-choose-the-kept-copy.md#préférer-un-dossier) |
| `--protect CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais modifié ; ses fichiers sont les copies gardées. [Étape 5](clean/05-choose-the-kept-copy.md#protéger-un-dossier) |
| `--exclude CHEMIN` | `audit`, `review`, `clean`, `crosscheck` | Dossier jamais analysé. [Étape 5](clean/05-choose-the-kept-copy.md#exclure-un-dossier) |
| `--exclude-name NOM` | `audit`, `clean`, `crosscheck` | Nom de dossier jamais analysé, où qu'il soit (casse ignorée, `*` et `?` permis : `--exclude-name Thumbnails,.Trash-*`) ; s'ajoute aux dossiers système et corbeilles toujours ignorés. [Étape 5](clean/05-choose-the-kept-copy.md#ignorer-un-nom-de-dossier-sur-tous-les-disques) |
| `--ext EXT` | `audit`, `clean`, `crosscheck` | N'analyse que ces catégories ou extensions (`--ext photo,video`, `--ext png,webp`) ; catégories intégrées `photo`, `raw`, `video`, `media`, plus celles de `[scan.categories]` ; `media` (toutes les photos, RAW et vidéos) par défaut. D'autres types aussi (`--ext pdf,docx`). [Étape 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `sort`, `undo`, `purge`, `classify` | Ne pas demander de confirmation (`undo` ne demande qu'avant d'annuler plusieurs passages d'un tri ; `classify`, avant de décrire beaucoup de photos avec un modèle local). |
| `--tier exact\|near` | `clean` | `exact` (par défaut) : seulement les copies identiques octet par octet. `near` : déplace aussi les quasi-doublons en quarantaine. [Étape 11](clean/11-near-duplicates.md) |
| `--delete` | `clean` | Supprime pour de bon les copies exactes, après une comparaison octet par octet, au lieu de les déplacer en quarantaine ; `undo` les reconstruit depuis la copie gardée. [Étape 8](clean/08-clean.md#besoin-de-la-place-tout-de-suite----delete) |
| `--decisions FICHIER` | `clean`, `review` | `clean` : applique les décisions sur les paires de dossiers d'un rapport et les photos de rafale écartées avec `review`. `review` : le fichier où les choix sont enregistrés, `decisions.json` par défaut. Un chemin relatif est lu dans `/reports`. [Étape 10](clean/10-review-bursts.md), [étape 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review`, `review-sort`, `places` | Port de la page dans le conteneur, `8080` par défaut ; publiez-le avec `-p 127.0.0.1::8080`. |
| `--prune N` | `reports` | Garde les N rapports les plus récents, supprime les autres. |
| `--year ANNÉE[-ANNÉE]` | `classify` | Seulement les fichiers de cette année ou de ces années. [Trier, étape 4](sort/04-classify.md#votre-propre-structure) |
| `--layout DISPOSITION` | `classify` | Où vont les fichiers sûrs, par exemple `{year}/{month}`. [Trier, étape 4](sort/04-classify.md#votre-propre-structure) |
| `--target CHEMIN` | `classify` | Dossier qui reçoit l'arborescence ; chaque dossier monté, sur place, par défaut. |
| `--leave CHEMIN` | `classify` | Dossier jamais trié ; toujours analysé et nettoyé. |
| `--carry-over CHEMIN` | `classify` | Classeur dont les modifications sont reprises ; celui du dernier `classify` par défaut. [Trier, étape 5](sort/05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail) |
| `--no-carry-over` | `classify` | Repartir de zéro : ne reprendre aucune modification d'un classeur précédent. |
| `--sample N` | `classify` | Décrire N photos prises au hasard avec le modèle local, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. [Trier, étape 8](sort/08-subjects-from-a-local-model.md#mesurer-dabord----sample) |
| `--no-describe` | `classify` | Ne rien demander de nouveau au modèle local : les règles `subject` lisent les descriptions déjà dans le cache. [Trier, étape 8](sort/08-subjects-from-a-local-model.md#la-longue-exécution-jamais-une-surprise) |
| `--format xlsx\|csv` | `inventory` | `xlsx` (par défaut) : un classeur avec les feuilles Fichiers et Résumé. `csv` : la feuille Fichiers seule, comme `plan.csv`. [Inventaire](reference-inventory.md#un-fichier-csv-à-la-place) |
| `--keep-empty-folders` | `sort` | Garder les dossiers sources que le tri laisse vides. [Trier, étape 7](sort/07-sort.md#les-dossiers-laissés-vides) |
| `--category NOM` | `album` | Les fichiers de cette catégorie, d'après le classeur modifié (un événement nommé dans le classeur donne son nom). [Trier, étape 11](sort/11-albums.md#choisir-ce-que-lalbum-rassemble) |
| `--event ÉVÉNEMENT` | `album` | Les fichiers de cet événement : son identifiant (feuille Événements) ou son nom. |
| `--rule NOM` | `album` | Les fichiers que l'entrée `[[classify.rules]]` de ce nom a décidés. |
| `--rating N` | `album` | Les fichiers qui ont au moins N étoiles (1 à 5) dans Windows, telles que l'audit les a lues (demande `/cache`). |
| `--workbook CHEMIN` | `album` | Le classeur de `classify` à lire ; celui du dernier `classify` par défaut. |
| `--apply` | `album` | Crée les liens ; sans cette option, `album` montre seulement ce qu'il rassemblerait. |

La plupart des options ont leur équivalent dans `config.toml` ([étape 7](clean/07-configuration-file.md)) ;
la ligne de commande l'emporte. Les règles de `classify` (`[[classify.rules]]`) n'ont pas
d'option : elles s'écrivent dans `config.toml` seulement ([trier, étape 6](sort/06-write-down-what-you-know.md)).

## L'aide intégrée

`cavo789/media-hygiene --help` et `cavo789/media-hygiene <commande> --help` documentent tout, dans
les deux langues (`--locale fr --help`). Voici ce qu'elles affichent :

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
│ --locale           <en|fr>                     Langue de l'interface.        │
│ --verbosity        <error|warning|info|debug>  Niveau de détail des          │
│                                                journaux.                     │
│ --color            <auto|always|never>         Quand utiliser les couleurs   │
│                                                (NO_COLOR est aussi           │
│                                                respecté).                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Analyser ───────────────────────────────────────────────────────────────────╮
│ audit        Trouve les doublons exacts et les fichiers cassés. Lecture      │
│              seule : montez les dossiers avec :ro.                           │
│ crosscheck   Compare un nouvel audit aux résultats de Czkawka : un second    │
│              avis, indépendant.                                              │
│ classify     Propose où ranger chaque photo et vidéo : année, événement,     │
│              catégorie. En lecture seule.                                    │
│ review-sort  Nommer les événements de la proposition de classify un par un,  │
│              dans votre navigateur.                                          │
│ places       Nommer vos lieux sur une carte des endroits où les photos ont   │
│              été prises ; enregistrés dans config.toml pour les règles       │
│              'place' et 'trip'.                                              │
│ inventory    Exporter vers Excel chaque photo et vidéo avec ce que les       │
│              audits en ont appris, depuis le cache seul : aucun fichier      │
│              n'est lu.                                                       │
│ history      Liste les exécutions et ce qu'elles ont fait.                   │
│ reports      Liste les rapports HTML des audits et nettoyages précédents.    │
│ config       Affiche chaque réglage, son origine, et les points de montage.  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Agir ───────────────────────────────────────────────────────────────────────╮
│ review       Écarter des photos de rafale, une série à la fois, au clavier   │
│              dans votre navigateur ; 'clean --decisions' les déplace         │
│              ensuite.                                                        │
│ clean        Audite, demande confirmation, puis supprime réellement les      │
│              copies en double (journalisé, annulable).                       │
│ sort         Déplacer les photos et vidéos comme le dit le classeur de       │
│              classify modifié (journalisé, annulable).                       │
│ album        Rassemble une sélection du plan de classify dans un dossier de  │
│              liens physiques : rien n'est copié ni déplacé (journalisé,      │
│              annulable).                                                     │
│ undo         Restaure chaque fichier d'une exécution, depuis la copie        │
│              conservée, la quarantaine ou là où il a été déplacé ; supprime  │
│              les liens d'un album.                                           │
│ purge        Supprime définitivement les fichiers cassés mis en quarantaine  │
│              par une exécution.                                              │
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

 Trouve les doublons exacts et les fichiers cassés. Lecture seule : montez les
 dossiers avec :ro.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Dossiers (remplacent folders.* de config.toml) ─────────────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Analyse (remplace scan.* de config.toml) ───────────────────────────────────╮
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

 Écarter des photos de rafale, une série à la fois, au clavier dans votre
 navigateur ; 'clean --decisions' les déplace ensuite.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --decisions          <path>              Fichier où les décisions sont       │
│                                          enregistrées, et repris au          │
│                                          lancement suivant. Un chemin        │
│                                          relatif se trouve dans le dossier   │
│                                          monté sur /reports. Par défaut :    │
│                                          decisions.json.                     │
│ --port               <int range> [x>=0]  Port de la page dans le conteneur ; │
│                                          publiez-le avec -p 127.0.0.1::8080  │
│                                          pour que Docker en choisisse un     │
│                                          libre sur votre ordinateur. Par     │
│                                          défaut : 8080.                      │
│ --help       -h                          Affiche ce message et quitte.       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Dossiers (remplacent folders.* de config.toml) ─────────────────────────────╮
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

 Audite, demande confirmation, puis supprime réellement les copies en double
 (journalisé, annulable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes        -y                    Ne pas demander de confirmation (remplace │
│                                    clean.confirm).                           │
│ --tier               <exact|near>  exact : supprime seulement les copies     │
│                                    identiques octet par octet. near :        │
│                                    déplace aussi les quasi-doublons (copies  │
│                                    redimensionnées ou recompressées, vidéos  │
│                                    réencodées) en quarantaine ; vérifiez-les │
│                                    d'abord dans le rapport. Par défaut :     │
│                                    exact.                                    │
│ --decisions          <path>        decisions.json téléchargé depuis un       │
│                                    rapport d'audit (paires de dossiers       │
│                                    inversées ou laissées telles quelles) ou  │
│                                    écrit par 'review' (photos de rafale      │
│                                    écartées). Un chemin relatif est lu dans  │
│                                    le dossier monté sur /reports. Le fichier │
│                                    est refusé si les dossiers, les paires ou │
│                                    les séries ont changé.                    │
│ --help       -h                    Affiche ce message et quitte.             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Dossiers (remplacent folders.* de config.toml) ─────────────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Analyse (remplace scan.* de config.toml) ───────────────────────────────────╮
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

 Liste les exécutions et ce qu'elles ont fait.

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

 Supprime définitivement les fichiers cassés mis en quarantaine par une
 exécution.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution dont la quarantaine est supprimée ; toutes    │
│                      par défaut.                                             │
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

 Liste les rapports HTML des audits et nettoyages précédents.

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

 Compare un nouvel audit aux résultats de Czkawka : un second avis,
 indépendant.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Dossiers (remplacent folders.* de config.toml) ─────────────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Analyse (remplace scan.* de config.toml) ───────────────────────────────────╮
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

 Propose où ranger chaque photo et vidéo : année, événement, catégorie. En
 lecture seule.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year                   <str>               Seulement les fichiers de cette │
│                                              année, ou de ces années : 2016  │
│                                              ou 2015-2017.                   │
│ --layout                 <str>               Où vont les fichiers sûrs, par  │
│                                              exemple '{year}/{month} -       │
│                                              {month_name}'.                  │
│ --target                 <str>               Dossier de l'hôte qui reçoit    │
│                                              l'arborescence ; sur place par  │
│                                              défaut.                         │
│ --leave                  <str>               Dossier de l'hôte jamais trié   │
│                                              (analysé et nettoyé comme       │
│                                              d'habitude).                    │
│ --carry-over             <str>               Classeur dont les modifications │
│                                              sont reprises ; celui du        │
│                                              dernier classify par défaut.    │
│ --no-carry-over                              Repartir de zéro : ne reprendre │
│                                              aucune modification d'un        │
│                                              classeur précédent.             │
│ --sample                 <int range> [x>=0]  Décrire ce nombre de photos     │
│                                              prises au hasard avec le modèle │
│                                              local, afficher le temps par    │
│                                              photo et l'estimation d'une     │
│                                              exécution complète, puis        │
│                                              s'arrêter.                      │
│ --no-describe                                Ne rien demander de nouveau au  │
│                                              modèle local : les règles       │
│                                              subject lisent les descriptions │
│                                              déjà dans le cache.             │
│ --yes            -y                          Décrire les photos sans         │
│                                              demander, quel que soit leur    │
│                                              nombre.                         │
│ --help           -h                          Affiche ce message et quitte.   │
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
│ --category          <str>                  Les fichiers de cette catégorie,  │
│                                            d'après le classeur modifié.      │
│ --event             <str>                  Les fichiers de cet événement :   │
│                                            son identifiant ou son nom.       │
│ --rule              <str>                  Les fichiers que la règle de      │
│                                            classify de ce nom a décidés.     │
│ --rating            <int range> [1<=x<=5]  Les fichiers qui ont au moins ces │
│                                            étoiles dans Windows (1 à 5).     │
│ --workbook          <str>                  Le classeur de classify à lire ;  │
│                                            celui du dernier classify par     │
│                                            défaut.                           │
│ --apply                                    Crée les liens ; sans cette       │
│                                            option, montre seulement ce que   │
│                                            l'album rassemble.                │
│ --help      -h                             Affiche ce message et quitte.     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>inventory --help</code></summary>

<!-- capture: help-inventory.txt -->
```text
 Utilisation : media-hygiene inventory [OPTIONS]

 Exporter vers Excel chaque photo et vidéo avec ce que les audits en ont
 appris, depuis le cache seul : aucun fichier n'est lu.

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

 Affiche chaque réglage, son origine, et les points de montage.

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

 Nommer vos lieux sur une carte des endroits où les photos ont été prises ;
 enregistrés dans config.toml pour les règles 'place' et 'trip'.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=0]  Port de la page dans le conteneur ;      │
│                                     publiez-le avec -p 127.0.0.1::8080 pour  │
│                                     que Docker en choisisse un libre sur     │
│                                     votre ordinateur. Par défaut : 8080.     │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
