# Fichiers compagnons

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-sidecars.md)

Les fichiers compagnons (*sidecars*) sont de petits fichiers posés à côté d'une photo ou d'une
vidéo, qui en gardent les métadonnées ou les retouches : `.xmp` (Lightroom, digiKam, darktable),
`.aae` (retouches de l'iPhone), `.thm` (vignettes des caméscopes). Un fichier compagnon
appartient aux fichiers de son dossier qui portent le même nom : `IMG_1.xmp` à `IMG_1.jpg` ou
`IMG_1.CR2`, et `IMG_1.CR2.xmp` à `IMG_1.CR2`, sans tenir compte de la casse.

- **À côté de sa photo**, un fichier compagnon n'est jamais touché.
- **Sa photo est gardée** : entre des copies identiques, celle qui a un fichier compagnon est
  gardée, et elle conserve ainsi ses retouches. Seul un dossier protégé ou préféré passe avant.
  Quand plusieurs copies ont chacune leur fichier compagnon, les autres
  [règles de choix](05-choose-the-kept-copy.md#comment-loutil-choisit) les départagent.
- **Orphelin** : une fois que `clean` a supprimé ou déplacé tous les fichiers du même nom à côté
  de lui (ou s'il n'y en avait déjà aucun), un fichier compagnon ne sert plus à rien. `clean` le
  déplace en quarantaine, sans jamais le supprimer, après avoir vérifié qu'aucun fichier du même
  nom n'est revenu. `undo` le remet en place ; `purge` le supprime définitivement. Sans le
  montage `/quarantine`, les orphelins restent en place.
- **Avec `--ext`**, l'audit ne regarde qu'une partie des fichiers : les fichiers compagnons déjà
  seuls avant le nettoyage restent où ils sont, seuls ceux que le nettoyage lui-même laisse seuls
  sont déplacés.
- **Les dossiers protégés** ne sont jamais modifiés, fichiers compagnons compris.

Le fichier compagnon d'une copie supprimée n'est pas déplacé à côté de la copie gardée : il
devient orphelin. Pour garder une autre copie *avec* ses retouches, indiquez son dossier dans
[`--prefer`](05-choose-the-kept-copy.md#préférer-un-dossier).

Dans l'audit, les fichiers compagnons orphelins sont comptés sur leur propre ligne, et le rapport
HTML les liste dans la section *Fichiers compagnons orphelins*
([capture](04-html-report.md#fichiers-cassés-et-fichiers-compagnons-orphelins)).
