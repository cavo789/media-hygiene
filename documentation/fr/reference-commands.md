# Commandes et options

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-commands.md)

Chaque commande, chaque option. Le [guide](README.md#pour-commencer) les présente une à une ;
cette page les rassemble.

## Commandes

| Commande | Rôle | Guide |
|---|---|---|
| `audit` | Trouve les doublons exacts et les fichiers cassés. N'écrit jamais dans vos dossiers. | [1](start/01-first-audit.md) |
| `review` | Analyse, puis trie les rafales dans votre navigateur, une à la fois, au clavier. N'écrit jamais dans vos dossiers. | [10](clean/10-review-bursts.md) |
| `clean` | Audite, demande confirmation, puis supprime les copies en double et les fichiers vides, et met en quarantaine les fichiers illisibles et les fichiers compagnons orphelins. | [8](clean/08-clean.md) |
| `undo [EXÉCUTION]` | Restaure chaque fichier d'une exécution (la plus récente par défaut). | [9](clean/09-undo-history-purge.md) |
| `history` | Liste les exécutions : leur commande, fichiers supprimés, espace libéré, quarantaine, restaurations. | [9](clean/09-undo-history-purge.md) |
| `purge [EXÉCUTION]` | Supprime définitivement la quarantaine d'un nettoyage (de tous par défaut). | [9](clean/09-undo-history-purge.md) |
| `reports [--prune N]` | Liste les rapports et régénère `index.html` ; `--prune N` garde les N plus récents. | [4](clean/04-html-report.md) |
| `crosscheck` | Refait l'audit, puis le compare aux résultats de Czkawka, un détecteur de doublons indépendant. | [13](clean/13-second-opinion.md) |
| `classify` | Propose où ranger chaque photo et vidéo : année, événement, catégorie. N'écrit jamais dans vos dossiers. | [4](sort/04-classify.md) |
| `config` | Affiche chaque réglage, son origine, et l'état de chaque point de montage. | [7](clean/07-configuration-file.md) |

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
| `--ext EXT` | `audit`, `clean`, `crosscheck` | N'analyse que ces extensions (`--ext png,webp`) ; toutes celles des photos, RAW et vidéos par défaut. D'autres types aussi (`--ext pdf,docx`). [Étape 6](clean/06-file-types.md) |
| `--yes`, `-y` | `clean`, `purge` | Ne pas demander de confirmation. |
| `--tier exact\|near` | `clean` | `exact` (par défaut) : seulement les copies identiques octet par octet. `near` : déplace aussi les quasi-doublons en quarantaine. [Étape 11](clean/11-near-duplicates.md) |
| `--decisions FICHIER` | `clean`, `review` | `clean` : applique les décisions sur les paires de dossiers d'un rapport et les photos de rafale écartées avec `review`. `review` : le fichier où les choix sont enregistrés, `decisions.json` par défaut. Un chemin relatif est lu dans `/reports`. [Étape 10](clean/10-review-bursts.md), [étape 12](clean/12-decide-pair-by-pair.md) |
| `--port PORT` | `review` | Port de la page dans le conteneur, `8080` par défaut ; publiez-le avec `-p 127.0.0.1::8080`. |
| `--prune N` | `reports` | Garde les N rapports les plus récents, supprime les autres. |

La plupart des options ont leur équivalent dans `config.toml` ([étape 7](clean/07-configuration-file.md)) ;
la ligne de commande l'emporte.

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
│ audit       Trouve les doublons exacts et les fichiers cassés. Lecture seule │
│             : montez les dossiers avec :ro.                                  │
│ crosscheck  Compare un nouvel audit aux résultats de Czkawka : un second     │
│             avis, indépendant.                                               │
│ classify    Propose où ranger chaque photo et vidéo : année, événement,      │
│             catégorie. En lecture seule.                                     │
│ history     Liste les exécutions et ce qu'elles ont fait.                    │
│ reports     Liste les rapports HTML des audits et nettoyages précédents.     │
│ config      Affiche chaque réglage, son origine, et les points de montage.   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Agir ───────────────────────────────────────────────────────────────────────╮
│ review      Écarter des photos de rafale, une série à la fois, au clavier    │
│             dans votre navigateur ; 'clean --decisions' les déplace ensuite. │
│ clean       Audite, demande confirmation, puis supprime réellement les       │
│             copies en double (journalisé, annulable).                        │
│ undo        Restaure chaque fichier d'une exécution, depuis la copie         │
│             conservée, la quarantaine ou l'endroit où il a été déplacé.      │
│ purge       Supprime définitivement les fichiers cassés mis en quarantaine   │
│             par une exécution.                                               │
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
│ --ext        <str>  N'analyse que les fichiers ayant ces extensions, p. ex.  │
│                     --ext png,webp (répétable). D'autres types aussi, comme  │
│                     --ext pdf,docx : leurs copies sont déplacées en          │
│                     quarantaine. Par défaut : toutes les extensions des      │
│                     photos, RAW et vidéos : 3g2, 3gp, arw, avi, avif, bmp,   │
│                     cr2, cr3, dng, flv, gif, heic, heif, jpe, jpeg, jpg,     │
│                     m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, nef, orf, pef, │
│                     png, raf, rw2, srw, tif, tiff, ts, webm, webp, wmv.      │
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
│                                    redimensionnées ou recompressées) en      │
│                                    quarantaine ; vérifiez-les d'abord dans   │
│                                    le rapport. Par défaut : exact.           │
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
│ --ext        <str>  N'analyse que les fichiers ayant ces extensions, p. ex.  │
│                     --ext png,webp (répétable). D'autres types aussi, comme  │
│                     --ext pdf,docx : leurs copies sont déplacées en          │
│                     quarantaine. Par défaut : toutes les extensions des      │
│                     photos, RAW et vidéos : 3g2, 3gp, arw, avi, avif, bmp,   │
│                     cr2, cr3, dng, flv, gif, heic, heif, jpe, jpeg, jpg,     │
│                     m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, nef, orf, pef, │
│                     png, raf, rw2, srw, tif, tiff, ts, webm, webp, wmv.      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Utilisation : media-hygiene undo [OPTIONS] [run_id]

 Restaure chaque fichier d'une exécution, depuis la copie conservée, la
 quarantaine ou l'endroit où il a été déplacé.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution à annuler (voir 'history') ; la plus récente  │
│                      par défaut.                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
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
│ --ext        <str>  N'analyse que les fichiers ayant ces extensions, p. ex.  │
│                     --ext png,webp (répétable). D'autres types aussi, comme  │
│                     --ext pdf,docx : leurs copies sont déplacées en          │
│                     quarantaine. Par défaut : toutes les extensions des      │
│                     photos, RAW et vidéos : 3g2, 3gp, arw, avi, avif, bmp,   │
│                     cr2, cr3, dng, flv, gif, heic, heif, jpe, jpeg, jpg,     │
│                     m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, nef, orf, pef, │
│                     png, raf, rw2, srw, tif, tiff, ts, webm, webp, wmv.      │
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
│ --year            <str>  Seulement les fichiers de cette année, ou de ces    │
│                          années : 2016 ou 2015-2017.                         │
│ --layout          <str>  Où vont les fichiers sûrs, par exemple              │
│                          '{year}/{month} - {month_name}'.                    │
│ --target          <str>  Dossier de l'hôte qui reçoit l'arborescence ; sur   │
│                          place par défaut.                                   │
│ --leave           <str>  Dossier de l'hôte jamais trié (analysé et nettoyé   │
│                          comme d'habitude).                                  │
│ --help    -h             Affiche ce message et quitte.                       │
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
