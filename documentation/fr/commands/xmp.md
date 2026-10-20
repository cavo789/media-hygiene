# `xmp` : emporter les mots avec les photos

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `xmp` · 🇬🇧 [English](../../en/commands/xmp.md)

## En bref

**Voir vos mots dans digiKam, darktable, Lightroom ou Immich, sans aucun changement dans les
photos elles-mêmes.**

Les mots de [`tags`](tags.md) vivent dans le [cache](../reference-glossary.md#cache) de cet outil. `xmp` les écrit dans des
**fichiers compagnons** : de petits fichiers `.xmp` à côté des photos (`IMG_1.jpg.xmp` à côté de
`IMG_1.jpg`). Sans `--apply`, il montre seulement ce qu'il écrirait.

**Quand** : après [`tags`](tags.md), et à nouveau après chaque nouveau passage de `tags`.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr xmp
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit avec `--apply` seulement : écrit des fichiers compagnons `.xmp` à côté des photos, jamais dans une photo. |
| Il faut | `/cache` (les mots) ; avec `--apply`, vos dossiers **sans** `:ro` et `/journal`. |
| Conseillé | `/quarantine` (un fichier compagnon d'une autre application y est copié avant d'être complété), `/config` (`[tags] xmp_sources`). |
| Écrit | Les fichiers compagnons, le journal. |
| Annuler | [`undo <exécution>`](undo.md) retire les fichiers compagnons qu'il a créés et remet les autres octet pour octet. |
| Avec `mh` | `mh xmp`, `mh xmp --apply`. |

## Lancer

Voyez d'abord ce qu'il écrirait (les dossiers peuvent rester en `:ro`), puis ajoutez `--apply` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr xmp --apply
```

## Ce qui est écrit

- Les mots des sources de `xmp_sources` (`vision` et `place` par défaut) dans `dc:subject` ; la
  phrase du modèle dans `dc:description`.
- Avec `place` : la ville dans `photoshop:City`, son pays dans `photoshop:Country`, votre lieu
  personnel dans `Iptc4xmpCore:Location`. Un nom qui est deux de ces lieux à la fois (Luxembourg,
  ville et pays ; un lieu à vous qui porte le nom de sa ville) remplit les deux champs.
- Avec `person` (à demander, jamais par défaut) : les noms des personnes sur la photo dans
  `Iptc4xmpExt:PersonInImage` ; `xmp` prévient d'abord, puisque les noms voyagent alors avec les
  photos.
- **Un fichier compagnon déjà là est complété, jamais remplacé** : ses modifications, ses autres
  propriétés et ses propres mots restent. Un champ qu'une autre application a rempli garde sa valeur.

## Une position d'après la ville du dossier

Beaucoup de photos n'ont pas de position GPS, mais leur dossier dit où elles ont été prises :
`2019/Douarnenez`, `Saint-Jean de Luz`. Avec cette ligne dans `config.toml`, `xmp` donne à chacune
de ces photos **la position du centre de la ville**, pour qu'un gestionnaire de photos la montre
sur sa carte :

```toml
[tags]
xmp_folder_gps = true
```

- **Approximatif** : le centre de la ville, pas la plage où la photo a été prise. C'est pourquoi
  c'est désactivé par défaut.
- **Une position à vous** : un dossier placé sur la carte de [`places`](places.md) (**Enregistrer
  cette position**, `[[places.folders]]`) reçoit cette position au lieu du centre de la ville ; le
  dossier le plus proche au-dessus d'une photo décide.
- **Quels dossiers** : les mêmes que pour la [règle `folder_town`](../sort/09-places-from-gps.md) de
  `classify`, qu'elle soit active ou non : le nom entier du dossier est une ville d'au moins 5 000
  habitants (sans tenir compte des majuscules, des accents ni des traits d'union), jamais un mois
  ni une saison, `folder_town_ignore` respecté.
- **Jamais par-dessus une vraie position** : une photo qui a sa propre position GPS (ou celle de
  son `.json` Google Takeout) ne reçoit rien ; une position qu'une autre application a écrite dans
  le `.xmp` est gardée.
- Écrite dans `exif:GPSLatitude` / `exif:GPSLongitude` (par exemple `48,5.7252N`), avec la ville
  et son pays dans `photoshop:City` / `photoshop:Country` quand les mots n'en donnent pas.
  exiftool lit ces positions ; si votre gestionnaire de photos lit une position dans un `.xmp` :
  à vérifier avec lui.
- L'essai à blanc dit combien de photos reçoivent une position, par ville : *37 photos sans GPS
  reçoivent la position de la ville de leur dossier (son centre, approximatif) : Douarnenez 25,
  Saint-Jean-de-Luz 12.*
- Désactivé à nouveau, le `xmp --apply` suivant retire les positions qu'il avait écrites ;
  `undo` aussi.

## Options

| Option | Rôle |
|---|---|
| `--path CHEMIN` | Seulement les photos sous ce dossier (chemin de l'hôte) ; à répéter pour plusieurs. |
| `--apply` | Écrire les fichiers compagnons ; sans cette option, montrer seulement ce qui serait écrit. |

## Bon à savoir

- **Relancez-le** après `tags` : les mots qu'il avait écrits et ne donne plus sont retirés, un mot
  que vous avez retiré dans une autre application n'est pas remis, un fichier compagnon déjà à jour
  n'est pas réécrit.
- **Laissés de côté** : les dossiers protégés, et les fichiers qui ont une copie identique (lancez
  d'abord [`clean`](clean.md) : seule la copie gardée reçoit un fichier compagnon).
- **Sûr** : chaque fichier compagnon est journalisé, écrit dans un fichier temporaire puis renommé,
  relu et vérifié.
- Un fichier compagnon écrit par `xmp` seul ne compte pas comme des retouches quand `clean` choisit
  la copie gardée.

## Pour aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
- [Les tags : emporter les mots avec les photos](../reference-tags.md#emporter-les-mots-avec-les-photos--xmp)
- [Fichiers compagnons](../reference-sidecars.md)

## L'aide intégrée

<details>
<summary><code>xmp --help</code></summary>

<!-- capture: help-xmp.txt -->
```text
 Utilisation : media-hygiene xmp [OPTIONS]

 Écrire les mots de 'tags' dans des fichiers compagnons .xmp à côté des photos,
 pour digiKam, darktable, Lightroom ou Immich ; jamais dans une photo
 (journalisé, annulable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path           <str>  Seulement les photos sous ce dossier (chemin de      │
│                         l'hôte, tel que vous l'avez monté) ; à répéter pour  │
│                         plusieurs. Par défaut : tous les fichiers de         │
│                         l'index.                                             │
│ --apply                 Écrire les fichiers compagnons ; sans cette option,  │
│                         seulement montrer ce qui serait écrit.               │
│ --help   -h             Affiche ce message et quitte.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque, monté en lecture  │
│                        seule : jamais modifié, et jamais refusé pour cela    │
│                        (mh passe vos sauvegardes). Répétable.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
