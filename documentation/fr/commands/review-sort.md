# `review-sort` : nommer les événements dans votre navigateur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `review-sort` · 🇬🇧 [English](../../en/commands/review-sort.md)

## En bref

**Nommer vos événements en regardant leurs photos, un événement à la fois, au clavier, plutôt
que dans un tableur.**

Le [classeur](../reference-glossary.md#classeur) de [`classify`](classify.md) est fait pour renommer en masse, pas pour *regarder*
des photos. `review-sort` montre **un événement à la fois** dans votre navigateur, avec ses
photos, sa proposition et un champ pour le nommer. Vos choix sont enregistrés à côté de la
proposition ; [`sort`](sort.md) les applique par-dessus le classeur.

**Quand** : facultatif, entre `classify` et `sort`, quand il y a beaucoup d'événements à nommer.
Le classeur seul suffit, et les deux peuvent servir ensemble.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées, ni le classeur : montez les photos en `:ro`. |
| Il faut | `/reports` (l'exécution de `classify`), vos dossiers (pour montrer les photos), et `-p 127.0.0.1:8088:8088`. |
| Écrit | `sort-decisions.json`, à côté de `plan.json` dans le dossier de l'exécution de `classify`. |
| Annuler | `Suppr` dans la page reprend un choix ; le classeur décide alors à nouveau. |
| Avec `mh` | `mh review-sort` : le port est publié pour vous. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr review-sort
```

Il compte les événements (*412 événements à décider : 260 avec une proposition sûre (un clic),
152 à regarder*), puis affiche l'adresse de la page : Ctrl+clic dessus. Ctrl+C, ou fermer son onglet, l'arrête ; la
fois suivante, il reprend.

## Les touches principales

| Touche | Rôle |
|---|---|
| `Entrée` | Accepter le nom et la catégorie, puis passer à l'événement suivant encore à décider. |
| `N` / `P` | Événement suivant ou précédent, sans décider. `U` : événement suivant encore à décider. |
| `V` | Accepter d'un coup toutes les propositions sûres ; `Maj`+`Z` reprend ce lot. |
| `E` / `C` | Écrire dans le champ du nom / de la catégorie ; `Échap` en sort. |
| `Maj`+`S` | Laisser tout l'événement où il est. |
| `Espace`, `O`, `S` | Sélectionner des photos, les envoyer vers une autre catégorie, ou les laisser où elles sont. |
| `Suppr` | Reprendre le choix fait ici. |
| `Z` | Agrandir la photo. |

## Options

| Option | Rôle |
|---|---|
| `CLASSEUR` | Le classeur de `classify` ; celui du dernier `classify` par défaut. |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- **Le classeur n'est jamais modifié** (Excel l'a peut-être ouvert). Vous pouvez continuer à le
  modifier : chaque choix de la page retient ce que disait le classeur au moment où vous l'avez fait.
- **Un conflit n'est jamais réglé en silence** : si le classeur a été changé depuis, sur le même
  événement ou fichier, pour autre chose, `sort` refuse et liste les deux valeurs ; la page les
  montre en rouge.
- **Relancez `classify`** : vos choix de la page sont repris dans les cellules jaunes du nouveau
  classeur, comme vos modifications.

## Pour aller plus loin

- [Trier, étape 11 : nommer les événements dans votre navigateur](../sort/11-name-events-in-the-browser.md)
- Ensuite : [`sort`](sort.md).

## L'aide intégrée

<details>
<summary><code>review-sort --help</code></summary>

<!-- capture: help-review-sort.txt -->
```text
 Utilisation : media-hygiene review-sort [OPTIONS] [workbook]

 🔒 Lecture seule : ne modifie jamais vos photos. Nommer les événements de la
 proposition de classify un par un, dans votre navigateur.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  Le classeur de classify ; celui du dernier classify   │
│                        par défaut.                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut :  port dans config.toml,     │
│                                     8088.                                    │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
