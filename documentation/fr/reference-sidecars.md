# Fichiers compagnons

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-sidecars.md)

Les fichiers compagnons (*sidecars*) sont de petits fichiers posés à côté d'une photo ou d'une
vidéo, qui en gardent les métadonnées ou les retouches : `.xmp` (Lightroom, digiKam, darktable),
`.aae` (retouches de l'iPhone), `.thm` (vignettes des caméscopes), et les fichiers `.json` d'un
[Takeout Google Photos](#google-photos-takeout). Un fichier compagnon
appartient aux fichiers de son dossier qui portent le même nom : `IMG_1.xmp` à `IMG_1.jpg` ou
`IMG_1.CR2`, et `IMG_1.CR2.xmp` à `IMG_1.CR2`, sans tenir compte de la casse.

- **À côté de sa photo**, un fichier compagnon n'est jamais touché.
- **Sa photo est gardée** : entre des copies identiques, celle qui a un fichier compagnon est
  gardée, et elle conserve ainsi ses retouches. Seul un dossier protégé ou préféré passe avant.
  Quand plusieurs copies ont chacune leur fichier compagnon, les autres
  [règles de choix](clean/05-choose-the-kept-copy.md#comment-loutil-choisit) les départagent.
- **Orphelin** : une fois que `clean` a supprimé ou déplacé tous les fichiers du même nom à côté
  de lui (ou s'il n'y en avait déjà aucun), un fichier compagnon ne sert plus à rien. `clean` le
  déplace en quarantaine, sans jamais le supprimer, après avoir vérifié qu'aucun fichier du même
  nom n'est revenu. `undo` le remet en place ; `purge` le supprime définitivement. Sans le
  montage `/quarantine`, les orphelins restent en place.
- **Avec `--ext`**, l'audit ne regarde qu'une partie des fichiers : les fichiers compagnons déjà
  seuls avant le nettoyage restent où ils sont, seuls ceux que le nettoyage lui-même laisse seuls
  sont déplacés.
- **Les dossiers protégés** ne sont jamais modifiés, fichiers compagnons compris.
- **Écrits par `xmp`** : un fichier compagnon que cet outil a créé pour ses mots, et que personne
  n'a modifié depuis, ne contient aucune retouche : il ne fait pas de sa photo la copie gardée
  ([tags](reference-tags.md#emporter-les-mots-avec-les-photos--xmp)).

Le fichier compagnon d'une copie mise de côté n'est pas déplacé à côté de la copie gardée : il
devient orphelin. Pour garder une autre copie *avec* ses retouches, indiquez son dossier dans
[`--prefer`](clean/05-choose-the-kept-copy.md#préférer-un-dossier).

Dans l'audit, les fichiers compagnons orphelins sont comptés sur leur propre ligne, et le rapport
HTML les liste dans la section *Fichiers compagnons orphelins*
([capture](clean/04-html-report.md#fichiers-cassés-et-fichiers-compagnons-orphelins)).

## Google Photos Takeout

Google Takeout (takeout.google.com) télécharge une copie de vos Google Photos en fichiers ZIP.
Extrayez-les, puis ajoutez le dossier extrait comme n'importe quel autre (étape 3) : ses photos
sont comparées aux vôtres, et ses fichiers `.json` sont traités comme des fichiers compagnons.

- **Chaque `.json` appartient à sa photo ou sa vidéo** : `IMG_1234.jpg.json` (anciens Takeout)
  ou `IMG_1234.jpg.supplemental-metadata.json` (récents), aussi quand Google a raccourci le nom
  (`.supplemental-me.json`, un long nom de photo coupé), déplacé le numéro d'un nom en double
  (`IMG_1234.jpg(1).json` pour `IMG_1234(1).jpg`) ou écrit `_` pour `&` et `?`. Une version
  retouchée (`IMG_1234-edited.jpg`) partage le `.json` de son original, ou l'a seule quand
  l'original n'est plus là.
- **Il suit sa photo** : `clean` le met de côté une fois sa photo partie, `sort` le déplace avec
  sa photo, `undo` le remet en place. Un `.json` qui ne décrit aucun fichier de son dossier
  n'est pas touché.
- **Sa date et son lieu servent** : une photo ou une vidéo sans date propre (une vidéo, une
  capture d'écran, une image reçue) est datée par `classify` et `tags` à partir du `.json`,
  après sa propre date EXIF ou vidéo et avant son nom ; sa position compte comme une position
  GPS pour les règles `place` et `trip` et les mots de lieu. Les photos elles-mêmes ne sont
  jamais modifiées. Il faut le cache (`/cache`) : les `.json` sont lus une fois, pendant
  l'audit.
- **Les dossiers d'année** (`Photos from 2019`) sont des noms de dossier génériques : entre
  copies identiques, celle d'un dossier d'album est gardée.
- **Une retouche et son original** ne sont jamais des quasi-doublons l'un de l'autre : les deux
  restent.

Pas vérifié sur un vrai Takeout (aucun sous la main) : ces règles de noms viennent des outils
qui lisent les Takeout. La description d'un `.json` se cherche ([`tags`](reference-tags.md#doù-viennent-les-mots) : source `takeout`, écrite dans les `.xmp` seulement si vous le demandez), le
suffixe d'une version retouchée n'est reconnu qu'en anglais (`-edited`), et un `.json` au nom
coupé que `sort` a renuméroté (` (2)`) ne retrouve plus sa photo. Dites-nous à quoi ressemble
votre Takeout s'il diffère.
