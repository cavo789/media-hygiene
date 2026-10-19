# `browse` : parcourir vos dossiers et mettre des photos de côté

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `browse` · 🇬🇧 [English](../../en/commands/browse.md)

## En bref

**Parcourir vos dossiers comme dans l'Explorateur, et mettre de côté les photos dont vous ne
voulez plus.**

`browse` ouvre votre photothèque dans votre navigateur : l'arborescence de vos dossiers à gauche
(chacun avec son nombre de photos et de vidéos et sa taille), les photos et vidéos du dossier
choisi à droite. Choisissez-en et mettez-les de côté : le prochain
[`clean --decisions`](clean.md) les déplace en quarantaine, journalisé et annulable. Supprimer
dans l'Explorateur ne laisse aucune trace ; ici, chaque retrait peut être annulé.

**Quand** : après un [`audit`](audit.md) : la page montre ce que l'audit a lu. Pas besoin de
[`tags`](tags.md).

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr browse
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées par la page : montez-les en `:ro`. |
| Il faut | `/cache` (les fichiers du dernier audit), vos dossiers (pour montrer les photos), `/reports` (pour garder ce que vous mettez de côté), et `-p 127.0.0.1:8088:8088` pour la page. |
| Écrit | Les petits aperçus de la grille, dans le cache ; les photos mises de côté, dans `decisions.json` des rapports. |
| Annuler | Rien à annuler dans la page : [`clean --decisions`](clean.md) déplace les photos mises de côté, [`undo`](undo.md) les remet. |
| Avec `mh` | `mh browse`. |

## Lancer

```powershell
mh browse
```

Votre navigateur s'ouvre sur la page (sinon : `http://127.0.0.1:8088/`).

- **L'arborescence** : vos dossiers montés, ouverts ; les dossiers en dessous, fermés (▸ en ouvre
  un). Cliquez un dossier : ses photos et vidéos apparaissent, triées par nom ou par date
  (**Trier par**).
- **Regarder** : Entrée ou un double clic montre une image en grand, une vidéo se lit ; ← et →
  passent à la précédente et à la suivante, comme dans l'application Photos ; Échap ferme.
- **Choisir** : un clic choisit un fichier, Ctrl+clic en ajoute ou en retire un, Maj+clic une
  plage, Espace le fichier en cours, Ctrl+A tout le dossier.
- **Mettre de côté** : Suppr, ou **Mettre de côté les fichiers choisis**. Le choix est enregistré
  aussitôt dans `decisions.json` de vos rapports, relu sur le disque et affiché avec son nombre et
  sa taille : *37 fichiers mis de côté (412 Mo), enregistrés dans … : 'clean --decisions' les
  déplace en quarantaine, et s'en souvient : si l'un d'eux revient (une nouvelle copie depuis le
  téléphone), l'audit le propose à nouveau.* (Voir [Ce que vous avez mis de côté reste de côté](../clean/09-undo-history-purge.md#ce-que-vous-avez-mis-de-côté-reste-de-côté).)
  Ces fichiers portent une étiquette rouge *à mettre de côté* ;
  **Retirer de la mise de côté** en retire les fichiers choisis.
- **Chercher par mots** ouvre la page [`search`](search.md), sur le même serveur : ce que vous y
  mettez de côté va dans le même fichier.

Ctrl+C arrête la page ; quand des fichiers sont mis de côté, `browse` propose l'étape suivante :

```powershell
mh clean --decisions
```

Il dit combien de fichiers et d'octets partent (à part des doublons), demande, puis les déplace en
quarantaine, journalisé : `mh undo` les remet, `mh purge` libère la place.

**Ouverte depuis l'[accueil](home.md)** (`mh` seul, puis l'étape *Parcourir vos dossiers*) : dès
que quelque chose est mis de côté, un bouton **Appliquer maintenant** apparaît sous la ligne
enregistrée. Il ferme la page et `mh` lance l'étape de l'accueil qui applique vos choix
(`mh clean --decisions`, avec `--tier near` si vous avez aussi revu des quasi-doublons), avec sa
question habituelle, dans la fenêtre où `mh` tourne (PowerShell sous Windows) ; puis l'accueil revient. Ouverte par
`mh browse` seul, pas de bouton : tapez la commande ci-dessus. Le bouton demande un `mh` écrit
par cette version (`mh update` le réécrit).

## Options

| Option | Rôle |
|---|---|
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- Rien n'est supprimé depuis la page, et rien ne bouge avant `clean --decisions`. Un fichier
  modifié depuis votre choix est laissé en place et listé dans le rapport du nettoyage ; un
  fichier d'un dossier protégé fait refuser tout le fichier, comme partout.
- La page liste ce que le dernier [`audit`](audit.md) a lu : relancez-le pour voir les nouveaux
  fichiers.
- Sans `/reports` (ou avec un dossier où l'outil ne peut pas écrire), mettre de côté dit pourquoi
  et n'enregistre rien ; regarder fonctionne toujours.
- Une vidéo montre ses premières images dans la grille quand votre navigateur sait lire son
  format (MP4, MOV) ; les autres affichent « Pas d'aperçu » et s'ouvrent en original.

## Aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
- [`search` : mettre de côté les photos trouvées par un mot, une personne, une
  année](search.md#mettre-des-photos-de-côté)

## L'aide intégrée

<details>
<summary><code>browse --help</code></summary>

<!-- capture: help-browse.txt -->
```text
 Utilisation : media-hygiene browse [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Parcourir vos dossiers dans
 votre navigateur, comme dans l'Explorateur, et mettre des photos de côté ;
 'clean --decisions' les déplace ensuite.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut : 8088.                       │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
