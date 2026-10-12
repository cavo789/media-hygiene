# `review` : choisir les meilleures photos, dans votre navigateur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `review` · 🇬🇧 [English](../../en/commands/review.md)

## En bref

**Ne garder que les meilleures photos de vos rafales, et trancher les quasi-doublons, en les
regardant en grand dans votre navigateur.**

Les [rafales](../reference-glossary.md#rafale) (cinq, dix, vingt photos en quelques secondes) et les [quasi-doublons](../reference-glossary.md#quasi-doublon) (une photo
réenregistrée, plus petite) ne sont pas des fichiers identiques : c'est à vous de dire lesquels
garder. `review` vous les montre **un à la fois** et vous choisissez au clavier. Chaque choix
est enregistré aussitôt dans `decisions.json` ; `clean --decisions` les applique ensuite.

**Quand** : après un audit qui a trouvé des rafales (ou des quasi-doublons, avec `--near`),
avant `clean --decisions`.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : la page ne fait que les montrer. Montez-les en `:ro`. |
| Il faut | Vos dossiers, `/reports` (où `decisions.json` est enregistré), et `-p 127.0.0.1:8088:8088`. |
| Conseillé | `/cache` (l'audit par lequel il commence prend quelques secondes), `/config`. |
| Écrit | `decisions.json` dans `/reports`, le cache. |
| Annuler | Changez vos choix dans la page, ou supprimez `decisions.json`. |
| Avec `mh` | `mh review`, `mh review --near` : le port est publié pour vous. |

## Deux sortes de tri

| Commande | Ce que vous décidez | Appliqué par |
|---|---|---|
| `review` | **Les rafales**, une à la fois : quelles photos vont en quarantaine. La plus nette vient en premier, celles proposées à l'écart sont marquées ; `→` accepte ce qui est montré. | `clean --decisions` |
| `review --near` | **Les quasi-doublons et vidéos réencodées**, groupe par groupe : comme prévu (`→`), garder l'autre version (`W`), laisser tel quel (`L`). | `clean --tier near --decisions` |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review
```

Il fait d'abord l'audit, puis affiche *✅ Tri prêt, ouvrez http://127.0.0.1:8088/ dans votre
navigateur*. Ctrl+clic dessus. Laissez la fenêtre ouverte : la page tourne tant qu'elle l'est ;
Ctrl+C l'arrête.

`-p 127.0.0.1:8088:8088` ouvre la page à votre ordinateur seulement, personne d'autre sur le réseau.

## Les touches principales

| Touche | Rafales (`review`) | Quasi-doublons (`review --near`) |
|---|---|---|
| `→` | Rafale suivante, telle que montrée | Comme prévu, puis le groupe suivant |
| `←` | Rafale précédente | Groupe précédent |
| `N` | Rafale suivante encore à voir | Groupe suivant encore indécis |
| `1` … `9` | Écarter cette photo, ou la reprendre | — |
| `S` / `A` / `X` | Garder seulement la plus nette / tout garder / écarter toute la rafale | — |
| `W` / `L` / `U` | — | Garder l'autre version / laisser tel quel / revenir à indécis |
| `V` / `G` | Valider d'un coup toutes les rafales évidentes | `G` : toute la paire de dossiers comme prévu |
| `Z` | Annuler le dernier choix | — |

Les listes complètes : [étape 10 du nettoyage](../clean/10-review-bursts.md#étape-5--aller-plus-vite) et
[étape 11 du nettoyage](../clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near).

## Options

| Option | Rôle |
|---|---|
| `--near` | Trier les quasi-doublons et vidéos réencodées au lieu des rafales. |
| `--decisions FICHIER` | Le fichier où les choix sont enregistrés, et repris ; `decisions.json` de `/reports` par défaut. |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même : `-p 127.0.0.1:9000:9000` pour `--port 9000`. |
| `--prefer`, `--protect`, `--exclude` | Comme pour [`audit`](audit.md#options) : donnez à `review` les mêmes qu'à `clean`. |

## Bon à savoir

- **Une preuve, pas une promesse** : après chaque choix, la page relit `decisions.json` sur le
  disque et montre ce qu'il contient (*✔ Enregistré, puis relu sur le disque à 14:32:05*).
- **Arrêtez quand vous voulez** : le `review` suivant ouvre la première rafale encore à voir. Les
  rafales que vous n'avez pas vues ne déplacent rien.
- **Un seul fichier pour tout** : `decisions.json` contient les photos de rafale (`bursts`), les
  quasi-doublons (`near`) et les paires de dossiers d'un rapport (`pairs`) ; chaque tri garde les
  autres.
- Une photo d'un **dossier protégé** n'est jamais proposée ni écartée.
- *port is already allocated* ? Un autre programme utilise 8088 : `-p 127.0.0.1:9000:9000` et
  `review --port 9000`.

## Pour aller plus loin

- [10. Trier les rafales dans votre navigateur](../clean/10-review-bursts.md)
- [11. Quasi-doublons](../clean/11-near-duplicates.md#décider-dans-le-navigateur--review---near)
- [Dépannage : la page de tri ne s'ouvre pas](../reference-troubleshooting.md#la-page-de-tri-ne-souvre-pas)
- Ensuite : [`clean --decisions`](clean.md).

## L'aide intégrée

<details>
<summary><code>review --help</code></summary>

<!-- capture: help-review.txt -->
```text
 Utilisation : media-hygiene review [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Écarter des photos de rafale,
 une série à la fois, au clavier dans votre navigateur ; 'clean --decisions'
 les déplace ensuite.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --near            Passer en revue les quasi-doublons et les vidéos           │
│                   réencodées groupe par groupe au lieu des rafales : comme   │
│                   prévu, garder l'autre version, ou laisser tel quel ; «     │
│                   clean --tier near --decisions » l'applique.                │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --decisions        <path>              Fichier où les décisions sont         │
│                                        enregistrées, et repris au lancement  │
│                                        suivant. Un chemin relatif se trouve  │
│                                        dans le dossier monté sur /reports.   │
│                                        Par défaut : decisions.json.          │
│ --port             <int range> [x>=1]  Port de la page. docker run le publie │
│                                        sous le même numéro sur votre         │
│                                        ordinateur, par exemple -p            │
│                                        127.0.0.1:9000:9000 pour --port 9000. │
│                                        Par défaut : 8088.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
