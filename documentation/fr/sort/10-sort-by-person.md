# 10. Trier par personne

[Documentation](../README.md) › Trier, étape 10 · 🇬🇧 [English](../../en/sort/10-sort-by-person.md)

Les dates, les dossiers et les lieux ([étapes 6 à 9](06-write-down-what-you-know.md)) disent
**quand** et **où**. Cette étape ajoute **qui** : les événements où figure Chloé vont dans
`2023/Personnes/Chloé`, ou dans le dossier de votre choix. Vous nommez chaque personne une fois,
sur une page de votre navigateur ; une règle de `classify` fait le reste. Cette étape est
**facultative** : sans elle, tout le reste fonctionne de la même façon.

Elle ajoute une seule chose aux commandes des étapes précédentes : `people`, pour trouver et
nommer les visages. `classify`, le classeur, `review-sort` et `sort` restent les mêmes.

## Ce qui quitte votre ordinateur

**Rien.** Les visages sont trouvés et comparés sur votre ordinateur ; ils restent dans le cache
(`/cache`), jamais dans vos photos, jamais dans les rapports. Les noms vont dans votre
`config.toml`, en texte. Le seul téléchargement est celui des deux modèles de visages (39 Mo),
une fois, depuis OpenCV Zoo : il n'envoie rien de vos photos. `people --forget` supprime tous les
visages ([plus bas](#oublier-les-visages)).

## 1. Mesurer d'abord

Trouver les visages prend du temps : environ un cinquième de seconde par photo, mesuré sur un
ordinateur personnel, donc des heures pour une grande collection la première fois. Chaque photo
n'est analysée **qu'une fois** : les exécutions suivantes n'analysent que les nouvelles. Mesurez
sur 200 photos prises au hasard avant la longue exécution :

```powershell
mh people --sample 200
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr people --sample 200
```

</details>

Sur la bibliothèque de démonstration de ce guide, 10 photos mesurées :

<!-- capture: people-sample.txt|re:^✅|. -->
```text
✅ 10 photos analysées : 3 visages, 0,05 s par photo.
```

Elle se termine par l'estimation de l'exécution complète (`Une exécution complète analyserait
encore 20 000 photos : environ 1 h 10 min.`) ; les visages trouvés sont gardés. Plutôt après
votre prochain audit ? `audit --people` fait l'audit, dit combien de temps prendront les visages,
et **demande** avant de les chercher
([Les personnes](../reference-people.md#pendant-laudit--audit---people)). Ctrl+C arrête entre
deux photos et garde ce qui est fait : l'exécution suivante continue.

## 2. Trouver les visages et les nommer

`people` a besoin du cache (où les audits ont listé vos photos), du dossier de `config.toml`
(`/config`, où les noms sont enregistrés) et du port de sa page, tous trois donnés par `mh` :

```powershell
mh people
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr people
```

</details>

Avec WSL ou Linux :

```bash
mh people
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```bash
docker run --rm -it -p 127.0.0.1:8088:8088 \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v media-hygiene-cache:/cache \
  -v "$HOME/media-hygiene/config:/config" \
  cavo789/media-hygiene --locale fr people
```

</details>

Elle analyse les photos pas encore vues, regroupe les visages qui se ressemblent
(sans doute une personne par groupe) et affiche l'adresse de la page, `http://127.0.0.1:8088/` :
Ctrl+clic dessus.

<!-- capture: people.txt|re:^✅| -->
```text
✅ 33 photos analysées : 14 visages, 0,05 s par photo.
✅ 17 visages dans 43 photos : 3 groupes de visages semblables, les plus grands
7, 5, 4 ; 1 vus une seule fois.
✅ Visages prêts, ouvrez http://127.0.0.1:8088/ dans votre navigateur pour les
nommer ; chaque nom est enregistré aussitôt dans config.toml. Ctrl+C l'arrête ;
les photos ne sont pas modifiées.
💡 La page ne s'ouvre pas ? docker run doit publier le même port des deux côtés,
avec -p 127.0.0.1:8088:8088.

✅ Page arrêtée ; rien n'a été modifié.
```

![La page des personnes : le plus grand groupe nommé Chloé, le nom relu dans config.toml en haut de la page, ses sept visages en dessous ; puis le groupe 2 et le groupe 3, pas encore nommés, chacun avec son champ pour taper un nom et ses boutons pour nommer, nommer avec d'autres ou ignorer le groupe](../images/people.webp)

Sur la page, les plus grands groupes viennent d'abord. **Tapez un nom** sur un groupe et appuyez
sur Entrée ; le nom est écrit dans `config.toml`, puis relu dans le fichier et affiché en haut de
la page (« Enregistré dans config.toml, relu : Chloé, 58 visages confirmés. »). Le clavier
suffit :

- la même personne coupée en deux groupes (un enfant à 3 ans et à 12 ans) : choisissez les deux
  avec `x` et nommez-les d'un coup, ou donnez au second le même nom ;
- un visage qui n'est pas le bon dans un groupe : × dessus, ce nom ne lui est plus jamais donné ;
- des inconnus, des affiches, des statues : `i` ignore le groupe ;
- « Chloé ? » est une suggestion : `y` la confirme. Une suggestion ne compte jamais tant que vous
  ne l'avez pas confirmée.

Nommer les dix plus grands groupes suffit souvent : les autres visages prennent le nom du visage
confirmé le plus proche quand ils lui ressemblent assez. Ctrl+C dans le terminal arrête la page.
Le `people` suivant affiche qui est nommé, et sur combien de photos :

```text
✅ Nommés : Chloé : 412 photos, Manon : 236 photos.
```

Le détail de la page et de ses réglages : [Les personnes](../reference-people.md#nommer-les-groupes).

## 3. Écrire la règle

Dans `config.toml`, ajoutez une règle `person` ([étape 6](06-write-down-what-you-know.md#les-personnes)),
une par personne à ranger :

```toml
[[classify.rules]]
name = "Avec Chloé"
match = "person"
names = ["Chloé"]
category = "Personnes/Chloé"
```

- Un **événement** (des photos prises à peu de temps d'intervalle,
  [étape 4](04-classify.md#lire-le-résultat)) va à la règle quand au moins 10 % de ses fichiers
  la montrent : c'est peut-être elle qui prend les photos. `min_share = 30` ne garde que les
  événements où on la voit souvent. Une photo hors de tout événement y va quand elle la montre.
- `names = ["Chloé", "Manon"]` : les événements avec l'une ou l'autre ; ajoutez `all = true`
  pour ceux avec les deux.
- Les noms sont ceux de la page ; la casse et les accents ne comptent pas (`chloe` vaut
  `Chloé`).
- **Placez-la sous les règles dont vous êtes plus sûr** (vos dossiers, les dates, les lieux) :
  les règles sont lues dans l'ordre, la première sûre décide. Quelqu'un présent sur la plupart de
  vos événements, placé au-dessus, prendrait presque toute la collection, comme une catégorie
  « Famille ».

## 4. Proposer, regarder, trier

Ensuite, les mêmes commandes qu'aux étapes [4](04-classify.md), [5](05-review-the-proposal.md)
et [7](07-sort.md) : `mh classify`, le classeur (ou
[`mh review-sort`](11-name-events-in-the-browser.md)), puis `mh sort`. Dans la bibliothèque de démonstration de ce guide, chaque photo est déjà dans
un dossier : la règle y est placée juste au-dessus de *Dossiers existants*, sinon cette règle-là
les déciderait toutes :

<!-- capture: classify-person.txt|re:^Pourquoi$|<blank> -->
```text
Pourquoi
┌────────────────────┬────┐
│ Avec Chloé         │ 25 │
│ Dossiers existants │ 18 │
│ Sans date          │  1 │
└────────────────────┴────┘
```

Ce qu'il faut vérifier :

- le tableau *Pourquoi* de `classify` a une ligne **Avec Chloé**, avec le nombre de fichiers que
  la règle a décidés ; la colonne *Raison* du classeur la nomme pour chaque fichier, et
  `review-sort` l'affiche sous *Proposé* ;
- la règle figure après *Règles qui n'ont rien décidé* ? Ses événements ont été décidés par une
  règle placée au-dessus, ou personne de nommé n'est sur assez de leurs photos : remontez-la, ou
  baissez `min_share` ;
- un nom que personne ne porte arrête `classify` avant toute lecture, et dit qui est nommé :

```text
❌ Règle 'Avec Chloé' : personne ne s'appelle "Manon" dans [[people.person]]. Personnes nommées : Chloé.
💡 Nommez d'abord son groupe sur la page 'people', ou corrigez les noms de la règle dans config.toml.
```

La proposition reste une proposition : un événement donné à tort à Chloé se corrige dans le
classeur comme les autres ([étape 5](05-review-the-proposal.md)).

## Annuler

- **Un tri** : `mh undo`, comme à l'[étape 7](07-sort.md) : chaque fichier revient où il était.
- **Une règle** : supprimez-la de `config.toml` et relancez `classify` ; rien n'a bougé avant
  `sort`.
- **Un nom** : sur la page, × retire un visage d'une personne, et un groupe peut être renommé.
  Les noms sont du simple texte dans `config.toml` : vous pouvez aussi modifier ou supprimer une
  table `[[people.person]]` à la main.

## Oublier les visages

```powershell
mh people --forget
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr people --forget
```

</details>

Tous les visages sont supprimés du cache, qui est ensuite relu pour montrer qu'il n'en reste
aucun. Puis la commande demande si les noms de `config.toml` partent aussi, et relit le fichier
pour le montrer. Vos photos et vos dossiers triés ne sont pas touchés. Pourquoi les visages
méritent ce soin : [votre vie privée](../reference-people.md#votre-vie-privée).

---

← [9. Lieux et voyages grâce au GPS](09-places-from-gps.md) · [Documentation](../README.md) · Suite : **[11. Nommer les événements dans le navigateur](11-name-events-in-the-browser.md)** →
