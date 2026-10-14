# `audit` : trouver les doublons et les fichiers cassés

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `audit` · 🇬🇧 [English](../../en/commands/audit.md)

## En bref

**Savoir, sans aucun risque, combien de copies vos dossiers contiennent et quelle place elles
prennent.**

`audit` examine chaque photo, fichier RAW et vidéo des dossiers que vous montez, et vous dit ce
qu'il trouve : copies identiques, fichiers cassés, [fichiers compagnons orphelins](../reference-glossary.md#fichier-compagnon-orphelin), quasi-doublons
et [rafales](../reference-glossary.md#rafale). Il ne modifie rien.

**Quand** : la toute première fois ; puis avant chaque `clean` (avec les mêmes options, pour
vérifier quelle copie reste), et après avoir ajouté des photos ou un disque.

**Essayer** :

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene --locale fr audit
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`, le système lui-même interdit alors tout changement. |
| Il faut | Vos dossiers, un `-v` chacun (`/data/<lecteur>/<chemin>`). |
| Conseillé | `/cache` (les audits suivants prennent quelques secondes), `/reports` (le rapport HTML), `/config` (votre `config.toml`). |
| Écrit | Le cache, et un rapport dans `/reports/<date>-audit/` quand `/reports` est monté. |
| Annuler | Rien à annuler : rien n'a changé. |
| Avec `mh` | `mh audit` ([`launcher`](launcher.md)). |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr audit
```

Il affiche, dans cet ordre :

1. **Résumé de l'audit** : fichiers analysés, groupes de fichiers identiques, copies en trop,
   place à libérer, fichiers cassés, quasi-doublons, rafales.
2. **Dossiers partageant des fichiers identiques** : une phrase par paire de dossiers, le
   dossier qui garde ses copies en premier.
3. **Ce que vous pouvez faire** : trois lignes au plus (copies identiques, quasi-doublons,
   rafales), chacune avec ce qu'elle rapporte et ce qu'elle vous coûte.
4. **👉 Et maintenant** : l'étape suivante, en commande complète prête à coller, puis une ou deux
   astuces 💡.

[Votre premier audit](../start/01-first-audit.md#lire-le-résultat) explique chaque ligne.

## Options

| Option | Rôle |
|---|---|
| `--prefer CHEMIN` | Dossier dont les copies sont gardées en priorité ; à répéter, l'ordre compte. [Étape 5 du nettoyage](../clean/05-choose-the-kept-copy.md#préférer-un-dossier) |
| `--protect CHEMIN` | Dossier jamais modifié ; ses fichiers sont les copies gardées. [Étape 5 du nettoyage](../clean/05-choose-the-kept-copy.md#protéger-un-dossier) |
| `--exclude CHEMIN` | Dossier jamais analysé, comme une vraie sauvegarde. [Étape 5 du nettoyage](../clean/05-choose-the-kept-copy.md#exclure-un-dossier) |
| `--exclude-name NOM` | Nom de dossier jamais analysé, où qu'il soit (`--exclude-name Thumbnails,.Trash-*`). [Étape 5 du nettoyage](../clean/05-choose-the-kept-copy.md#ignorer-un-nom-de-dossier-sur-tous-les-disques) |
| `--full` | Relire tous les dossiers, même ceux inchangés depuis le dernier audit (repris du cache sinon) : pour une photo modifiée sur place par un autre programme. [Étape 2](../start/02-keep-the-cache.md#ce-qui-change) |
| `--ext EXT` | Seulement ces catégories ou extensions (`--ext photo,video`, `--ext heic`) ; d'autres types de fichiers aussi (`--ext pdf,docx`). [Étape 6 du nettoyage](../clean/06-file-types.md) |
| `--people` | Chercher ensuite les visages des photos pas encore examinées, après avoir dit combien de temps cela prend et demandé ([Les personnes](../reference-people.md#pendant-laudit--audit---people)) ; `with_audit = true` dans `[people]` le fait à chaque audit. |
| `--yes`, `-y` | Avec `--people` : ne pas demander. Sans terminal (pas de `-it`), `--people` en a besoin : rien n'attend de réponse. |

Les chemins s'écrivent à la façon de Windows (`C:\Photos\Famille`), comme dans l'Explorateur.
Chaque option a sa ligne dans `config.toml` ([étape 7 du nettoyage](../clean/07-configuration-file.md)) :
écrivez-la une fois, la ligne de commande l'emporte toujours.

## Exemples

```powershell
# Garder d'abord les copies du dossier du téléphone principal
cavo789/media-hygiene --locale fr audit --prefer "C:\Photos\Téléphone"

# Laisser une vraie sauvegarde hors de l'analyse
cavo789/media-hygiene --locale fr audit --exclude "D:\Sauvegarde"

# Seulement les vidéos
cavo789/media-hygiene --locale fr audit --ext video

# Tout ce que les fichiers disent d'eux-mêmes (dates, GPS, formats), après le résumé,
# et le temps pris par chaque étape (liste, vérifications, empreintes, quasi-doublons…)
cavo789/media-hygiene --locale fr --verbosity verbose audit

# Puis les visages, une fois le temps accepté (il faut /cache)
cavo789/media-hygiene --locale fr audit --people
```

(chacune avec la même partie `docker run … -v …` que ci-dessus)

## Bon à savoir

- **Ctrl+C** arrête à tout moment, sans message d'erreur : rien n'a changé.
- **Le premier audit** d'une grande photothèque peut être long ; avec
  [le cache](../start/02-keep-the-cache.md), les suivants ne lisent que les fichiers nouveaux ou
  modifiés.
- **Montez chaque dossier une seule fois** : `C:\Photos` contient déjà `C:\Photos\2019`. Un
  dossier monté deux fois est refusé, plutôt que de prendre une photo pour une copie d'elle-même.
- **Une vraie sauvegarde** doit rester une copie : laissez-la de côté, ou `--exclude`-la.
- Le résumé des **quasi-doublons** et des **rafales** n'est qu'une prévision : un `clean` simple
  n'y touche jamais.

## Pour aller plus loin

- [1. Votre premier audit](../start/01-first-audit.md), [2. Garder le cache](../start/02-keep-the-cache.md),
  [3. Plusieurs dossiers et disques](../start/03-several-folders.md)
- [4. Le rapport HTML](../clean/04-html-report.md) : les images, les paires de dossiers, la preuve.
- Ensuite : [`clean`](clean.md) met les copies en trop de côté ; [`review`](review.md) trie les rafales.

## L'aide intégrée

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
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --full              Relire tous les dossiers, même ceux qui n'ont pas changé │
│                     depuis le dernier audit : pour une photo modifiée sur    │
│                     place par un autre programme.                            │
│ --people            Chercher ensuite les visages des photos pas encore       │
│                     examinées (comme 'people'), après avoir dit combien de   │
│                     temps cela prend et demandé.                             │
│ --yes     -y        Avec --people : ne pas demander, continuer.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
