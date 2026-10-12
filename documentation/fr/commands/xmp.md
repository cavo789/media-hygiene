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
- **Un fichier compagnon déjà là est complété, jamais remplacé** : ses modifications, ses autres
  propriétés et ses propres mots restent. Un champ qu'une autre application a rempli garde sa valeur.

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
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
