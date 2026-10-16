# 1. Votre premier audit

[Documentation](../README.md) › Pour commencer, étape 1 sur 3 · 🇬🇧 [English](../../en/start/01-first-audit.md)

Dans cette première étape, vous demandez à l'outil de regarder **un seul dossier** de photos et
de vous dire ce qu'il y trouve. Rien n'est modifié : un audit ne fait que lire. Avec `:ro`
ci-dessous, ce n'est pas qu'une promesse : le système lui-même interdit toute modification
([comment vos photos restent en sécurité](../reference-safety.md)).

## Ce qu'il vous faut

- Docker installé et démarré : l'[étape 0](00-install-docker.md) explique comment, sous Windows ou
  Linux.
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
| `--locale fr` | Parle français. Sans cette option, l'outil parle anglais ; l'[étape 7 du nettoyage](../clean/07-configuration-file.md) vous évitera de la retaper. |
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

### Combien de temps dure le premier audit

Le premier audit décode chaque photo une fois : sur une grosse bibliothèque, et à travers Docker
sous Windows, cela prend des minutes, parfois des heures. Quand plus de 500 fichiers sont à
vérifier, l'outil chronomètre ses 20 premières secondes, puis dit une fois combien de temps
prendra le reste, arrondi vers le haut :

```text
⏳ 23.412 photos et 318 vidéos à vérifier pour la première fois : environ 45 min. Le cache
n'est pas gardé : le prochain audit les vérifiera tous à nouveau (voir le conseil à la fin).
```

Sans cache, comme ici, chaque audit repart de zéro : l'[étape suivante](02-keep-the-cache.md)
garde ce travail, et les audits suivants prennent quelques secondes.

## Lire le résultat

Voici ce qu'affiche un audit de `C:\Photos` (une bibliothèque de démonstration, dont les images
sont dessinées par un programme) :

<!-- capture: audit-photos.txt -->
```text
🔒 Lecture seule : vos photos et vidéos ne sont pas touchées.
──────────────────────────────────── Audit ─────────────────────────────────────
Résumé de l'audit
┌──────────────────────────────────────────────────────────┬────────┐
│ Fichiers média analysés                                  │     61 │
│ Groupes de fichiers identiques                           │      8 │
│ Copies en trop, à mettre de côté                         │     12 │
│ Espace libérable                                         │ 3,4 Mo │
│ Fichiers cassés (vides ou illisibles)                    │      0 │
│ Quasi-doublons (déplacés seulement avec --tier near)     │      2 │
│ Vidéos réencodées (déplacées seulement avec --tier near) │      1 │
│ Rafales (déplacées seulement si écartées avec 'review')  │      3 │
│ Durée                                                    │    2 s │
└──────────────────────────────────────────────────────────┴────────┘

Dossiers partageant des fichiers identiques
• 8 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\Ancien téléphone (des copies que 'clean' déplace en
  quarantaine), 2,3 Mo à libérer avec 'purge'. C:\Photos\Ancien téléphone ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\2019\Vacances
  à la mer.
• 3 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\2019\Nouveau dossier (des copies que 'clean' déplace en
  quarantaine), 872,9 Ko à libérer avec 'purge'. C:\Photos\2019\Nouveau dossier
  ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 1 fichier est présent plusieurs fois dans C:\Photos\2019\Vacances à la mer :
  un exemplaire est gardé (292,0 Ko à libérer).

Ce que vous pouvez faire
✅ 12 copies identiques, 3,4 Mo : sans risque, une commande.
👀 3 groupes de quasi-doublons : 1 sûr, 2 à regarder (~1 min dans « review
--near ») ; « clean --tier near » déplace les sûrs.
🎞️ 3 rafales : facultatif, ~2 min dans 'review' ; les rafales non revues sont
gardées entières.

👉 Et maintenant : lancez 'clean' pour mettre 3,4 Mo de copies de côté. La
commande ajoute /journal, /quarantine : des dossiers de votre profil.
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
💡 Choisissez les dossiers qui gardent leurs copies : folders.preferred dans
config.toml, ou --prefer.
⚙️  À régler une fois : -v "<un de vos dossiers>:/reports" (rapports HTML); -v
media-hygiene-cache:/cache (prochains audits bien plus rapides); -e
TZ=Europe/Brussels (heures dans votre fuseau, pas en UTC).
(2 autres conseils : ajoutez --verbosity verbose pour les voir.)
```

D'abord le tableau (un mot inconnu ? [les mots de ce guide](../reference-glossary.md)) :

