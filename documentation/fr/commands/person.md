# `person` : qui est sur cette photo — la nommer, ou la mettre de côté

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `person` · 🇬🇧 [English](../../en/commands/person.md)

## En bref

**Une photo montre quelqu'un que la page people ne vous a jamais demandé (« c'est tante
Juliette ») ?** `person` ouvre la page *Identifier quelqu'un* sur cette photo : nommez chaque
visage, puis confirmez, parmi les photos qui lui ressemblent, celles qui sont vraiment cette
personne. La page et ses gestes sont décrits dans
[`people`](people.md#depuis-nimporte-quelle-photo--nommer-ou-mettre-de-côté-quelquun).

La même page s'ouvre depuis le 👤 **Identifier quelqu'un** de la grande vue de chaque page,
depuis la page people (**👤 Nommer quelqu'un depuis une photo**) et depuis la page d'accueil
(*Retrouver*).

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées. Ce que vous mettez de côté va dans `decisions.json`, pour [`clean --decisions`](clean.md). |
| Il faut | `/cache` (l'index) avec les visages d'[`audit --people`](audit.md). |
| Écrit | Les noms dans `config.toml` (`[[people.person]]`), relus et affichés ; un visage tracé à la main (**✏ Tracer un visage manqué par l'outil**) dans l'index, comme décrit dans [`people`](people.md#depuis-nimporte-quelle-photo--nommer-ou-mettre-de-côté-quelquun). |
| Envoie | Rien : les visages restent sur cet ordinateur. |

## Lancer

Dans Windows PowerShell, la photo telle que l'Explorateur montre son chemin (sous les dossiers
montés) :

```powershell
mh person "C:\Photos\2026\IMG_1234.jpg"
```

La console donne l'adresse de la page ; Ctrl+C l'arrête. Un chemin qui n'est pas une photo des
dossiers montés est refusé tout de suite, rien n'est servi.

## L'aide intégrée

<details>
<summary><code>person --help</code></summary>

<!-- capture: help-person.txt -->
```text
 Utilisation : media-hygiene person [OPTIONS] {photo}

 Qui est sur cette photo : nommez chaque visage, puis confirmez les autres
 photos de cette personne, dans votre navigateur.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    photo      <str>  La photo, telle que l'Explorateur montre son chemin   │
│                        (C:\Photos\x.jpg), sous les dossiers montés.          │
│                        [required]                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut :  port dans config.toml,     │
│                                     8088.                                    │
│ --help  -h      <bool>              Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
