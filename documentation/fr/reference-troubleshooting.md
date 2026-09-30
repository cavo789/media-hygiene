# Dépannage

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-troubleshooting.md)

## Une vraie sauvegarde est vue comme des doublons

Si `D:\sauvegarde` doit rester une seconde copie de vos photos,
[excluez-la](clean/05-choose-the-kept-copy.md#exclure-un-dossier) (ou ne la montez pas). Sinon l'outil
voit ses fichiers comme des doublons, ce qui est exact.

## Un dossier est refusé parce qu'il est monté deux fois

Un dossier inclut déjà ses sous-dossiers : montez `C:\Photos` seul, pas `C:\Photos` **et**
`C:\Photos\2019`. Windows ignore la casse, Docker non : `C:\Photos` plus `C:\photos\2019`, c'est
le même dossier deux fois. L'outil le refuse plutôt que de prendre une photo pour un doublon
d'elle-même.

## OneDrive « fichiers à la demande »

Analyser un dossier dont les fichiers sont uniquement en ligne les télécharge tous. Rendez-les
d'abord disponibles hors connexion, ou laissez ce dossier de côté.

## Les disques Windows sont lents via Docker

Le premier audit lit chaque image, ainsi que chaque fichier qui a la même taille qu'un autre.
Avec [`-v media-hygiene-cache:/cache`](start/02-keep-the-cache.md), les audits suivants ne lisent que les
fichiers nouveaux ou modifiés. Rien que lister des dizaines de milliers de fichiers prend quelques
minutes : [chaque étape affiche sa progression](start/01-first-audit.md#ce-qui-saffiche-pendant-lanalyse).

## L'ordinateur est lent pendant un audit

L'outil utilise tous les processeurs pour aller plus vite. Pour en garder pour le reste :
[limiter les processeurs utilisés](reference-advanced.md#limiter-les-processeurs-utilisés).

## « Impossible de demander confirmation sans terminal interactif »

Lancez avec `-it` : sans terminal, `clean` et `purge` ne peuvent pas demander confirmation, et
les couleurs sont désactivées. Dans un script, ajoutez plutôt `--yes`.

## Dossiers où l'outil ne peut pas écrire

Quand un dossier donné à `-v` n'existe pas encore, Docker le crée pour l'administrateur
(`root`), et l'outil (qui ne tourne pas en `root`) ne peut pas y écrire. La commande s'arrête
alors avant l'analyse et nomme le dossier.

- Créez vos dossiers **avant** `docker run` (`mkdir …`).
- Depuis WSL ou Linux, ajoutez `--user "$(id -u):$(id -g)"` ; un dossier déjà créé par Docker
  redevient le vôtre avec `sudo chown "$(id -u):$(id -g)" <dossier>`.
- Un `:ro` sur `/journal`, `/quarantine`, `/reports` ou `/cache` l'arrête de la même façon. Seul
  `config.toml` est facultatif : il n'est alors pas créé.
- Si seul le rapport échoue après un audit, un avertissement le signale et les résultats restent
  à l'écran.

## Un chemin Windows de `config.toml` est refusé

Écrivez les chemins Windows entre **apostrophes** : `'D:\backup'`. Entre guillemets, TOML
transforme le `\b` de `"D:\backup"` en caractère de contrôle, et l'outil refuse ce chemin au lieu
de l'ignorer ([étape 7](clean/07-configuration-file.md#le-remplir)).

## La page de tri ne s'ouvre pas

- Avez-vous publié le port ? La commande a besoin de `-p 127.0.0.1::8080`.
- L'adresse vient de `docker port media-hygiene-review 8080`, dans une autre fenêtre, pendant que le
  tri tourne ([étape 10](clean/10-review-bursts.md#étape-2--ouvrir-la-page)).
- Ouvrez-la avec `127.0.0.1` ou `localhost` : la page refuse les autres noms d'hôte.
- *« Le tri ne tourne plus »* : la fenêtre du tri a été fermée ou arrêtée avec Ctrl+C.
  Relancez-le ; vos choix sont conservés.
