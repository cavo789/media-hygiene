# 9. Lieux et voyages grâce au GPS

[Documentation](../README.md) › Trier, étape 9 · 🇬🇧 [English](../../en/sort/09-places-from-gps.md)

Les téléphones récents écrivent **où** chaque photo a été prise. Avec cela, une photo peut dire
« Maison », « Chez papy » ou « Italie/Turin » sans rien deviner. Les anciens téléphones et la
plupart des appareils photo n'écrivaient rien : le [premier audit](../start/01-first-audit.md)
dit combien de vos photos ont une position GPS (*Photos et vidéos avec une position GPS*). Cette
étape est **facultative** : sans positions, tout le reste fonctionne de la même façon.

## Ce qui quitte votre ordinateur

**Rien.** Villes et pays sont nommés à partir des données [GeoNames](https://www.geonames.org/)
livrées avec l'image : environ 160 000 villes de plus de 1 000 habitants, lues sur votre
ordinateur. Aucune position, aucune photo, aucune liste de lieux n'est jamais envoyée nulle
part. Seule la carte de `places` (plus bas) charge des **tuiles de carte** dans votre
navigateur : elles montrent les zones que vous regardez, jamais une photo. Et seulement quand
vous cliquez sur **Chercher sur OpenStreetMap** sur cette carte, le **texte saisi** dans sa
zone de recherche est envoyé à OpenStreetMap ([plus bas](#un-village-ou-un-parc-comme-zone)) ;
`classify` ne va jamais sur Internet.

## Nommer vos lieux sur une carte

`places` montre où vos photos ont été prises, à partir du cache des audits, et vous laisse
nommer les lieux qui comptent pour vous. Il lui faut le cache (`/cache`, où les audits ont
noté les positions) et le dossier de `config.toml` (`/config`, où les lieux sont enregistrés) ;
vos dossiers de photos, en lecture seule, montrent les photos d'un groupe. `mh` monte le tout,
et ouvre le port de la page :

```powershell
mh places
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr places
```

</details>

Comme pour [`review`](../clean/10-review-bursts.md#étape-2--ouvrir-la-page), Ctrl+clic sur
l'adresse affichée, `http://127.0.0.1:8088/`.

![La carte des lieux : les tuiles OpenStreetMap du parc du Cinquantenaire à Bruxelles, le cercle des photos prises là, le cercle vert du lieu Parc du Cinquantenaire qui vient d'être enregistré, et à gauche la liste des lieux et des plus grands groupes sans nom](../images/places.webp)

- **Les cercles** sont vos photos avec une position GPS, groupées par environ 200 mètres, plus
  grands là où il y en a plus. La liste de gauche donne d'abord **les plus grands groupes sans
  nom** : la maison est souvent le premier. Cliquez sur **le nombre de photos** d'une de ses
  lignes (par exemple « 11 photos ») pour voir les photos de ce groupe, 24 au plus, et
  reconnaître le lieu avant de le nommer.
- **Repliez une liste** en cliquant sur son titre (*Vos lieux (10)*) : les groupes restent à
  portée.
- **Cliquez sur un cercle, ou n'importe où sur la carte**, pour nommer un lieu. Donnez-lui un
  nom, réglez son **rayon** avec le curseur (une maison : 100 à 200 mètres ; un village :
  quelques kilomètres), et faites glisser son repère pour le déplacer. Cochez **Maison** pour
  votre maison : les voyages se mesurent à partir d'elle.
- **Chercher une ville** cherche parmi les villes livrées avec l'image, hors ligne, et y zoome.
- **Chercher sur OpenStreetMap** (ou Entrée dans la même zone) trouve un village, un quartier ou
  un parc avec son contour : voir [plus bas](#un-village-ou-un-parc-comme-zone).
- **Enregistrer** écrit le lieu dans `config.toml` aussitôt, en gardant vos commentaires et le
  reste du fichier. Cliquez sur un lieu pour le déplacer, le renommer ou le supprimer.

Ctrl+C dans le terminal arrête la carte. Un nom de lieu devient un nom de dossier : deux lieux
ne peuvent pas le partager, et les caractères que Windows refuse sont refusés.

Vous pouvez aussi écrire les lieux à la main, la latitude et la longitude copiées de n'importe
quelle carte :

```toml
[[classify.places]]
name = "Maison"
latitude = 50.0
longitude = 5.0
radius_m = 200
home = true

[[classify.places]]
name = "Chez papy"
latitude = 50.1
longitude = 5.2
radius_m = 150
```

## Un village ou un parc comme zone

Un village n'est pas un cercle, et les petits ne sont pas parmi les villes livrées avec
l'image. Saisissez son nom dans la zone de recherche et cliquez sur **Chercher sur
OpenStreetMap** (ou appuyez sur Entrée) : la carte liste les zones
qu'[OpenStreetMap](https://www.openstreetmap.org/) connaît sous ce nom, avec leur nom complet
(village, commune, province, pays). Cliquez sur l'une d'elles : son contour est dessiné,
l'éditeur s'ouvre avec son nom, que vous pouvez changer, et **Enregistrer** l'écrit comme
n'importe quel autre lieu. Une photo lui appartient alors quand elle a été prise **à
l'intérieur du contour**, pas simplement près de lui ; un cercle dans la zone (la maison dans
son village) l'emporte sur la zone.

- **Ce qui quitte votre ordinateur** : le texte saisi, et rien d'autre, envoyé par
  `media-hygiene` lui-même (pas votre navigateur) au service de recherche, sur votre clic
  seulement. Jamais une photo, jamais une position, jamais votre liste de lieux.
- **Une fois enregistré, le contour vit dans `config.toml`**, avec l'identifiant OpenStreetMap
  de la zone : `classify` n'interroge jamais le service, fonctionne hors ligne et donne le même
  résultat demain.
- **Limites** : le service public d'OpenStreetMap, [Nominatim](https://nominatim.org/), a des
  [conditions d'utilisation](https://operations.osmfoundation.org/policies/nominatim/) : une
  recherche par seconde au plus (l'outil attend si vous allez plus vite), aucune recherche
  pendant la frappe, chaque texte demandé une seule fois par session. Une zone de plus de
  1 000 points (une région, un pays) n'est pas listée : une règle `trip` nomme mieux les pays.
  Une zone à cheval sur le 180e méridien n'est pas prise en charge.
- **Pour la désactiver**, ou utiliser un autre service (votre propre Nominatim, par exemple) :
  `nominatim_url` dans `[places]` ([plus bas](#une-autre-carte)) ; vide, le bouton disparaît et
  la recherche reste hors ligne.
- Sans Internet, la page le dit ; la recherche de villes hors ligne fonctionne toujours.

Un lieu enregistré à partir d'une zone ressemble à ceci (un village fictif, contour raccourci) :

```toml
[[classify.places]]
name = "Fictiville"
latitude = 50.315
longitude = 5.12
osm = "R9000001"
area = [
    [[[50.3, 5.1], [50.3, 5.14], [50.33, 5.14], [50.33, 5.1]]],
]
```

`area` contient une ligne par partie de la zone ; chaque partie est une liste d'anneaux de
points `[latitude, longitude]`, le contour d'abord, puis ses trous (un lac dans le village).
`latitude` et `longitude` sont son milieu, montré sur la carte ; un lieu avec une zone n'a pas
de `radius_m`.

## Écrire les règles

Les lieux ne font rien seuls : deux règles s'en servent, dans `[[classify.rules]]`
([étape 6](06-write-down-what-you-know.md)) :

```toml
[[classify.rules]]
name = "Mes lieux"
match = "place"

[[classify.rules]]
name = "Voyages"
match = "trip"
```

- **`place`** : une photo dont la position est dans le rayon d'un de vos lieux, ou dans sa
  zone, va dans le nom du lieu : `2023/Maison`. Sa catégorie est `{place}`, sauf si vous en écrivez une autre, comme
  `category = "Famille/{place}"`.
- **`trip`** : les photos d'un événement **à plus de `trip_min_km`** (100 km) de la maison
  sont un voyage. Sa catégorie est `{country}/{city}`, sauf si vous en écrivez une autre, comme
  `category = "Vacances et sorties/{country} {year}"` : `2023/Italie/Turin`.

Comme une règle de dates, une règle GPS suit les **événements**
([étape 4](04-classify.md#lire-le-résultat)) :

- une photo **sans** position, dans un événement dont les photos situées sont à un de vos
  lieux, y va aussi ; dans un voyage, elle suit le voyage. Sa raison est alors
  `place-neighbour` ou `trip-neighbour`, avec un score plus bas (70) : « à vérifier » par
  défaut, jamais une certitude ;
- les jours d'un voyage sont réunis **par la distance, pas par la ville** : des événements à
  moins de `trip_merge_gap_hours` (48 heures) d'écart et à moins de `trip_merge_max_km`
  (120 km) l'un de l'autre font un seul voyage ; un tour des villages reste donc un seul
  voyage. Un jour sans positions entre deux jours d'un voyage le rejoint ; un jour à la maison
  le termine ;
- un voyage est nommé d'après la **plus grande ville** à moins de 10 km de son jour principal :
  un hôtel dans une banlieue de Turin donne `Turin`. Les noms de pays sont écrits dans la langue
  de l'interface (`Italie` en français) ; les noms de villes sont ceux de GeoNames (souvent leur
  nom anglais, comme `Munich`, parfois le leur, comme `Brugge`) :
  [vos noms pour les villes](#vos-noms-pour-les-villes) les changent.

| `[classify]` | Défaut | Sens |
|---|---|---|
| `trip_min_km` | 100 | Plus loin de la maison que cela, un événement est un voyage. |
| `trip_merge_gap_hours` | 48 | Des événements d'un voyage à moins de cet écart ne font qu'un voyage. |
| `trip_merge_max_km` | 120 | …et à moins de cette distance l'un de l'autre. |
| `folder_town_min_population` | 5000 | La plus petite ville dont un dossier peut porter le nom. |
| `folder_town_ignore` | `[]` | Les noms de dossiers qui ne sont jamais des villes. |

Une règle `trip` a besoin d'un lieu avec `home = true` : sans lui, le fichier est refusé à la
lecture, avec le nom de la règle.

Les modèles et les catégories peuvent aussi utiliser `{place}` (le lieu personnel du fichier)
et `{country}`, `{region}`, `{city}` (ceux de son voyage) ; ils sont vides pour les autres
fichiers, et un niveau de dossier vide est omis.

## Les villes nommées par vos dossiers

La plupart des photos n'ont pas de position, mais leurs dossiers disent souvent où elles ont été
prises : `2017\Durbuy`, `Vacances\Spa`. Une troisième règle les lit :

```toml
[[classify.rules]]
name = "Villes des dossiers"
match = "folder_town"
```

- Un dossier n'est reconnu que si son **nom entier** est celui d'une ville (sans tenir compte
  des majuscules ni des accents) : `Durbuy` l'est, `Durbuy 2017` et `Week-end à Durbuy` non. Le
  dossier le plus proche au-dessus d'une photo compte.
- Seules les villes d'au moins `folder_town_min_population` habitants (5 000) comptent : un
  village de 3 000 habitants n'est pas cherché. Les noms de mois et de saisons ne sont jamais des
  villes (`Mai` est le mois, pas Mai au Kenya).
- Entre des villes de même nom, celles des pays de vos photos situées et de la maison passent
  d'abord, puis la plus grande : `Bruges` est la belge quand vous habitez en Belgique.
- Quand les photos situées du dossier sont à plus de `trip_merge_max_km` (120 km) de la ville,
  le dossier n'est pas nommé d'après elle : un dossier `Nice` de photos prises en Ardenne reste
  à l'écart.
- Ses photos vont dans `{country}/{city}` (`2017/Belgique/Durbuy`), sauf si vous écrivez une
  autre `category`. Son score est bas (60) : les propositions sont **à vérifier**, et toute autre
  règle passe avant.

Un nom de dossier est un indice faible : un prénom (`Martin`, `Victoria`) est aussi une ville
quelque part. Relisez les dossiers « À vérifier » avant de trier, et listez les noms qui ne sont
jamais des villes dans `[classify] folder_town_ignore = ["Martin", "Victoria"]` (sans tenir compte
des majuscules ni des accents) ; ou donnez `score = 0` à la règle pour l'éteindre.

## Vos noms pour les villes

GeoNames nomme une ville en anglais (`Brussels`, `Antwerp`) ou dans sa propre langue (`Brugge`,
`Gent`). Pour lire vos noms dans les catégories, écrivez-les dans `config.toml`, le nom GeoNames
exact d'abord :

```toml
[classify.town_names]
"Brussels" = "Bruxelles"
"Brugge" = "Bruges"
"Gent" = "Gand"
```

Les voyages, `{city}`, la recherche de ville de la page `places` et la règle `folder_town`
utilisent vos noms ; un dossier nommé de l'une ou l'autre façon est reconnu (`Brugge` ou
`Bruges`). Un nom qui n'est pas une ville de GeoNames ne fait rien.

## Une autre carte

Les tuiles de la carte viennent d'OpenStreetMap par défaut. Un autre serveur de tuiles se règle
dans `[places]` ; la page n'autorise que ce serveur. `nominatim_url` est le service de
recherche de [**Chercher sur OpenStreetMap**](#un-village-ou-un-parc-comme-zone) : une autre
instance, ou vide pour désactiver la recherche en ligne :

```toml
[places]
tiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
attribution = "© OpenStreetMap contributors"
nominatim_url = "https://nominatim.openstreetmap.org"
```

## Crédits

Villes, régions et pays : [GeoNames](https://www.geonames.org/), sous licence
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). Noms des pays
en anglais et en français : [Unicode CLDR](https://cldr.unicode.org/). La carte :
[Leaflet](https://leafletjs.com/) (licence BSD 2-Clause), livrée avec l'image, et les tuiles du
serveur que vous configurez. Les zones trouvées en ligne : © [contributeurs
d'OpenStreetMap](https://www.openstreetmap.org/copyright), sous licence
[Open Database License](https://opendatacommons.org/licenses/odbl/) (ODbL), cherchées avec
[Nominatim](https://nominatim.org/).

---

← [8. Nommer les sujets avec un modèle local](08-subjects-from-a-local-model.md) · [Documentation](../README.md) · Suite : **[10. Trier par personne](10-sort-by-person.md)** →
