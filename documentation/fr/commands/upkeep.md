# `upkeep` : l'entretien régulier d'un coup

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `upkeep` · 🇬🇧 [English](../../en/commands/upkeep.md)

## En bref

**Un clic, ou une commande, pour ce que vous faites toutes les quelques semaines.**

`upkeep` lance les étapes de `[routine]` dans `config.toml`, dans cet ordre : `audit` (relit la
bibliothèque, seulement ce qui a changé), `copies` (`clean` : les copies exactes en quarantaine,
après sa question ; `mh undo` les remet), `reports` (la liste rafraîchie) ; `purge` (les exécutions
en quarantaine plus vieilles que `purge_hint_days`, après la question de `purge` pour chacune) ne
tourne que si vous l'ajoutez à `steps`, sinon lancez [`purge`](purge.md) à part. En dernier,
`reread` (`audit --reread`) relit en entier les fichiers lus il y a le plus longtemps,
`reread_gb` par passage, pour trouver un fichier que le disque a abîmé ; elle ne change rien
([Sécurité](../reference-safety.md#un-fichier-abîmé-par-le-disque)). Elle
finit sur une ligne 👉 : ce qui vous attend encore. Sur la [page d'accueil](home.md) : *Lancer
l'entretien régulier*, dans Nettoyer.

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ⚠️ `copies` déplace des fichiers en quarantaine, `purge` efface les vieilles quarantaines : chacune demande d'abord. |
| Il faut | Les mêmes options `-v` que `clean` (ou `mh upkeep`). |
| Écrit | Ce qu'écrit chaque étape. |
| Annuler | `mh undo` pour les copies ; **rien** après une purge. |
| Avec `mh` | `mh upkeep`. |

## Lancer

```powershell
mh upkeep
```

Pour couper une étape, retirez-la de la liste :

```toml
[routine]
steps = ["audit", "copies", "reports", "reread"]
reread_gb = 20
```

Une étape qui échoue arrête la chaîne ; ce qui précède reste fait.

## Bon à savoir

Avant chaque étape qui change des fichiers, une ligne donne leur nombre et la page qui les montre :
*Ensuite, 'clean' met de côté environ 12 copies : le rapport les montre d'abord*, *Ensuite, 'purge'
efface 41 fichiers pour de bon : 'mh undo --pick' les montre en photos d'abord*. Continuer tout droit
reste une touche : la question de l'étape.

Répondre *non* à une question ne saute que cette étape.

## Pour aller plus loin

- [`clean`](clean.md), [`purge`](purge.md), [`audit`](audit.md)

## L'aide intégrée

<details>
<summary><code>upkeep --help</code></summary>

<!-- capture: help-upkeep.txt -->
```text
 Utilisation : media-hygiene upkeep [OPTIONS]

 Lance l'entretien régulier d'un coup, comme listé dans config.toml : audit,
 copies mises de côté, rapports ; chacun demande comme d'habitude.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h      <bool>  Affiche ce message et quitte.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
