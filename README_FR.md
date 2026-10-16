# media-hygiene

Nettoie, range et explore les photos et vidéos réparties sur plusieurs dossiers et plusieurs
disques — avec Docker, sous Windows (PowerShell) ou WSL. Tout se passe sur votre
ordinateur, et chaque changement est journalisé et peut être annulé.

- **Nettoyer les doublons** : copies identiques, copies redimensionnées ou recompressées, rafales.
- **Ranger** : une arborescence proposée par date, événement, lieu (GPS, hors ligne), sujet (un
  modèle de vision local) et personne, que vous corrigez avant que rien ne bouge.
- **Retrouver les personnes** : les visages sont trouvés et regroupés sur votre ordinateur ;
  nommez-les une fois, puis retrouvez les photos de quelqu'un par son nom et rangez-les par
  personne, sans serveur photo comme Immich.

[![Docker Hub](https://img.shields.io/docker/v/cavo789/media-hygiene?sort=semver&label=Docker%20Hub)](https://hub.docker.com/r/cavo789/media-hygiene)
[![Pulls](https://img.shields.io/docker/pulls/cavo789/media-hygiene)](https://hub.docker.com/r/cavo789/media-hygiene)

L'image : [**cavo789/media-hygiene** sur Docker Hub](https://hub.docker.com/r/cavo789/media-hygiene) (amd64 et arm64).

🇬🇧 [English version](README.md)

![Un audit dans le terminal : 83 fichiers média analysés, 20 groupes de fichiers identiques, 32 copies en trop, 14,0 Mo à libérer, puis les dossiers partageant des fichiers identiques, chaque paire disant quel dossier garde ses copies](documentation/fr/images/terminal-audit.webp)

## Démarrage rapide

Avec Docker installé ([comment l'installer](https://cavo789.github.io/media-hygiene/fr/start/00-install-docker/), sous
Windows ou Linux), écrivez `mh` une fois, une commande courte qui retient vos dossiers. Dans
**PowerShell**, avec votre dossier à la place de `C:\Photos` :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
New-Item -ItemType Directory -Force "$HOME\media-hygiene", (Split-Path $PROFILE) | Out-Null
docker run --rm -e MEDIA_HYGIENE_GENERAL__LOCALE=fr cavo789/media-hygiene launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

`mh audit` liste les photos et vidéos en double ou cassées de `C:\Photos`, sans rien modifier :
`mh` lui donne votre dossier en lecture seule (`:ro`), et Docker lui-même interdit toute écriture.
Le premier lancement télécharge l'image [depuis Docker Hub](https://hub.docker.com/r/cavo789/media-hygiene) tout seul.
Ensuite, `mh` seul ouvre un menu qui propose l'étape suivante, et `mh shortcut` pose une icône
*Media Hygiene* sur votre Bureau. [Votre premier audit](https://cavo789.github.io/media-hygiene/fr/start/01-first-audit/)
explique ces lignes et le résultat, morceau par morceau.

Juste pour essayer, ou dans un terminal **WSL** (ou Linux), une seule commande audite un dossier
sans `mh` :

```bash
docker run --rm -it -v "/mnt/c/Photos:/data/c/Photos:ro" cavo789/media-hygiene --locale fr audit
```

Ce qu'il trouve :

- **Doublons exacts** : même taille et même SHA-256, entre dossiers *et* entre disques (`C:` et
  `D:` dans la même exécution).
- **Fichiers cassés** : fichiers vides, images et fichiers RAW impossibles à décoder (JPEG
  tronqué, …), vidéos impossibles à ouvrir.
- **Fichiers compagnons orphelins** : un fichier compagnon (`.xmp`, `.aae`, `.thm`) resté sans
  sa photo.
- **Rafales et quasi-doublons** (vidéos réencodées comprises) : montrés côte à côte dans un
  rapport HTML ; `review` vous fait ensuite choisir les meilleures photos de chaque rafale [au clavier, dans votre navigateur](https://cavo789.github.io/media-hygiene/fr/clean/10-review-bursts/).

Ensuite, si vous le décidez, `clean` met de côté les copies en trop et les fichiers cassés ; les
rafales et les quasi-doublons seulement si vous le demandez.

## Vos photos sont en sécurité

**Nous le garantissons : ces commandes ne modifient, ne déplacent ni ne suppriment jamais une
photo ou une vidéo** — `audit`, `crosscheck`, `classify`, `review`, `review-sort`, `places`,
`inventory`, `tags`, `search`, `people`, `history`, `reports`, `config`, `status`, `launcher`. Elles n'écrivent que leurs propres fichiers
(rapports, cache, `config.toml`). Lancez-les avec vos dossiers montés en `:ro` : le système
lui-même interdit alors toute modification.

**Les commandes qui agissent n'effacent jamais rien.** `sort` déplace des fichiers (sur un même
disque, un simple renommage : aucune copie, aucune place prise), `album` ajoute des seconds noms,
`xmp` écrit de petits fichiers compagnons `.xmp` à côté des photos, `clean` déplace les copies en double en quarantaine après les avoir comparées octet par octet avec
la copie gardée, `undo` remet en place. Jamais par-dessus un autre fichier, chaque étape
journalisée, tout est annulable.

**Seul `purge` efface** : la quarantaine, pour de bon, après vous l'avoir demandé (et
`clean --delete`, si vous le demandez : la copie gardée reste). Plus de détails dans
[comment vos photos restent en sécurité](https://cavo789.github.io/media-hygiene/fr/reference-safety/).

## Documentation

La [documentation](https://cavo789.github.io/media-hygiene/fr/) vous accompagne pas à pas, avec
une recherche. L'étape 1 écrit `mh` ; ensuite, chaque étape est une commande `mh` courte.

**Trois guides, une page chacun**, le strict minimum d'abord :

- 🧹 [Nettoyer en bref](https://cavo789.github.io/media-hygiene/fr/clean/quick-guide/) — libérer la place des copies en double, sans risque.
- 🗂️ [Trier en bref](https://cavo789.github.io/media-hygiene/fr/sort/quick-guide/) — une arborescence rangée, proposée, corrigée par vous, puis appliquée.
- 🔎 [Retrouver en bref](https://cavo789.github.io/media-hygiene/fr/find/quick-guide/) — retrouver une photo par une personne, un lieu, une année ou un mot.

Ou pas à pas, une option à la fois :

**Pour commencer** — les trois mêmes premières étapes, quoi que vous fassiez ensuite (pas encore
de Docker ? [Installez Docker](https://cavo789.github.io/media-hygiene/fr/start/00-install-docker/) d'abord) :

1. [Votre premier audit](https://cavo789.github.io/media-hygiene/fr/start/01-first-audit/) : écrire `mh` pour un dossier,
   `mh audit`, et comment lire le résultat.
2. [Garder le cache](https://cavo789.github.io/media-hygiene/fr/start/02-keep-the-cache/) : les audits suivants prennent des
   secondes au lieu de minutes.
3. [Plusieurs dossiers et disques](https://cavo789.github.io/media-hygiene/fr/start/03-several-folders/) : `mh folders add`,
   `C:` et `D:` ensemble ; sans `mh`, WSL et Linux.

**Nettoyer les doublons**

4. [Le rapport HTML](https://cavo789.github.io/media-hygiene/fr/clean/04-html-report/) : les images, les paires de dossiers, la
   preuve.
5. [Choisir la copie gardée](https://cavo789.github.io/media-hygiene/fr/clean/05-choose-the-kept-copy/) : `--prefer`,
   `--protect`, `--exclude`.
6. [Seulement certains types de fichiers](https://cavo789.github.io/media-hygiene/fr/clean/06-file-types/) : `--ext`, et les
   fichiers autres que des photos.
7. [Le fichier de configuration](https://cavo789.github.io/media-hygiene/fr/clean/07-configuration-file/) : écrire vos choix une
   fois pour toutes, dans `config.toml`.
8. [Nettoyer](https://cavo789.github.io/media-hygiene/fr/clean/08-clean/) : mettre les copies en trop de côté en
   quarantaine, avec un journal.
9. [Annuler, historique, purge](https://cavo789.github.io/media-hygiene/fr/clean/09-undo-history-purge/) : changer d'avis, voir
   ce qui a été fait, vider la quarantaine pour libérer la place.
10. [Trier les rafales dans le navigateur](https://cavo789.github.io/media-hygiene/fr/clean/10-review-bursts/) : garder les
    meilleures photos de chaque rafale, au clavier.
11. [Les quasi-doublons](https://cavo789.github.io/media-hygiene/fr/clean/11-near-duplicates/) : les copies réduites et
    recompressées (`--tier near`).
12. [Décider paire par paire](https://cavo789.github.io/media-hygiene/fr/clean/12-decide-pair-by-pair/) : inverser une paire de
    dossiers ou ne pas y toucher, depuis le rapport.
13. [Un second avis](https://cavo789.github.io/media-hygiene/fr/clean/13-second-opinion/) : comparer avec Czkawka, un outil
    indépendant.

**Trier les photos** (nettoyez d'abord les doublons)

4. [Proposer une arborescence](https://cavo789.github.io/media-hygiene/fr/sort/04-classify/) — `classify` propose une
   place pour chaque fichier, et ne modifie rien.
5. [Revoir la proposition](https://cavo789.github.io/media-hygiene/fr/sort/05-review-the-proposal/) — la corriger dans un
   classeur, regarder les photos dans le rapport.
6. [Écrire ce que vous savez](https://cavo789.github.io/media-hygiene/fr/sort/06-write-down-what-you-know/) — des règles
   pour vos voyages, anniversaires, dossiers et appareils, appliquées à chaque exécution.
7. [Trier](https://cavo789.github.io/media-hygiene/fr/sort/07-sort/) — `sort` déplace les fichiers comme le dit le
   classeur, journalisé et annulable.
8. [Nommer les sujets avec un modèle local](https://cavo789.github.io/media-hygiene/fr/sort/08-subjects-from-a-local-model/) —
   un modèle de vision sur votre ordinateur dit ce que montrent les photos isolées (facultatif).
9. [Lieux et voyages grâce au GPS](https://cavo789.github.io/media-hygiene/fr/sort/09-places-from-gps/) — nommer vos
   lieux sur une carte ; le GPS des téléphones récents trie maison, famille et voyages, hors
   ligne (facultatif).
10. [Trier par personne](https://cavo789.github.io/media-hygiene/fr/sort/10-sort-by-person/) — nommer les visages
    trouvés dans vos photos ; une règle range les événements où quelqu'un figure, hors ligne
    (facultatif).
11. [Nommer les événements dans le navigateur](https://cavo789.github.io/media-hygiene/fr/sort/11-name-events-in-the-browser/) —
    un événement à la fois avec ses photos, nommé au clavier (facultatif).
12. [Albums](https://cavo789.github.io/media-hygiene/fr/sort/12-albums/) — une photo dans plusieurs dossiers, en liens
    physiques : aucune copie, aucune place prise (facultatif).

**Chaque commande a sa page** : d'abord ce qu'elle vous apporte, quand, et une commande à essayer ;
puis les dossiers dont elle a besoin, ses options, des exemples : [`audit`](https://cavo789.github.io/media-hygiene/fr/commands/audit/), [`status`](https://cavo789.github.io/media-hygiene/fr/commands/status/),
[`clean`](https://cavo789.github.io/media-hygiene/fr/commands/clean/), [`undo`](https://cavo789.github.io/media-hygiene/fr/commands/undo/),
[`history`](https://cavo789.github.io/media-hygiene/fr/commands/history/), [`purge`](https://cavo789.github.io/media-hygiene/fr/commands/purge/),
[`review`](https://cavo789.github.io/media-hygiene/fr/commands/review/), [`reports`](https://cavo789.github.io/media-hygiene/fr/commands/reports/),
[`crosscheck`](https://cavo789.github.io/media-hygiene/fr/commands/crosscheck/), [`config`](https://cavo789.github.io/media-hygiene/fr/commands/config/),
[`launcher`](https://cavo789.github.io/media-hygiene/fr/commands/launcher/), [`classify`](https://cavo789.github.io/media-hygiene/fr/commands/classify/),
[`review-sort`](https://cavo789.github.io/media-hygiene/fr/commands/review-sort/), [`sort`](https://cavo789.github.io/media-hygiene/fr/commands/sort/),
[`album`](https://cavo789.github.io/media-hygiene/fr/commands/album/), [`places`](https://cavo789.github.io/media-hygiene/fr/commands/places/),
[`inventory`](https://cavo789.github.io/media-hygiene/fr/commands/inventory/), [`tags`](https://cavo789.github.io/media-hygiene/fr/commands/tags/),
[`search`](https://cavo789.github.io/media-hygiene/fr/commands/search/), [`xmp`](https://cavo789.github.io/media-hygiene/fr/commands/xmp/),
[`people`](https://cavo789.github.io/media-hygiene/fr/commands/people/). Vous hésitez ?
[Quelle commande ?](https://cavo789.github.io/media-hygiene/fr/reference-commands/#quelle-commande-)

**Référence** : [les mots de ce guide](https://cavo789.github.io/media-hygiene/fr/reference-glossary/),
[commandes et options](https://cavo789.github.io/media-hygiene/fr/reference-commands/),
[points de montage](https://cavo789.github.io/media-hygiene/fr/reference-mount-points/),
[comment vos photos restent en sécurité](https://cavo789.github.io/media-hygiene/fr/reference-safety/),
[fichiers compagnons](https://cavo789.github.io/media-hygiene/fr/reference-sidecars/),
[dépannage](https://cavo789.github.io/media-hygiene/fr/reference-troubleshooting/),
[le classeur d'inventaire](https://cavo789.github.io/media-hygiene/fr/reference-inventory/),
[les tags](https://cavo789.github.io/media-hygiene/fr/reference-tags/),
[les personnes](https://cavo789.github.io/media-hygiene/fr/reference-people/),
[utilisation avancée](https://cavo789.github.io/media-hygiene/fr/reference-advanced/).

**Pour les développeurs** : [construire l'image, le devcontainer, les versions](https://cavo789.github.io/media-hygiene/fr/development/).

## La commande complète

Ce que `mh clean` tape pour vous, écrit en entier : deux dossiers, le cache, les rapports, la
configuration, le journal et la quarantaine. Utile sans `mh` (un script, un autre shell). Elle
nettoie ; pour un audit, ajoutez `:ro` à vos dossiers et écrivez `audit` au lieu de `clean`.

```powershell
mkdir -Force "$HOME\media-hygiene\reports", "$HOME\media-hygiene\config", "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
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
`cavo789/media-hygiene:0.4.0` en fixe une.

### Vous veniez de media-dedup ?

Jusqu'à la version 0.2, l'outil s'appelait **media-dedup** (`cavo789/media-dedup`) ; il
s'appelle media-hygiene depuis la version 0.3.0. Rien de ce que vous avez n'est perdu :

- Écrivez `cavo789/media-hygiene` au lieu de `cavo789/media-dedup` dans vos commandes :
  l'ancienne image n'est plus sur Docker Hub (Docker répond alors *pull access denied*).
- Gardez vos dossiers et vos volumes : `$HOME\media-dedup\journal`, `media-dedup-cache` et
  les autres vous appartiennent, quel que soit leur nom. Continuez à les écrire dans vos
  options `-v` : `undo`, `history` et le cache y retrouvent tout.
- Les variables d'environnement `MEDIA_DEDUP_…` ne sont plus lues depuis la version 0.4.0 :
  renommez-les `MEDIA_HYGIENE_…`.

## Licences

L'outil lui-même est sous [licence MIT](LICENSE). L'image Docker contient aussi le travail
d'autres personnes, chacun sous sa propre licence :

| Composant | Licence |
|---|---|
| [x265](https://github.com/Multicorewareinc/x265) (lecture des HEIC, fourni par `pillow-heif`) | GPL-2.0-or-later |
| [libheif](https://github.com/strukturag/libheif), [libde265](https://github.com/strukturag/libde265) (HEIC, fournis par `pillow-heif`) | LGPL-3.0-or-later |
| [FFmpeg](https://ffmpeg.org/legal.html) (`ffprobe`, `ffmpeg`, compilés sans `--enable-gpl`) | LGPL-2.1-or-later |
| [LibRaw](https://www.libraw.org/) (fichiers RAW, via `rawpy`) | LGPL-2.1 ou CDDL-1.0 |
| [Czkawka](https://github.com/qarmin/czkawka) (`czkawka_cli`, le second avis de `crosscheck`) | MIT |
| Les villes de [GeoNames](https://www.geonames.org/) (`geo/data`, voir son `ATTRIBUTION.txt`) | CC BY 4.0 |
| [Leaflet](https://leafletjs.com/) (la carte de `places`) | BSD-2-Clause |
| Python, Pillow, NumPy, ONNX Runtime et les autres paquets Python, avec les bibliothèques que leurs wheels embarquent (libjpeg, libpng, libtiff, libwebp, OpenBLAS…) | PSF, MIT, BSD, Apache-2.0 et licences permissives semblables |
| Les paquets Debian de l'image de base `python:3.14-slim` | Leurs propres licences (`/usr/share/doc/*/copyright`) |

À cause de x265, l'image **dans son ensemble** relève de la GPL quand vous la redistribuez.
Chaque composant est la version d'origine, non modifiée, épinglée dans `Dockerfile` et
`uv.lock` : ses sources sont celles de cette version. Les modèles de visages de `people` ne sont
pas dans l'image : ils sont téléchargés à la première utilisation depuis
[OpenCV Zoo](https://github.com/opencv/opencv_zoo) (YuNet : MIT, SFace : Apache-2.0).
