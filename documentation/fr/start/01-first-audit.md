# 1. Votre premier audit

[Documentation](../README.md) › Pour commencer, étape 1 sur 3 · 🇬🇧 [English](../../en/start/01-first-audit.md)

Dans cette première étape, vous demandez à l'outil de regarder **un seul dossier** de photos et
de vous dire ce qu'il y trouve. Rien n'est modifié : un audit ne fait que lire.

## Ce qu'il vous faut

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré.
- Un dossier de photos et de vidéos, ici `C:\Photos`.
- Une fenêtre PowerShell (ou un terminal WSL, voir l'[étape 3](03-several-folders.md#depuis-wsl)).

## Lancer l'audit

Copiez cette commande dans PowerShell, avec le chemin de votre propre dossier à la place de
`C:\Photos` :

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene --locale fr audit
```

Le premier lancement télécharge l'outil (quelques centaines de Mo) ; les suivants démarrent tout
de suite.

| Morceau | Ce qu'il veut dire |
|---|---|
| `docker run` | Démarre l'outil dans un conteneur, une petite boîte isolée. |
| `--rm` | Supprime cette boîte quand l'outil se termine : rien ne traîne. |
| `-it` | Relie la boîte à votre fenêtre : couleurs, barres de progression, et questions auxquelles vous pouvez répondre. |
| `-v "C:\Photos:/data/c/Photos:ro"` | Montre votre dossier à l'outil. La boîte ne voit que ce que vous lui donnez avec `-v` : ici `C:\Photos`, qu'elle appelle `/data/c/Photos`. |
| `:ro` | *Read-only*, lecture seule : Docker lui-même interdit toute modification de votre dossier. |
| `cavo789/media-hygiene` | L'outil, tel que publié sur Docker Hub. |
| `--locale fr` | Parle français. Sans cette option, l'outil parle anglais ; l'[étape 7](../clean/07-configuration-file.md) vous évitera de la retaper. |
| `audit` | Ce qu'il faut faire : chercher les doublons et les fichiers cassés. |

## Ce qui s'affiche pendant l'analyse

Chaque étape affiche une ligne de progression et, en dessous en gris, ce qu'elle fait réellement :

```text
⠴ Preuve d'identité (SHA-256 complet) ━━━━━━━━╸━━━━━━━ 11.707/23.907 écoulé 0:00:47 · encore ~0:02:19
  Lit entièrement les candidats restants : même SHA-256 veut dire identiques, octet par octet.
```

- **`11.707/23.907`** : fichiers traités par *cette étape*, sur le nombre qu'elle doit traiter.
- **`écoulé`** : temps passé dans cette étape. **`encore ~…`** : une estimation pour cette étape
  seulement, d'après sa vitesse jusqu'ici. Elle bouge : quelques grosses vidéos la ralentissent,
  des petites photos l'accélèrent.
- **Ctrl+C** arrête à tout moment, sans message d'erreur. Un audit ne modifie jamais rien.

| À l'écran | Ce que l'étape fait réellement |
|---|---|
| Recherche des fichiers médias | Parcourt le dossier et garde les photos, fichiers RAW et vidéos, reconnus à leur extension ([la liste](../clean/06-file-types.md)). Le total n'est pas encore connu : un compteur remplace la barre. |
| Vérification de la lisibilité des fichiers | Repère les fichiers cassés : vides (0 octet), images et fichiers RAW impossibles à décoder (chacun est décodé entièrement), vidéos impossibles à ouvrir. |
| Empreinte des vidéos | Une fois par vidéo, gardé dans le cache : décode quelques images et en calcule les empreintes, pour trouver les [copies réencodées](../clean/11-near-duplicates.md#les-vidéos-aussi--les-copies-réencodées). |
| Comparaison des fichiers de même taille | Deux fichiers ne peuvent être identiques que s'ils ont la même taille. Pour ceux-là, lit leurs premiers et derniers 64 Ko : rapide, et cela en écarte la plupart. |
| Preuve d'identité (SHA-256 complet) | Lit entièrement les candidats restants et calcule leur empreinte SHA-256 : même empreinte, même contenu, octet par octet. L'étape la plus longue avec de grosses vidéos. |

Sur une grosse bibliothèque, le premier audit peut être long : l'[étape suivante](02-keep-the-cache.md)
rend les suivants bien plus rapides.

## Lire le résultat

Voici ce qu'affiche un audit de `C:\Photos` (une bibliothèque de démonstration, dont les images
sont dessinées par un programme) :

<!-- capture: audit-photos.txt -->
```text
──────────────────────────────────── Audit ─────────────────────────────────────
Résumé de l'audit
┌─────────────────────────────────────────────────────────┬────────┐
│ Fichiers média analysés                                 │     59 │
│ Groupes de fichiers identiques                          │      8 │
│ Copies en trop, supprimables                            │     12 │
│ Espace libérable                                        │ 3,4 Mo │
│ Fichiers cassés (vides ou illisibles)                   │      0 │
│ Quasi-doublons (déplacés seulement avec --tier near)    │      1 │
│ Rafales (déplacées seulement si écartées avec 'review') │      3 │
│ Durée                                                   │    1 s │
└─────────────────────────────────────────────────────────┴────────┘

Inventaire
┌────────────────────────────────────────┬──────────────────┐
│ Photos avec une date de prise de vue   │ 57 sur 58 (98 %) │
│ Vidéos datées par leurs balises        │    0 sur 1 (0 %) │
│ Photos et vidéos avec une position GPS │   0 sur 59 (0 %) │
│ Formats des photos                     │ JPEG 55 · HEIF 3 │
│ Durée totale des vidéos                │              8 s │
└────────────────────────────────────────┴──────────────────┘

Dossiers partageant des fichiers identiques
• 8 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\Ancien téléphone (supprimés), gain de 2,2 Mo. C:\Photos\Ancien
  téléphone ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 3 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\2019\Nouveau dossier (supprimés), gain de 864,7 Ko.
  C:\Photos\2019\Nouveau dossier ne contient rien d'autre : c'est entièrement
  une copie de C:\Photos\2019\Vacances à la mer.
• 1 fichier est présent plusieurs fois dans C:\Photos\2019\Vacances à la mer :
  un exemplaire est gardé (gain de 287,5 Ko).

💡 Ajoutez -v "<un de vos dossiers>:/reports" pour obtenir des rapports HTML.
💡 Lancez 'clean' (mêmes options -v, sans :ro) pour libérer 3,4 Mo.
💡 Second avis : lancez Czkawka, un détecteur de doublons indépendant, sur les
mêmes dossiers, puis 'media-hygiene crosscheck' (mêmes options -v) :
docker run --rm -v "C:\Photos:/data/c/Photos:ro" … -C /out/czkawka.json
💡 Choisissez les dossiers qui gardent leurs copies : folders.preferred dans
config.toml, ou --prefer.
💡 Les quasi-doublons et les rafales sont dans le rapport HTML ; 'clean --tier
near' déplace les quasi-doublons en quarantaine.
💡 Triez les rafales au clavier : 'media-hygiene review' (ajoutez -p
127.0.0.1::8080 à docker run).
💡 Ajoutez -v media-hygiene-cache:/cache : les prochains audits seront bien plus
rapides.
```

D'abord le tableau :

| Ligne | Ce qu'elle veut dire |
|---|---|
| Fichiers média analysés | Toutes les photos, fichiers RAW et vidéos trouvés. Les fichiers compagnons (`.xmp`, …) ne sont pas comptés. |
| Groupes de fichiers identiques | Combien de photos ou vidéos distinctes existent en plusieurs copies identiques. |
| Copies en trop, supprimables | Les fichiers qu'un nettoyage supprimerait. Pour chaque photo présente plusieurs fois, un exemplaire est gardé et les autres sont en trop : une photo rangée dans 3 dossiers donne 2 copies en trop. |
| Espace libérable | La taille totale de ces copies en trop. |
| Fichiers cassés | Les fichiers vides (0 octet) et ceux qui ne s'ouvrent pas (JPEG tronqué, vidéo abîmée). |
| Fichiers compagnons orphelins | Seulement s'il y en a : des [fichiers compagnons](../reference-sidecars.md) restés sans leur photo. |
| Quasi-doublons | La même photo enregistrée à nouveau : réduite, recompressée. Ce ne sont pas des fichiers identiques, ils restent en place sauf si vous le demandez ([étape 11](../clean/11-near-duplicates.md)). |
| Rafales | Des photos prises à quelques secondes d'intervalle. Jamais touchées, sauf si vous choisissez ([étape 10](../clean/10-review-bursts.md)). |
| Durée | Le temps qu'a pris tout l'audit. |

Puis l'*Inventaire* : ce que vos photos et vos vidéos disent d'elles-mêmes. Combien de photos
ont une date de prise de vue (écrite par l'appareil), combien de vidéos sont datées par leurs
balises, combien de fichiers portent une position GPS, les formats des photos et la durée totale
des vidéos. Rien n'y est jugé : ce sont des faits que les fichiers contiennent, comptés pour vous.

Puis *Dossiers partageant des fichiers identiques* : chaque phrase décrit deux dossiers qui
contiennent les mêmes fichiers. Les copies du premier dossier sont **gardées**, celles du second
seraient **supprimées**, et la phrase se termine par l'espace libéré. Les paires qui libèrent le
plus d'espace viennent en premier.

- *« … ne contient rien d'autre : c'est entièrement une copie de … »* : le second dossier ne
  contient que des copies de fichiers gardés ailleurs. C'est le cas le plus rassurant : ce dossier
  est une simple copie.
- *« … est présent plusieurs fois dans … : un exemplaire est gardé »* : le même fichier deux
  fois dans un dossier, comme `IMG_0101.jpg` et `IMG_0101 (1).jpg`.

Ce n'est pas le dossier que vous voulez garder ? L'[étape 5](../clean/05-choose-the-kept-copy.md) montre
comment choisir.

Viennent enfin les astuces 💡. Elles proposent quoi ajouter ensuite, et les étapes suivantes de
ce guide les suivent une à une.

> 🔒 Rien n'a changé dans `C:\Photos` : un audit n'écrit jamais, et `:ro` s'en est assuré.

---

[Documentation](../README.md) · Suivant : **[2. Garder le cache](02-keep-the-cache.md)** →
