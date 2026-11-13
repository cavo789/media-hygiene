# `spots` : où vos photos ont été prises, gardé dans l'index

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `spots` · 🇬🇧 [English](../../en/commands/spots.md)

## En bref

**Un monument ou une ville dont vous vous souvenez retrouve la photo.**

Pour chaque photo avec une position GPS, l'index garde le lieu remarquable où elle a été prise
(à moins de 200 m), sa ville, ses deux niveaux de région et son pays. [`library`](library.md) la
trouve alors par chacun d'eux (« Montagne de Bueren », « Colmar », « Haut-Rhin »), affiche
`📍 Liège` (la ville) sous la date, le lieu remarquable étant une pastille `📍 Montagne de Bueren` cliquable parmi les mots, et le [diaporama](slideshow.md) le lit au lieu de le
recalculer à chaque séance.

**Chaque `audit` le fait pour vous**, nouvelles photos comprises. Lancez `spots` une fois après
une mise à jour si vous ne voulez pas attendre le prochain audit ; il est aussi sur la page
d'accueil, sous *Retrouver*. *Donner des mots à vos photos*, sur la même page, le fait d'abord,
avec sa ligne de progression.

## En un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Ni lues, ni modifiées : seulement les positions que l'index connaît déjà (`--vision` 🤖 les lit, sans jamais les modifier). |
| Il faut | `/cache` (l'index) : lancez [`audit`](audit.md) une fois avant. |
| Écrit | Dans l'index seulement. |
| Envoie | Rien. Les villes et les lieux viennent de la copie de GeoNames dans l'image. Avec `--vision` 🤖, les photos ne vont qu'à votre modèle local. |

## Lancer

Dans Windows PowerShell :

```powershell
mh spots
```

Une deuxième fois n'écrit rien et ne prend qu'un instant : une position est nommée une seule fois.
Arrêté en route, il reprend où il s'était arrêté.

## Ce qui est affiché

- Votre [lieu](places.md) d'abord, sinon la ville : `Maison`, `Liège`. Un lieu dessiné s'applique
  aussitôt.
- Le lieu remarquable passe devant : le nom accepté d'OpenStreetMap après un
  [`import`](import.md) (jamais envoyé sans votre Oui), sinon celui de GeoNames.
- Les régions (`Grand Est`, `Haut-Rhin`) se cherchent et ne s'affichent pas. Un dossier « Alsace »
  vient de votre propre lieu : GeoNames ne connaît que les régions d'aujourd'hui.
- À plus de `[tags] town_km` (20 km) de toute ville, aucune ville n'est nommée.

Une photo déplacée par [`sort`](sort.md) ou [`undo`](undo.md) garde sa ligne. Un dossier renommé
dans l'Explorateur est nommé à nouveau au prochain audit.

## 🤖 Le bâtiment que montre la photo : `--vision`

Le GPS seul nomme le monument le plus proche à moins de 200 m : une cathédrale photographiée
depuis l'autre côté de la place n'a rien, une photo prise à côté d'un château, dos à lui, a le
château. Avec votre propre modèle de vision local (Ollama, réglé dans `[classify.ai] model`,
comme pour [`tags`](tags.md)) :

```powershell
mh spots --vision   # 🤖 demande un modèle d'IA local
```

Le modèle voit chaque photo localisée et choisit, parmi les monuments à moins de 1 km (les 10
plus proches), celui qu'elle montre, ou aucun. Une courte liste où choisir, jamais une
devinette libre : une réponse hors de la liste laisse la photo telle quelle. Chaque choix est
gardé aussitôt dans l'index, cherchable, et demandé une seule fois. Un nom saisi à la main
l'emporte toujours : une telle photo n'est jamais envoyée. Sans modèle, ou si le serveur ne
répond pas, rien ne change. Les photos ne vont qu'à votre modèle local.

Sur la page d'accueil, *Retrouver*, à côté de cette étape : **🤖 Laisser l'IA locale nommer le
monument**. Elle montre d'abord une partie des photos sur lesquelles elle interrogera le modèle
(60 au plus, réparties sur la liste ; survolez-en une pour son chemin et ses monuments), la carte de
l'IA locale pour choisir le modèle, et le nombre sur le bouton. La progression se suit ensuite dans
la page ; *Arrêter après cette photo* garde chaque choix déjà fait, et le passage suivant continue.
Les vidéos et les fichiers mis de côté ne sont pas soumis.

## 📍 Taper soi-même le monument : touche L

GeoNames nomme un monument à moins de 200 m pour une photo localisée sur dix seulement (mesuré
sur une vraie collection de 281 photos localisées). Dans la grande vue de
[`library`](library.md), appuyez sur **L** : *📍 Le monument que montre cette photo* propose les
monuments à moins de 500 m, du plus proche au plus lointain avec leur distance, et le nom
OpenStreetMap s'il a été demandé ; choisissez-en un ou tapez le nom, puis *Écrire ce nom*.
*Mauvais nom* dit que le nom actuel est faux : il est retiré et plus jamais proposé pour cette
photo.

Le nom va dans le fichier compagnon `.xmp` de la photo (`Iptc4xmpExt:LocationShown`, lu par
digiKam et Lightroom), jamais dans la photo ; journalisé : `mh undo` le reprend, et les vignettes suivent aussitôt (le nom précédent, ou la ville). La ligne sous la
photo est le compagnon relu sur le disque. Le compagnon suit la photo (`sort`, `undo`, un dossier
renommé dans l'Explorateur) : le nom et les noms refusés la suivent ; un index reconstruit les
relit au prochain audit. Un nom posé par une autre application est gardé.

Une fois le nom écrit, la fenêtre demande *Un de vos lieux ?* : **L'ajouter comme lieu** écrit un
cercle de 200 m autour de la photo dans `[[classify.places]]` de `config.toml` (la ligne affichée
est le fichier relu ; un lieu du même nom déjà présent est gardé), *Non, le nom seulement* ne
touche pas aux lieux. Rien n'est ajouté sans ce clic.

Le monument est aussi une **pastille 📍**, la première parmi les mots de la vignette et de la
grande vue : un clic montre toutes les photos de ce monument (Ctrl+clic l'ajoute à la recherche).

## L'aide intégrée

<details>
<summary><code>spots --help</code></summary>

<!-- capture: help-spots.txt -->
```text
 Utilisation : media-hygiene spots [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Nomme où les photos déjà dans
 l'index ont été prises (lieu remarquable, ville, régions), hors ligne ;
 l'audit le fait pour les nouvelles.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h      <bool>  Affiche ce message et quitte.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🤖 IA locale (Ollama), facultative : un modèle indiqué dans config.toml ────╮
│ --vision        <bool>  🤖 Puis laisser le modèle de vision local de         │
│                         [classify.ai] choisir, parmi les monuments à moins   │
│                         de 1 km, celui que montre chaque photo (les photos   │
│                         ne sont envoyées qu'à ce modèle ; un nom saisi à la  │
│                         main l'emporte toujours).                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