| Ligne | Ce qu'elle veut dire |
|---|---|
| Fichiers média analysés | Toutes les photos, fichiers RAW et vidéos trouvés. Les fichiers compagnons (`.xmp`, …) ne sont pas comptés. |
| Groupes de fichiers identiques | Combien de photos ou vidéos distinctes existent en plusieurs copies identiques. |
| Copies en trop, à mettre de côté | Les fichiers qu'un nettoyage mettrait en quarantaine (rien n'est effacé). Pour chaque photo présente plusieurs fois, un exemplaire est gardé et les autres sont en trop : une photo rangée dans 3 dossiers donne 2 copies en trop. |
| Espace libérable | La taille totale de ces copies en trop. |
| Fichiers cassés | Les fichiers vides (0 octet) et ceux qui ne s'ouvrent pas (JPEG tronqué, vidéo abîmée). |
| Fichiers compagnons orphelins | Seulement s'il y en a : des [fichiers compagnons](../reference-sidecars.md) restés sans leur photo. |
| Quasi-doublons | La même photo enregistrée à nouveau : réduite, recompressée. Ce ne sont pas des fichiers identiques, ils restent en place sauf si vous le demandez ([étape 11 du nettoyage](../clean/11-near-duplicates.md)). |
| Rafales | Des photos prises à quelques secondes d'intervalle. Jamais touchées, sauf si vous choisissez ([étape 10 du nettoyage](../clean/10-review-bursts.md)). |
| Durée | Le temps qu'a pris tout l'audit. Avec `--verbosity verbose`, une ligne sous le tableau le détaille par étape (*Temps par étape : liste 1,2 s · vérifications 3,4 s · …*), puis le rapport dit le temps pris pour l'écrire. |

Avec `--verbosity verbose` (une option globale, avant `audit`), l'*Inventaire* suit : ce que vos
photos et vos vidéos disent d'elles-mêmes. Combien de photos ont une date de prise de vue (écrite
par l'appareil), combien de vidéos sont datées par leurs balises, combien de fichiers portent une
position GPS, les formats des photos et la durée totale des vidéos. Rien n'y est jugé : ce sont
des faits que les fichiers contiennent, comptés pour vous. La commande
[`inventory`](../reference-inventory.md) les liste fichier par fichier.

Puis *Dossiers partageant des fichiers identiques* : chaque phrase décrit deux dossiers qui
contiennent les mêmes fichiers. Les copies du premier dossier sont **gardées** ; celles du
second sont les copies que `clean` mettra en quarantaine, et la phrase se termine par la place
qu'elles occupent. C'est une prévision : l'audit n'a rien déplacé. Les paires qui libèrent le
plus d'espace viennent en premier.

- *« … ne contient rien d'autre : c'est entièrement une copie de … »* : le second dossier ne
  contient que des copies de fichiers gardés ailleurs. C'est le cas le plus rassurant : ce dossier
  est une simple copie.
- *« … est présent plusieurs fois dans … : un exemplaire est gardé »* : le même fichier deux
  fois dans un dossier, comme `IMG_0101.jpg` et `IMG_0101 (1).jpg`.

Ce n'est pas le dossier que vous voulez garder ? L'[étape 5 du nettoyage](../clean/05-choose-the-kept-copy.md) montre
comment choisir.

Puis *Ce que vous pouvez faire* : trois lignes au plus, chacune avec ce qu'elle rapporte et ce
qu'elle vous coûte.

| Ligne | Ce qu'elle signifie |
|---|---|
| ✅ copies identiques | Sans risque, une commande : `clean` les met de côté, `undo` les ramène. |
| 👀 quasi-doublons | Des groupes à regarder avant de les déplacer, avec une estimation du temps que cela prend ([étape 11 du nettoyage](../clean/11-near-duplicates.md)). |
| 🎞️ rafales | Facultatif : une rafale que vous ne revoyez pas est gardée entière ([étape 10 du nettoyage](../clean/10-review-bursts.md)). |

La ligne 👉 donne l'étape qui vient logiquement maintenant, suivie de sa **commande complète**,
prête à coller : vos dossiers sur les mêmes points de montage (sans `:ro` pour une commande qui
les modifie), les dossiers que vous montez déjà, et ceux dont la commande suivante a besoin et
qui manquaient à celle-ci (comme `/journal` et `/quarantine`, dans un dossier `media-hygiene` de
votre profil, créés d'abord par `mkdir`). Elle est écrite pour PowerShell quand vos dossiers sont
des chemins Windows (`C:\…`), pour bash sinon : les exemples de ce guide montrent celle pour
PowerShell (`C:\Photos`).

Puis deux astuces 💡 au plus, la plus utile d'abord ; les options à régler une fois (le cache,
votre fuseau horaire, un dossier de rapports) partagent une seule ligne ⚙️. Une dernière ligne
dit combien d'astuces ont été omises : ajoutez `--verbosity verbose` pour les voir toutes. Les
étapes suivantes de ce guide les suivent une à une.

> 🔒 Rien n'a changé dans `C:\Photos` : un audit n'écrit jamais, et `:ro` s'en est assuré.

---

← [0. Installer Docker](00-install-docker.md) · [Documentation](../README.md) · Suivant : **[2. Garder le cache](02-keep-the-cache.md)** →
