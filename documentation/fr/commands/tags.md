# `tags` : des mots pour retrouver chaque photo

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `tags` · 🇬🇧 [English](../../en/commands/tags.md)

## En bref

**Donner à chaque photo et vidéo des mots pour la retrouver (ses dossiers, son nom, sa date, son
lieu, ce qu'elle montre), sans toucher aux fichiers.**

`tags` donne à chaque photo et vidéo **des mots pour la retrouver** : les mots parlants de ses
dossiers (« Durbuy », « ours ») et de son nom, sa date (année, mois, saison, fêtes), son lieu,
et, si vous le voulez, ce qu'y voit un [modèle de vision](../reference-glossary.md#modèle-de-vision) local (« gâteau », « bougie », « neige
»). Les mots restent **dans le cache**, jamais dans vos photos ; [`search`](search.md) les
retrouve, [`xmp`](xmp.md) les écrit dans des [fichiers compagnons](../reference-glossary.md#fichier-compagnon).

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

### Depuis la page d'accueil

Sur la page d'accueil (`mh`), le bouton **Dans cette page** à côté de *Donner des mots à vos
photos* lance `tags` sans la console. Il écrit d'abord les mots des dossiers, des noms, des dates
et des lieux (quelques secondes), puis montre ce que coûterait le modèle de vision : *40 099
photos à décrire avec qwen2.5vl:7b, environ 21 h 27 min*. Choisissez **Décrire maintenant**,
**Décrire pendant 1 h** (il s'arrête tout seul) ou **Pas maintenant**. Pendant la description, la
page montre les photos décrites, le rythme et le temps restant ; **Arrêter après cette photo**
l'interrompt, et le passage suivant reprend là où il s'était arrêté (chaque réponse est gardée
aussitôt dans le cache). Rouvrir la page pendant un passage le montre. Seul le cache est écrit :
vos photos ne sont pas modifiées. Si Ollama est injoignable, la page le dit en une ligne.

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
| 🤖 `--sample N` | **Avec une IA locale seulement.** Décrire N photos prises au hasard avec le modèle, afficher leurs mots, le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. |
| 🤖 `--no-describe` | **Avec une IA locale seulement.** Ne rien demander de nouveau au modèle : les mots des dossiers, noms, dates et lieux, et les descriptions déjà dans le cache. |
| 🤖 `--yes`, `-y` | **Avec une IA locale seulement.** Décrire les photos sans demander, quel que soit leur nombre (au-delà de 200, il demande d'abord). |
| 🤖 `--meaning` | Un modèle sur le processeur de cet ordinateur (CLIP : ni Ollama, ni carte graphique, rien n'est envoyé) regarde chaque photo une fois, environ 1 minute pour 1 000 photos, pour que [`search`](search.md) trouve ce qu'une photo montre ([recherche par le sens](../reference-tags.md#retrouver-une-photo-par-ce-quelle-montre----meaning)). Le modèle (894 Mo) est téléchargé dans le cache la première fois. Par défaut : `[tags] meaning`. |

## Bon à savoir

- **Cherchable pendant le passage** : chaque photo décrite écrit ses mots aussitôt, avec ceux de
  ses copies identiques, de sa rafale et de son groupe de quasi-doublons. Une recherche ouverte
  pendant un passage de plusieurs heures les trouve (en une vingtaine de secondes) ; un passage
  arrêté, ou une fenêtre fermée, ne perd aucun mot déjà écrit.
- **Le modèle de vision** est celui de `[classify.ai]` (`model`, `url`) : chaque photo y est
  envoyée, en JPEG de 768 pixels, et seulement là. Gardez ce serveur sur votre propre ordinateur.
  Sans `model`, rien n'est jamais envoyé.
- **Une photo par ensemble** : les copies identiques partagent leurs mots, une rafale prend ceux de
  sa photo la plus nette ; une vidéo est vue par l'image du milieu ; les petites images et
  vidéos ne sont pas envoyées. `classify` réutilise ensuite ces réponses au lieu de renvoyer les
  photos.
- **Recherche par le sens** (`--meaning`, à activer) : ce qu'une photo montre, jamais qui ni où
  (les noms viennent de `people`, les lieux du GPS) ; les copies identiques sont regardées une
  fois, les vidéos jamais.
- **Arrêtez quand vous voulez** : Ctrl+C laisse finir les photos en cours de description ; la
  fois suivante reprend où celle-ci s'est arrêtée.
- **Pourquoi pas dans les photos ?** Écrire dans un JPEG change ses octets, son empreinte, et deux
  copies identiques cesseraient de l'être. [`xmp`](xmp.md) écrit des fichiers compagnons à la place.

## Pour aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
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
 mots pour la retrouver, gardés dans le cache, jamais dans les photos : ses
 dossiers, son nom, sa date, son lieu, et ce qu'elle montre avec une IA locale
 facultative 🤖

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path             <str>  Seulement les photos sous ce dossier (chemin de    │
│                           l'hôte, tel que vous l'avez monté) ; à répéter     │
│                           pour plusieurs. Par défaut : tous les fichiers de  │
│                           l'index.                                           │
│ --meaning                 Laisser aussi un modèle regarder chaque photo sur  │
│                           le processeur de cet ordinateur (CLIP, une seule   │
│                           fois, environ 1 minute pour 1 000 photos), pour    │
│                           que 'search' trouve ce qu'une photo montre. Par    │
│                           défaut :  meaning.                                 │
│ --help     -h             Affiche ce message et quitte.                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🤖 IA locale (Ollama), facultative : un modèle indiqué dans config.toml ────╮
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
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
