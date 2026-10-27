# 6. Seulement certains types de fichiers

[Documentation](../README.md) › Nettoyer, étape 6 sur 14 · 🇬🇧 [English](../../en/clean/06-file-types.md)

Par défaut, l'outil analyse toutes les photos, tous les fichiers RAW et toutes les vidéos, et
rien d'autre. `--ext` restreint l'analyse à certains types ; l'audit liste les autres fichiers
de vos dossiers de photos.

## Ce qui est analysé par défaut

Les fichiers sont reconnus à leur extension, quelle que soit sa casse :

| Type | Extensions |
|---|---|
| Images | avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif, tiff, webp |
| RAW (décodés par LibRaw, aperçu tiré du JPEG intégré par l'appareil) | arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw |
| Vidéos | 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, ts, webm, wmv |

`media-hygiene config` les liste aussi, comme catégories intégrées `photo` (images), `raw`,
`video` et `media` (les trois). Les [fichiers compagnons](../reference-sidecars.md)
(`.xmp`, `.aae`, `.thm`) ne sont pas analysés seuls : ils suivent leur photo.

## Seulement certains types

`--ext` prend une ou plusieurs catégories ou extensions, séparées par des virgules ou répétées
(`--ext heic --ext mp4`) ; la casse n'importe pas. Une catégorie nomme toute une liste :
`--ext video` analyse les 15 extensions de vidéos, `--ext photo,raw` toutes les images mais
aucune vidéo. Par exemple, seulement les photos de l'iPhone et les vidéos :

```powershell
mh audit --ext heic,video
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr audit --ext heic,video
```

</details>

L'audit commence par dire ce qu'il analyse :

<!-- capture: audit-ext.txt|Seuls sont|└ -->
```text
⚠️  Seuls sont analysés : heic, video.
18 dossiers inchangés repris de l'index, 6 relus.
💡 Une photo modifiée sur place par un autre programme ? 'audit --full' relit
tous les dossiers (c'est fait de toute façon pour ceux listés il y a 7 jours).

♻️  Rien de nouveau ni de modifié depuis le dernier audit : 10 fichiers repris
du cache.
Résumé de l'audit
┌──────────────────────────────────────────────────────────┬────────┐
│ Fichiers média analysés                                  │     10 │
│ Groupes de fichiers identiques                           │      4 │
│ Copies en trop, à mettre de côté                         │      4 │
│ Espace libérable                                         │ 5,9 Mo │
│ Fichiers cassés (vides ou illisibles)                    │      1 │
│ Vidéos réencodées (déplacées seulement avec --tier near) │      1 │
│ Durée                                                    │    0 s │
└──────────────────────────────────────────────────────────┴────────┘
```

Une valeur sans point est une catégorie quand l'une porte ce nom, sinon une extension :
`--ext heic` désigne l'extension. Seules les extensions de photos, RAW et vidéos sont acceptées :
`--ext pdf` est refusé. Un nom proche d'une catégorie (`--ext photos`) est refusé,
avec la bonne orthographe : sans cette vérification, il n'analyserait rien, sans rien dire.

## Vos propres catégories

Nommez les listes que vous tapez souvent dans le [fichier de configuration](07-configuration-file.md),
sous `[scan.categories]` :

```toml
[scan.categories]
telephone = ["heic", "jpg", "mov", "mp4"]
web = ["png", "webp", "gif"]
```

Ensuite `--ext telephone`, ou `extensions = ["telephone"]` dans `[scan]`. Un nom contient des
lettres, des chiffres, `-` et `_` ; une catégorie liste des extensions, jamais d'autres
catégories ; `photo`, `raw`, `video` et `media` ne peuvent pas être redéfinies. Une catégorie
ne fait que nommer une liste : chaque fichier reste traité selon son extension.

## Fichiers qui ne sont ni des photos ni des vidéos

Un zip, un document Word ou un PDF copié parmi les photos de famille n'est pas analysé, mais
l'audit le compte : une ligne à la fin, rien quand il n'y en a pas.

```text
🧹 312 fichiers qui ne sont ni des photos ni des vidéos (zip, docx, pdf, …) occupent 4,2 Go
dans vos dossiers de photos : voyez « Fichiers intrus » dans le rapport.
```

La section **🧹 Fichiers intrus** du rapport donne les totaux par extension et les dossiers les
plus lourds ; `intruders.csv`, à côté de `plan.csv`, liste chaque fichier (chemin, dossier,
extension, taille, date). Les compter ne coûte aucune lecture disque en plus : l'audit liste
de toute façon chaque dossier.

- **Rien n'est déplacé** : un document peut compter. Supprimez-les ou déplacez-les vous-même,
  ou gardez-les.
- **Les dossiers protégés et de sauvegarde sont laissés de côté**, comme les dossiers exclus
  (jamais lus).
- **Les compagnons ne sont jamais des intrus** : ce qui accompagne une photo ou un dossier de
  photos, `.xmp`, `.aae`, `.thm`, `.json` (Google Takeout), `Thumbs.db`, `desktop.ini`,
  `.DS_Store`, `.picasa.ini`, `.nomedia`, `.lrv` et `.srt` (GoPro, drones). Changez la liste dans `[scan] companions` du
  [fichier de configuration](07-configuration-file.md) : un nom, ou une extension avec son
  point, sans tenir compte de la casse, par exemple
  `companions = [".xmp", ".json", "thumbs.db", ".lrv"]`.

---

← [5. Choisir la copie gardée](05-choose-the-kept-copy.md) · [Documentation](../README.md) · Suivant : **[7. Le fichier de configuration](07-configuration-file.md)** →
