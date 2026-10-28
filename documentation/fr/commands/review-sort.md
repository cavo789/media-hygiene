# `review-sort` : désormais la vue 🗂 Événements de `search`

La page de `review-sort` n'existe plus : ses événements, ses choix, ses règles et *Trier cet
événement maintenant* sont la [vue 🗂 Événements de `search`](search.md#les-événements-du-dernier-classify).
Pour cette version, `mh review-sort` ouvre cette vue (une ligne le dit) ; elle disparaît à la
version suivante : utilisez `mh search` et ouvrez **🗂 Événements du dernier classify**. Votre
`sort-decisions.json` continue de servir : la vue le lit et l'écrit comme avant.

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
