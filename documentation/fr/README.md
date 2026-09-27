# Documentation de media-dedup

← [Retour au projet](../../README_FR.md) · 🇬🇧 [English version](../en/README.md)

Ce guide vous emmène de votre toute première commande jusqu'à une photothèque débarrassée de ses
doublons, une étape à la fois. Chaque étape ajoute une seule chose à la commande de l'étape
précédente. Arrêtez-vous quand vous avez ce qu'il vous faut : dès l'étape 1, vous savez où sont
vos doublons.

## Guide — pas à pas

**Trouver les doublons** (rien n'est modifié) :

1. [Votre premier audit](01-first-audit.md) : un dossier, une commande, et comment lire le
   résultat.
2. [Garder le cache](02-keep-the-cache.md) : les audits suivants prennent des secondes au lieu de
   minutes.
3. [Plusieurs dossiers et disques](03-several-folders.md) : `C:` et `D:` ensemble, le dossier
   courant, WSL.
4. [Le rapport HTML](04-html-report.md) : les images, les paires de dossiers, la preuve.

**Affiner l'analyse :**

5. [Choisir la copie gardée](05-choose-the-kept-copy.md) : `--prefer`, `--protect`, `--exclude`.
6. [Seulement certains types de fichiers](06-file-types.md) : `--ext`, et les fichiers autres que
   des photos.
7. [Le fichier de configuration](07-configuration-file.md) : écrire vos choix une fois pour
   toutes, dans `config.toml`.

**Libérer l'espace :**

8. [Nettoyer](08-clean.md) : supprimer les copies en trop, avec un journal et une quarantaine.
9. [Annuler, historique, purge](09-undo-history-purge.md) : changer d'avis, voir ce qui a été
   fait, vider la quarantaine.

**Aller plus loin :**

10. [Trier les rafales dans le navigateur](10-review-bursts.md) : garder les meilleures photos de
    chaque rafale, au clavier.
11. [Les quasi-doublons](11-near-duplicates.md) : les copies réduites et recompressées
    (`--tier near`).
12. [Décider paire par paire](12-decide-pair-by-pair.md) : inverser une paire de dossiers ou ne
    pas y toucher, depuis le rapport.
13. [Un second avis](13-second-opinion.md) : comparer avec Czkawka, un outil indépendant.

## Référence

- [Commandes et options](reference-commands.md) : chaque commande, chaque option, et leur
  `--help`.
- [Points de montage](reference-mount-points.md) : `/data`, `/cache`, `/reports`, `/config`,
  `/journal`, `/quarantine`.
- [Comment vos photos restent en sécurité](reference-safety.md) : ce qui compte comme doublon, ce
  qui est vérifié avant chaque action, comment le vérifier vous-même.
- [Fichiers compagnons](reference-sidecars.md) : `.xmp`, `.aae`, `.thm`.
- [Dépannage](reference-troubleshooting.md) : mises en garde et messages d'erreur.

## Pour les développeurs

- [Développement](development.md) : construire l'image, les commandes du devcontainer, les
  versions.

Les captures d'écran et les sorties console de ce guide viennent d'une bibliothèque de
démonstration d'images synthétiques (paysages dessinés, aucune vraie photo), analysée par la vraie
image.
