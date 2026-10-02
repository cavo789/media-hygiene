# media-hygiene

Trouve et nettoie en toute sécurité les photos et vidéos en double, réparties sur plusieurs
dossiers et plusieurs disques — d'un seul `docker run`, sous Windows (PowerShell) ou WSL.

🇬🇧 [English version](README.md)

![Un audit dans le terminal : 83 fichiers média analysés, 20 groupes de fichiers identiques, 32 copies en trop, 13,9 Mo à libérer, puis les dossiers partageant des fichiers identiques, chaque paire disant quel dossier garde ses copies](documentation/fr/images/terminal-audit.webp)

## Démarrage rapide

Avec Docker installé, une seule commande audite un dossier :

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene --locale fr audit
```

Elle liste les photos et vidéos en double ou cassées de `C:\Photos`, sans rien modifier : `:ro`
(lecture seule) fait interdire toute écriture par Docker lui-même. Le premier lancement
télécharge l'image tout seul. [Votre premier audit](documentation/fr/start/01-first-audit.md) explique
cette commande et son résultat, morceau par morceau.

Ce qu'elle fait :

- **Doublons exacts** : même taille et même SHA-256, comparés à nouveau octet par octet juste
  avant toute suppression. Détectés entre dossiers *et* entre disques (`C:` et `D:` dans la même
  exécution).
- **Fichiers cassés** : fichiers vides, images et fichiers RAW impossibles à décoder (JPEG
  tronqué, …), vidéos impossibles à ouvrir.
- **Réversible** : chaque action est journalisée ; `undo` reconstruit chaque copie supprimée à
  partir de la copie conservée, et ressort chaque fichier de la quarantaine.
- **Fichiers compagnons orphelins** : un fichier compagnon (`.xmp`, `.aae`, `.thm`) resté sans
  sa photo est déplacé en quarantaine ; celui qui accompagne sa photo n'est jamais touché.
- **Rafales et quasi-doublons** : montrés côte à côte dans un rapport HTML ; vous choisissez les
  meilleures photos de chaque rafale [au clavier, dans votre navigateur](documentation/fr/clean/10-review-bursts.md).
- **Jamais touchés sans votre accord** : les rafales, les quasi-doublons, les dossiers protégés.

## Documentation

La [documentation](documentation/fr/README.md) vous accompagne pas à pas. Chaque étape ajoute une
seule chose à la commande de l'étape précédente.

**Pour commencer** — les trois mêmes premières étapes, quoi que vous fassiez ensuite :

1. [Votre premier audit](documentation/fr/start/01-first-audit.md) : un dossier, une commande, et
   comment lire le résultat.
2. [Garder le cache](documentation/fr/start/02-keep-the-cache.md) : les audits suivants prennent des
   secondes au lieu de minutes.
3. [Plusieurs dossiers et disques](documentation/fr/start/03-several-folders.md) : `C:` et `D:`
   ensemble, le dossier courant, WSL.

**Nettoyer les doublons**

4. [Le rapport HTML](documentation/fr/clean/04-html-report.md) : les images, les paires de dossiers, la
   preuve.
5. [Choisir la copie gardée](documentation/fr/clean/05-choose-the-kept-copy.md) : `--prefer`,
   `--protect`, `--exclude`.
6. [Seulement certains types de fichiers](documentation/fr/clean/06-file-types.md) : `--ext`, et les
   fichiers autres que des photos.
7. [Le fichier de configuration](documentation/fr/clean/07-configuration-file.md) : écrire vos choix une
   fois pour toutes, dans `config.toml`.
8. [Nettoyer](documentation/fr/clean/08-clean.md) : supprimer les copies en trop, avec un journal et une
   quarantaine.
9. [Annuler, historique, purge](documentation/fr/clean/09-undo-history-purge.md) : changer d'avis, voir
   ce qui a été fait, vider la quarantaine.
10. [Trier les rafales dans le navigateur](documentation/fr/clean/10-review-bursts.md) : garder les
    meilleures photos de chaque rafale, au clavier.
11. [Les quasi-doublons](documentation/fr/clean/11-near-duplicates.md) : les copies réduites et
    recompressées (`--tier near`).
12. [Décider paire par paire](documentation/fr/clean/12-decide-pair-by-pair.md) : inverser une paire de
    dossiers ou ne pas y toucher, depuis le rapport.
13. [Un second avis](documentation/fr/clean/13-second-opinion.md) : comparer avec Czkawka, un outil
    indépendant.

**Trier les photos** (nettoyez d'abord les doublons)

4. [Proposer une arborescence](documentation/fr/sort/04-classify.md) — `classify` propose une
   place pour chaque fichier, et ne modifie rien.
5. [Revoir la proposition](documentation/fr/sort/05-review-the-proposal.md) — la corriger dans un
   classeur, regarder les photos dans le rapport.
6. [Écrire ce que vous savez](documentation/fr/sort/06-write-down-what-you-know.md) — des règles
   pour vos voyages, anniversaires, dossiers et appareils, appliquées à chaque exécution.
7. [Trier](documentation/fr/sort/07-sort.md) — `sort` déplace les fichiers comme le dit le
   classeur, journalisé et annulable.
8. [Nommer les sujets avec un modèle local](documentation/fr/sort/08-subjects-from-a-local-model.md) —
   un modèle de vision sur votre ordinateur dit ce que montrent les photos isolées (facultatif).
9. [Lieux et voyages grâce au GPS](documentation/fr/sort/09-places-from-gps.md) — nommer vos
   lieux sur une carte ; le GPS des téléphones récents trie maison, famille et voyages, hors
   ligne (facultatif).
10. [Nommer les événements dans le navigateur](documentation/fr/sort/10-name-events-in-the-browser.md) —
    un événement à la fois avec ses photos, nommé au clavier (facultatif).
11. [Albums](documentation/fr/sort/11-albums.md) — une photo dans plusieurs dossiers, en liens
    physiques : aucune copie, aucune place prise (facultatif).

**Référence** : [commandes et options](documentation/fr/reference-commands.md),
[points de montage](documentation/fr/reference-mount-points.md),
[comment vos photos restent en sécurité](documentation/fr/reference-safety.md),
[fichiers compagnons](documentation/fr/reference-sidecars.md),
[dépannage](documentation/fr/reference-troubleshooting.md),
[le classeur d'inventaire](documentation/fr/reference-inventory.md),
[utilisation avancée](documentation/fr/reference-advanced.md).

**Pour les développeurs** : [construire l'image, le devcontainer, les versions](documentation/fr/development.md).

## La commande complète

Une fois le guide parcouru, la plupart des gens arrivent à cette commande : deux dossiers, le
cache, les rapports, la configuration, le journal et la quarantaine. Elle nettoie ; pour un
audit, ajoutez `:ro` à vos dossiers et écrivez `audit` au lieu de `clean`.

```powershell
mkdir "$HOME\media-hygiene\reports", "$HOME\media-hygiene\config", "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

