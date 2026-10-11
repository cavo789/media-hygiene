# `status` : où en suis-je ?

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `status` · 🇬🇧 [English](../../en/commands/status.md)

De retour après quelques jours, vous ne savez plus quelle exécution est en quarantaine, ni si un
tri a été appliqué ? `status` lit les dossiers de l'outil, sans analyser vos photos (environ une
seconde), vous dit où vous en êtes, puis **une** étape suivante, en commande complète.

## En bref

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées, même pas lues : aucune analyse. |
| Il faut | Rien ; il lit ce que vous montez. |
| Conseillé | Les mêmes dossiers de l'outil que pour `clean` : `/reports`, `/journal`, `/quarantine`, `/cache`. |
| Écrit | Rien. |
| Annuler | Rien à annuler. |
| Avec `mh` | `mh status` : chaque dossier est monté pour vous. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr status
```

## Ce qu'il dit

Sous le titre *Où vous en êtes* :

- **le dernier audit ou nettoyage** : quand, et ce qu'il a trouvé ;
- **la quarantaine** : combien de fichiers, quelle place, depuis quand ;
- **les exécutions que `undo` peut encore restaurer**, avec la commande `undo` complète ;
- **les rafales encore à voir** et les décisions de `review` pas encore appliquées ;
- **la dernière proposition de `classify`**, et si `sort` l'a appliquée ;

puis **une** étape suivante, en commande complète prête à coller. Une quarantaine de plus de
30 jours est la première chose qu'il propose de vider avec [`purge`](purge.md).

## Bon à savoir

- `status` n'a pas d'option.
- Un dossier non monté est signalé, jamais une erreur : montez celui qu'il nomme pour en savoir plus.
- Les 30 jours sont `purge_hint_days`, dans la section `[clean]` de `config.toml`.

## Pour aller plus loin

- [9. Annuler, historique, purge : où en suis-je ?](../clean/09-undo-history-purge.md#où-en-suis-je--status)
- [`history`](history.md) : chaque exécution, en détail.

## L'aide intégrée

<details>
<summary><code>status --help</code></summary>

<!-- capture: help-status.txt -->
```text
 Utilisation : media-hygiene status [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Où en suis-je ? Le dernier
 audit, la quarantaine, ce qu'il reste : sans analyse.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
