# `history` : ce qu'a fait chaque exécution

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `history` · 🇬🇧 [English](../../en/commands/history.md)

## En bref

**Voir ce que chaque exécution a fait, et trouver le nom à donner à `undo` ou à `purge`.**

`history` lit le [journal](../reference-glossary.md#journal) et liste les exécutions, de la plus récente à la plus ancienne : la
commande qui a fait chacune, ce qu'elle a supprimé, libéré, déplacé et mis de côté, et combien
de fichiers ont été restaurés depuis.

**Quand** : après un `clean`, un `sort`, un `album` ou un `xmp --apply`, avant un `undo` ou un
`purge`.

**Essayer** :

```powershell
docker run --rm -it -v "$HOME\media-hygiene\journal:/journal" cavo789/media-hygiene --locale fr history
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : il ne lit que le journal. |
| Il faut | `/journal`, le dossier où `clean` écrit. |
| Écrit | Rien. |
| Annuler | Rien à annuler. |
| Avec `mh` | `mh history` ; depuis la page d'accueil, *Historique et annulation* › **Voir ce qu'a fait chaque exécution** affiche le même tableau dans la page elle-même (rien n'est écrit dans le terminal), avec la ligne `mh undo <run>` à copier pour chaque exécution. |

## Lancer

```powershell
docker run --rm -it -v "$HOME\media-hygiene\journal:/journal" cavo789/media-hygiene --locale fr history
```

Aucun dossier de photos n'est nécessaire. Sans `/journal`, il dit *Pas de montage /journal :
aucun historique à afficher*.

## Lire le tableau

| Colonne | Ce qu'elle veut dire |
|---|---|
| Exécution | Le nom de l'exécution, sa date et son heure (`20261011-100826`) : ce que prennent `undo` et `purge`. |
| Commande | `clean`, `sort`, `album`, `xmp`… |
| Supprimés, Libéré | Les fichiers supprimés (fichiers vides, `--delete`) et la place qu'ils ont libérée. |
| En quarantaine | Les fichiers déplacés en quarantaine : leur place est libérée par `purge`. |
| Déplacés, Liés, Compagnons | Affichées dès qu'une exécution a déplacé des fichiers vers un autre de vos dossiers (`sort`), créé des liens (`album`) ou écrit des fichiers compagnons (`xmp`). |
| Dossiers supprimés | Affichée dès qu'une exécution a supprimé les dossiers qu'elle a laissés vides (`clean`, `sort`) ; `undo` les recrée. |
| Restaurés | Combien de fichiers `undo` a ramenés depuis. |

Par exemple, après un nettoyage, son annulation, puis un nouveau nettoyage :

```text
Exécutions (les plus récentes d'abord)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Exécution       ┃ Commande ┃ Supprimés ┃ Libéré ┃ En quarantaine ┃ Restaurés ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 20261011-100826 │ clean    │         1 │      0 │             41 │         0 │
│ 20261011-100820 │ clean    │         1 │      0 │             35 │        36 │
└─────────────────┴──────────┴───────────┴────────┴────────────────┴───────────┘
```

## Bon à savoir

- `history` n'a pas d'option.
- Le journal est petit et rend `undo` possible : ne le supprimez jamais tant que vous pourriez
  encore vouloir restaurer une exécution.
- [`status`](status.md) donne une vue plus courte : ce qui est encore annulable, et l'étape suivante.

## Pour aller plus loin

- [9. Annuler, historique, purge](../clean/09-undo-history-purge.md#voir-ce-qui-a-été-fait--history)
- Ensuite : [`undo`](undo.md) une exécution, [`purge`](purge.md) sa quarantaine.

## L'aide intégrée

<details>
<summary><code>history --help</code></summary>

<!-- capture: help-history.txt -->
```text
 Utilisation : media-hygiene history [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Liste les exécutions et ce
 qu'elles ont fait.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
