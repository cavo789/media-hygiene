# 6. Seulement certains types de fichiers

[Documentation](../README.md) › Nettoyer, étape 6 sur 13 · 🇬🇧 [English](../../en/clean/06-file-types.md)

Par défaut, l'outil analyse toutes les photos, tous les fichiers RAW et toutes les vidéos, et
rien d'autre. `--ext` restreint l'analyse à certains types, ou l'élargit à d'autres fichiers.

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
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr audit --ext heic,video
```

L'audit commence par dire ce qu'il analyse :

<!-- capture: audit-ext.txt|Seuls sont|└ -->
```text
⚠️  Seuls sont analysés : heic, video.

Résumé de l'audit
┌───────────────────────────────────────┬────────┐
│ Fichiers média analysés               │      9 │
│ Groupes de fichiers identiques        │      4 │
│ Copies en trop, supprimables          │      4 │
│ Espace libérable                      │ 5,9 Mo │
│ Fichiers cassés (vides ou illisibles) │      1 │
│ Durée                                 │    0 s │
└───────────────────────────────────────┴────────┘
```

Une valeur sans point est une catégorie quand l'une porte ce nom, sinon une extension :
`--ext pdf` désigne l'extension. Écrivez le point pour demander une extension qui porte aussi le
nom d'une catégorie : `--ext .raw`. Un nom proche d'une catégorie (`--ext photos`) est refusé,
avec la bonne orthographe : sans cette vérification, il n'analyserait rien, sans rien dire.

## Vos propres catégories

Nommez les listes que vous tapez souvent dans le [fichier de configuration](07-configuration-file.md),
sous `[scan.categories]` :

```toml
[scan.categories]
documents = ["pdf", "docx", "doc", "odt", "txt"]
web = ["png", "webp", "svg"]
```

Ensuite `--ext documents`, ou `extensions = ["documents"]` dans `[scan]`. Un nom contient des
lettres, des chiffres, `-` et `_` ; une catégorie liste des extensions, jamais d'autres
catégories ; `photo`, `raw`, `video` et `media` ne peuvent pas être redéfinies. Une catégorie
ne fait que nommer une liste : chaque fichier reste traité selon son extension. Avec `web`
ci-dessus, les fichiers PNG sont des images (vérifiées, prévisualisées, leurs copies supprimées)
et les fichiers SVG d'autres fichiers (seulement comparés, leurs copies déplacées en quarantaine,
voir ci-dessous).

## Autres types de fichiers

L'outil est fait pour les photos et les vidéos, mais `--ext` accepte aussi d'autres extensions,
par exemple pour trouver les documents en double d'un dossier familial. `clean`
([étape 8](08-clean.md)) a alors besoin du montage `/quarantine` :

```powershell
docker run --rm -it `
  -v "C:\Users\Moi\Documents:/data/c/Users/Moi/Documents" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean --ext pdf,docx
```

Ces fichiers sont traités avec plus de précautions que les photos. Pour une photo, le dossier
n'est qu'une façon de ranger ; pour un document ou un programme, **l'endroit où se trouve le
fichier peut être ce qui le fait fonctionner** : un `LICENSE`, un `__init__.py` ou un modèle
identique dans deux projets est normal, et supprimer « la copie » casse l'un d'eux.

- **Seulement comparés**, octet par octet : jamais décodés (les images passent par Pillow, les
  fichiers RAW par LibRaw, les vidéos par `ffprobe` ; les autres types n'ont aucune
  vérification), pas d'aperçu, pas de quasi-doublons. Un fichier vide n'est jamais « cassé » :
  ce peut être un marqueur dont un programme a besoin.
- **Leurs copies sont déplacées en quarantaine**, jamais supprimées : `clean` refuse de
  s'exécuter sans le montage `/quarantine`. `undo` les remet en place ; `purge` les supprime
  définitivement.
- **Les dossiers de logiciels sont ignorés** : `.git`, `.hg`, `.svn`, `node_modules`, `.venv`,
  `venv`, `site-packages`, `__pycache__`, `AppData`, `ProgramData`, `Program Files`,
  `Program Files (x86)` et `Windows`, quelle que soit leur casse.
- **Une faute de frappe dans une extension n'est pas refusée** : `--ext jpgg` est une extension
  valable, qui ne correspond simplement à rien (seuls les noms proches d'une catégorie sont
  refusés). L'audit nomme les extensions qui ne sont ni des photos ni des
  vidéos : lisez cet avertissement.
- **`--ext` limite toujours l'analyse** : `--ext jpg,pdf` analyse les photos JPEG et les
  documents PDF, pas les fichiers RAW ni les vidéos.

Montez les dossiers qui contiennent vos documents, jamais un disque entier ni `C:\Users` : les
programmes et leurs données s'y trouvent aussi.

---

← [5. Choisir la copie gardée](05-choose-the-kept-copy.md) · [Documentation](../README.md) · Suivant : **[7. Le fichier de configuration](07-configuration-file.md)** →
