# `clean` : mettre les copies en trop de côté

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `clean` · 🇬🇧 [English](../../en/commands/clean.md)

## En bref

**Libérer la place que prennent vos photos en double, en sécurité : les copies en trop sont
mises de côté, jamais effacées, et tout peut être remis en place.**

`clean` refait l'audit, vous montre ce qu'il va faire, **demande**, puis déplace les copies en
trop en [quarantaine](../reference-glossary.md#quarantaine), après avoir comparé chacune octet par octet avec la copie gardée. `undo`
remet tout en place ; la place n'est libérée que quand vous videz la quarantaine avec `purge`.

**Quand** : après un [`audit`](audit.md) dont vous avez lu et approuvé les paires de dossiers.

**Essayer** :

```powershell
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit : déplace en quarantaine les copies en trop, les fichiers illisibles et les fichiers compagnons orphelins ; supprime les fichiers vides (0 octet). |
| Il faut | Vos dossiers **sans** `:ro`, `/journal` et `/quarantine` (des dossiers à vous). |
| Conseillé | `/cache`, `/reports`, `/config`. |
| Écrit | Le journal de l'exécution, la quarantaine, le rapport de nettoyage. |
| Annuler | [`undo`](undo.md) restaure chaque fichier de l'exécution. |
| Avec `mh` | `mh clean` : vos dossiers sont montés en écriture pour cette commande seulement. |

## Lancer

Créez une fois le journal et la quarantaine, puis lancez la commande de votre audit sans `:ro`,
avec ces deux dossiers et `clean` au lieu d'`audit` :

```powershell
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

Il montre le résumé et les paires de dossiers, puis demande : *❓ Déplacer 32 copies en double
(14,0 Mo) en quarantaine et traiter 3 fichiers cassés ? [o/N]*. Toute autre réponse que `o`
arrête là, et rien ne change. Avec `o`, une ligne sous la barre nomme chaque fichier et ce qui
lui arrive ; le tableau final compte ce qui a été déplacé, ignoré et en échec.

## Ce qui arrive à chaque fichier

| Fichier | Ce que fait `clean` |
|---|---|
| Copie en trop d'une photo ou d'une vidéo | **Déplacée** en quarantaine, juste après une dernière comparaison octet par octet avec la copie gardée. La moindre différence ? Ignorée. |
| Fichier vide (0 octet) | Supprimé : il ne contient rien (`undo` le recrée). |
| Fichier illisible | Déplacé en quarantaine. |
| [Fichier compagnon](../reference-sidecars.md) orphelin | Déplacé en quarantaine. |
| Quasi-doublons, photos de rafale | Pas touchés, sauf si vous le demandez (`--tier`, `--decisions`). |
| Un fichier que vous aviez mis de côté, revenu depuis (une sauvegarde de téléphone) | Remis en quarantaine, compté sur une ligne à part. [Étape 9 du nettoyage](../clean/09-undo-history-purge.md#ce-que-vous-avez-mis-de-côté-reste-de-côté) |
| Fichiers d'un dossier protégé | Pas touchés, jamais. |

La quarantaine garde les chemins d'origine sous un dossier par exécution :
`quarantine\<exécution>\d\Ancien disque\2020\IMG_1203.jpg`.

## Options

| Option | Rôle |
|---|---|
| `--tier exact` | Par défaut : seulement les copies identiques octet par octet. |
| `--tier near` | Aussi les quasi-doublons et vidéos réencodées **sûrs**, et les groupes décidés avec `review --near`. [Étape 11 du nettoyage](../clean/11-near-duplicates.md#les-groupes-sûrs-et-ceux-à-vérifier) |
| `--tier near-all` | Tous les quasi-doublons, tels que le rapport les montre : regardez-les d'abord. |
| `--decisions [FICHIER]` | Applique les choix faits dans le navigateur : paires de dossiers d'un rapport ([étape 12 du nettoyage](../clean/12-decide-pair-by-pair.md)), photos de rafale écartées et quasi-doublons décidés avec [`review`](review.md), photos mises de côté dans [`search`](search.md#mettre-des-photos-de-côté). Seule, elle lit `decisions.json` dans `/reports`. |
| `--yes`, `-y` | Ne pas demander (indispensable sans `-it`). |
| `--delete` | Supprime pour de bon les copies exactes au lieu de les déplacer ; `undo` les reconstruit depuis la copie gardée. [Étape 8 du nettoyage](../clean/08-clean.md#besoin-de-la-place-tout-de-suite----delete) |
| `--prefer`, `--protect`, `--exclude`, `--exclude-name`, `--ext` | Comme pour [`audit`](audit.md#options) : donnez à `clean` les mêmes que pour l'audit que vous avez lu. |

## Exemples

```powershell
# Seulement les copies identiques (par défaut)
cavo789/media-hygiene --locale fr clean

# Aussi les quasi-doublons sûrs, et les rafales et groupes décidés dans review
cavo789/media-hygiene --locale fr clean --tier near --decisions

# Un script, une tâche planifiée : aucune question
cavo789/media-hygiene --locale fr clean --yes
```

(chacune avec la même partie `docker run … -v …` que ci-dessus)

## Bon à savoir

- **Commencez petit** : un sous-dossier, vérifiez, puis élargissez. Mettez OneDrive, Google
  Drive ou Dropbox en pause pendant le nettoyage.
- **Des refus qui vous protègent** : `clean` s'arrête avant l'analyse sans `/journal` ni
  `/quarantine`, avec un dossier en `:ro`, avec un dossier où il ne peut pas écrire, ou avec un
  dossier de l'outil placé dans un dossier de photos. Le message dit lequel.
- **Interrompu ?** Ctrl+C, une coupure de courant : chaque action est écrite dans le journal avant
  et après avoir eu lieu, donc `undo` restaure encore ce qui a été fait.
- **Une fois appliqué**, `decisions.json` est archivé sous `decisions.applied-<run>.json` : après
  un `undo`, `--decisions` avec ce nom applique à nouveau les mêmes choix.
- Si [Czkawka](crosscheck.md) a donné son avis, `clean` rappelle son verdict avant de demander.
- `confirm = false` dans la section `[clean]` de `config.toml` revient à `--yes`, à chaque fois.

## Pour aller plus loin

- [8. Nettoyer](../clean/08-clean.md), [9. Annuler, historique, purge](../clean/09-undo-history-purge.md)
- [10. Rafales](../clean/10-review-bursts.md), [11. Quasi-doublons](../clean/11-near-duplicates.md),
  [12. Décider paire par paire](../clean/12-decide-pair-by-pair.md)
- [Comment vos photos restent en sécurité](../reference-safety.md) : chaque vérification faite
  avant qu'un fichier bouge.
- Ensuite : [`history`](history.md) liste l'exécution, [`undo`](undo.md) l'annule,
  [`purge`](purge.md) libère la place.

## L'aide intégrée

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

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