Depuis WSL, écrivez les chemins Linux et lancez le conteneur sous votre identité, pour que les
fichiers créés vous appartiennent :

```bash
mkdir -p ~/media-hygiene/{reports,config,journal,quarantine}
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos" \
  -v "/mnt/d/Ancien disque:/data/d/Ancien disque" \
  -v media-hygiene-cache:/cache \
  -v ~/media-hygiene/reports:/reports \
  -v ~/media-hygiene/config:/config \
  -v ~/media-hygiene/journal:/journal \
  -v ~/media-hygiene/quarantine:/quarantine \
  cavo789/media-hygiene --locale fr clean
```

`undo` au lieu de `clean` remet tout en place.

## Mettre à jour

`docker pull cavo789/media-hygiene` récupère la dernière version ; un tag comme
`cavo789/media-hygiene:0.3.0` en fixe une.

### Vous veniez de media-dedup ?

Jusqu'à la version 0.2, l'outil s'appelait **media-dedup** (`cavo789/media-dedup`) ; il
s'appelle media-hygiene depuis la version 0.3.0. Rien de ce que vous avez n'est perdu :

- Écrivez `cavo789/media-hygiene` au lieu de `cavo789/media-dedup` dans vos commandes :
  l'ancienne image n'est plus sur Docker Hub (Docker répond alors *pull access denied*).
- Gardez vos dossiers et vos volumes : `$HOME\media-dedup\journal`, `media-dedup-cache` et
  les autres vous appartiennent, quel que soit leur nom. Continuez à les écrire dans vos
  options `-v` : `undo`, `history` et le cache y retrouvent tout.
- Les variables d'environnement `MEDIA_DEDUP_…` fonctionnent encore jusqu'à la version 0.4.0,
  avec un avertissement : renommez-les `MEDIA_HYGIENE_…`.
