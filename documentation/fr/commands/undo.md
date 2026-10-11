# `undo` : défaire une exécution

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `undo` · 🇬🇧 [English](../../en/commands/undo.md)

`undo` restaure chaque fichier d'une exécution, tel que le journal l'a noté : les fichiers d'un
`clean` reviennent de la quarantaine (ou sont reconstruits depuis la copie gardée), les fichiers
d'un `sort` retournent dans leurs dossiers, les liens d'un `album` et les fichiers compagnons de
`xmp` sont retirés.

## En bref

| | |
|---|---|
| Vos photos | ✋ Agit : remet les fichiers là où ils étaient, jamais par-dessus un autre fichier. |
| Il faut | `/journal`, vos dossiers **sans** `:ro`, et `/quarantine` quand l'exécution y a déplacé des fichiers. |
| Conseillé | Les mêmes options `-v` que l'exécution que vous annulez. |
| Écrit | Chaque restauration, dans le journal de l'exécution (`history` les compte). |
| Annuler | Pour refaire, relancez la commande ([`clean`](clean.md), [`sort`](sort.md)…). |
| Avec `mh` | `mh undo`, `mh undo <exécution>`. |

## Quand l'utiliser

- Vous avez changé d'avis après un `clean`, un `sort`, un `album` ou un `xmp --apply`.
- Une photo que vous vouliez est en quarantaine : annulez cette exécution, puis nettoyez à nouveau
  avec d'autres options.

## Lancer

La même commande que l'exécution, avec `undo` comme dernier mot :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr undo
```

Sans nom, `undo` restaure l'exécution **la plus récente** ; `undo <exécution>` restaure
celle-là. Les noms des exécutions viennent de [`history`](history.md), de [`status`](status.md)
et des dernières lignes de chaque exécution.

## Ce qu'il fait, exécution par exécution

| Exécution | Ce que fait `undo` |
|---|---|
| `clean` | Chaque fichier en quarantaine retourne à sa place ; chaque copie supprimée (`--delete`) ou fichier vide est reconstruit depuis la copie gardée, date comprise. Les dossiers de quarantaine qu'il laisse vides disparaissent. |
| `sort` | Les fichiers reviennent, les dossiers que le tri avait supprimés reviennent, ceux qu'il avait créés disparaissent. Un tri relancé après une interruption est annulé **en entier**, du plus récent au plus ancien, après une seule question. |
| `album` | Ses liens, son fichier `.media-hygiene-album` et ses dossiers disparaissent ; les originaux ne sont pas touchés. |
| `xmp` | Les fichiers compagnons qu'il a créés disparaissent ; ceux qu'il a complétés sont remis octet pour octet. |

## Options

| Option | Rôle |
|---|---|
| `EXÉCUTION` | L'exécution à annuler (voir `history`) ; la plus récente par défaut. Pour un tri, toutes les exécutions du même classeur. |
| `--yes`, `-y` | Ne pas demander avant d'annuler plusieurs exécutions d'un tri. |

## Bon à savoir

- **Jamais par-dessus un autre fichier, jamais au hasard** : un fichier déjà revenu, ou dont la
  copie a disparu, est laissé tel quel et listé avec la raison.
- `undo` vérifie les montages **avant** de changer quoi que ce soit : sans le même `/journal`,
  avec des dossiers en `:ro`, ou sans la `/quarantine` utilisée par l'exécution, il refuse et
  nomme l'exécution.
- Un lien d'album dont l'original a été supprimé ou déplacé depuis est peut-être le dernier
  exemplaire de la photo : `undo` le garde et le dit. Un fichier compagnon modifié depuis que
  `xmp` l'a écrit est gardé aussi.
- Après un [`purge`](purge.md), les fichiers de cette quarantaine ne peuvent plus revenir.

## Pour aller plus loin

- [9. Annuler, historique, purge](../clean/09-undo-history-purge.md#annuler-un-nettoyage--undo)
- [Trier, étape 7 : changer d'avis](../sort/07-sort.md#changer-davis),
  [étape 12 : annuler un album](../sort/12-albums.md#lannuler)
- [Comment vos photos restent en sécurité](../reference-safety.md)

## L'aide intégrée

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Utilisation : media-hygiene undo [OPTIONS] [run_id]

 Restaure chaque fichier d'une exécution, depuis la copie conservée, la
 quarantaine ou là où il a été déplacé ; supprime les liens d'un album.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution à annuler (voir 'history') ; la plus récente  │
│                      par défaut. Pour un tri, tous les passages du même      │
│                      classeur.                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Ne pas demander de confirmation avant d'annuler plusieurs  │
│                   passages d'un tri (remplace sort.confirm).                 │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
