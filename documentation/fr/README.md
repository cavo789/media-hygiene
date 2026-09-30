# Documentation de media-hygiene

← [Retour au projet](../../README_FR.md) · 🇬🇧 [English version](../en/README.md)

Ce guide vous emmène de votre toute première commande jusqu'à une photothèque débarrassée de ses
doublons, une étape à la fois. Chaque étape ajoute une seule chose à la commande de l'étape
précédente. Arrêtez-vous quand vous avez ce qu'il vous faut : dès l'étape 1, vous savez où sont
vos doublons.

## Pour commencer

Quoi que vous vouliez faire ensuite, les trois premières étapes sont les mêmes : elles
montrent ce que contiennent vos dossiers, sans rien modifier.

1. [Votre premier audit](start/01-first-audit.md) : un dossier, une commande, et comment lire le
   résultat.
2. [Garder le cache](start/02-keep-the-cache.md) : les audits suivants prennent des secondes au lieu de
   minutes.
3. [Plusieurs dossiers et disques](start/03-several-folders.md) : `C:` et `D:` ensemble, le dossier
   courant, WSL.
## Nettoyer les doublons

Libérer la place des copies en trop, en toute sécurité, et garder les meilleures photos.

**Les voir** (rien n'est modifié) :

4. [Le rapport HTML](clean/04-html-report.md) : les images, les paires de dossiers, la preuve.

**Affiner l'analyse :**

5. [Choisir la copie gardée](clean/05-choose-the-kept-copy.md) : `--prefer`, `--protect`, `--exclude`.
6. [Seulement certains types de fichiers](clean/06-file-types.md) : `--ext`, et les fichiers autres que
   des photos.
7. [Le fichier de configuration](clean/07-configuration-file.md) : écrire vos choix une fois pour
   toutes, dans `config.toml`.

**Libérer l'espace :**

8. [Nettoyer](clean/08-clean.md) : supprimer les copies en trop, avec un journal et une quarantaine.
9. [Annuler, historique, purge](clean/09-undo-history-purge.md) : changer d'avis, voir ce qui a été
   fait, vider la quarantaine.

**Aller plus loin :**

10. [Trier les rafales dans le navigateur](clean/10-review-bursts.md) : garder les meilleures photos de
    chaque rafale, au clavier.
11. [Les quasi-doublons](clean/11-near-duplicates.md) : les copies réduites et recompressées
    (`--tier near`).
12. [Décider paire par paire](clean/12-decide-pair-by-pair.md) : inverser une paire de dossiers ou ne
    pas y toucher, depuis le rapport.
13. [Un second avis](clean/13-second-opinion.md) : comparer avec Czkawka, un outil indépendant.

## Trier les photos

Donner à vos photos une arborescence rangée, `année/catégorie` ou celle que vous choisissez.
Nettoyez d'abord les doublons : sinon les deux copies sont triées.

4. [Proposer une arborescence](sort/04-classify.md) : `classify` propose une place pour chaque
   fichier, et ne modifie rien.
5. [Revoir la proposition](sort/05-review-the-proposal.md) : la corriger dans un classeur, regarder
   les photos dans le rapport.
6. [Écrire ce que vous savez](sort/06-write-down-what-you-know.md) : des règles pour vos voyages,
   vos anniversaires, vos dossiers et vos appareils, appliquées à chaque exécution.

## Référence

- [Commandes et options](reference-commands.md) : chaque commande, chaque option, et leur
  `--help`.
- [Points de montage](reference-mount-points.md) : `/data`, `/cache`, `/reports`, `/config`,
  `/journal`, `/quarantine`.
- [Comment vos photos restent en sécurité](reference-safety.md) : ce qui compte comme doublon, ce
  qui est vérifié avant chaque action, comment le vérifier vous-même.
- [Fichiers compagnons](reference-sidecars.md) : `.xmp`, `.aae`, `.thm`.
- [Dépannage](reference-troubleshooting.md) : mises en garde et messages d'erreur.
- [Utilisation avancée](reference-advanced.md) : limiter les processeurs utilisés
  (`PYTHON_CPU_COUNT`).

## Pour les développeurs

- [Développement](development.md) : construire l'image, les commandes du devcontainer, les
  versions.

Les captures d'écran et les sorties console de ce guide viennent d'une bibliothèque de
démonstration d'images synthétiques (paysages dessinés, aucune vraie photo), analysée par la vraie
image.
