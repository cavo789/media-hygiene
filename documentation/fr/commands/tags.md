# `tags` : des mots pour retrouver chaque photo

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `tags` · 🇬🇧 [English](../../en/commands/tags.md)

## En bref

**Donner à chaque photo et vidéo des mots pour la retrouver (ses dossiers, son nom, sa date, son
lieu, ce qu'elle montre), sans toucher aux fichiers.**

`tags` donne à chaque photo et vidéo **des mots pour la retrouver** : les mots parlants de ses
dossiers (« Durbuy », « ours ») et de son nom, sa date (année, mois, saison, fêtes), son lieu,
et, si vous le voulez, ce qu'y voit un modèle de vision local (« gâteau », « bougie », « neige
»). Les mots restent **dans le cache**, jamais dans vos photos ; [`search`](search.md) les
retrouve, [`xmp`](xmp.md) les écrit dans des fichiers compagnons.

**Quand** : après un audit lancé avec le cache ; à nouveau après de nouvelles photos ou un
dossier renommé.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr tags
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | `/cache`, rempli par un [`audit`](audit.md) précédent. |
| Conseillé | Vos dossiers (indispensables pour le modèle de vision, qui lit les photos), `/config` (le modèle, `[tags]`). |
| Écrit | Les mots, dans le cache. |
| Annuler | Rien à annuler ; relancez-le après avoir renommé un dossier ou ajouté une règle. |
| Avec `mh` | `mh tags`. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr tags
```

Sans modèle de vision, il prend quelques secondes : *✅ 52 318 fichiers : 241 906 mots tirés de
leurs dossiers, noms, dates et lieux.*

## D'où viennent les mots

| Source | Mots | Coût |
|---|---|---|
| Dossiers | Les mots des noms de dossiers que vous avez choisis (`2022/Durbuy - ours` donne `Durbuy`, `ours`) ; les dossiers d'appareil, les dates et les petits mots de liaison sont laissés de côté. | Secondes |
| Nom du fichier | Les mots d'un nom que vous avez choisi (`Anniversaire Léa.mp4` donne `Anniversaire`, `Léa`) ; les noms donnés par un appareil ou une application (`IMG_1234`, `VID-20190712-WA0001`), les nombres et les dates ne donnent rien. | Secondes |
| Date | Année, mois, saison, fêtes, et les noms de vos règles `calendar` et `date_range`. | Secondes |
| Lieu | Votre lieu quand la position GPS s'y trouve, puis la ville la plus proche et son pays, hors ligne. | Secondes |
| Modèle de vision | Une phrase et 5 à 10 mots sur ce que montre la photo (facultatif). | Environ 2 s par photo |

## Options

| Option | Rôle |
|---|---|
| `--path CHEMIN` | Seulement les photos sous ce dossier (chemin de l'hôte, tel que vous l'avez monté) ; à répéter pour plusieurs. |
| `--sample N` | Décrire N photos prises au hasard avec le modèle, afficher leurs mots, le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. |
| `--no-describe` | Ne rien demander de nouveau au modèle : les mots des dossiers, noms, dates et lieux, et les descriptions déjà dans le cache. |
| `--yes`, `-y` | Décrire les photos sans demander, quel que soit leur nombre (au-delà de 200, il demande d'abord). |

## Bon à savoir

- **Le modèle de vision** est celui de `[classify.ai]` (`model`, `url`) : chaque photo y est
  envoyée, en JPEG de 768 pixels, et seulement là. Gardez ce serveur sur votre propre ordinateur.
  Sans `model`, rien n'est jamais envoyé.
- **Une photo par ensemble** : les copies identiques partagent leurs mots, une rafale prend ceux de
  sa photo la plus nette ; une vidéo est vue par l'image du milieu ; les petites images et
  vidéos ne sont pas envoyées. `classify` réutilise ensuite ces réponses au lieu de renvoyer les
  photos.
- **Arrêtez quand vous voulez** : Ctrl+C laisse finir les photos en cours de description ; la
  fois suivante reprend où celle-ci s'est arrêtée.
- **Pourquoi pas dans les photos ?** Écrire dans un JPEG change ses octets, son empreinte, et deux
  copies identiques cesseraient de l'être. [`xmp`](xmp.md) écrit des fichiers compagnons à la place.

## Pour aller plus loin

- [Les tags](../reference-tags.md) : chaque source, les réglages, la longue exécution.
- [Trier, étape 8 : un modèle de vision local](../sort/08-subjects-from-a-local-model.md)
- Ensuite : [`search`](search.md), [`xmp`](xmp.md), [`inventory`](inventory.md).

## L'aide intégrée

<details>
<summary><code>tags --help</code></summary>

<!-- capture: help-tags.txt -->
```text
 Utilisation : media-hygiene tags [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Donner à chaque photo des
 mots pour la retrouver : ses dossiers, son nom, sa date, son lieu, et ce qu'y
 voit un modèle de vision local. Gardés dans le cache, jamais dans les photos.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path                 <str>               Seulement les photos sous ce      │
│                                            dossier (chemin de l'hôte, tel    │
│                                            que vous l'avez monté) ; à        │
│                                            répéter pour plusieurs. Par       │
│                                            défaut : tous les fichiers de     │
│                                            l'index.                          │
│ --sample               <int range> [x>=0]  Décrire ce nombre de photos       │
│                                            prises au hasard avec le modèle   │
│                                            local, afficher le temps par      │
│                                            photo et l'estimation d'une       │
│                                            exécution complète, puis          │
│                                            s'arrêter.                        │
│ --no-describe                              Ne rien demander de nouveau au    │
│                                            modèle local : seulement les mots │
│                                            des dossiers, des noms, des dates │
│                                            et des lieux, et les descriptions │
│                                            déjà dans le cache.               │
│ --yes          -y                          Décrire les photos sans demander, │
│                                            quel que soit leur nombre.        │
│ --help         -h                          Affiche ce message et quitte.     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
