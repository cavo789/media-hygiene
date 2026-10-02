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
navigateur : elles montrent les zones que vous regardez, jamais une photo.

## Nommer vos lieux sur une carte

`places` montre où vos photos ont été prises, à partir du cache des audits, et vous laisse
nommer les lieux qui comptent pour vous. Il lui faut le cache (`/cache`, où les audits ont
noté les positions) et le dossier de `config.toml` (`/config`, où les lieux sont enregistrés) :

```powershell
docker run --rm -it --name media-hygiene-places -p 127.0.0.1::8080 `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr places
```

Comme pour [`review`](../clean/10-review-bursts.md#étape-2--ouvrir-la-page), demandez
l'adresse à Docker dans une autre fenêtre, `docker port media-hygiene-places 8080`, et
ouvrez-la dans votre navigateur.

- **Les cercles** sont vos photos avec une position GPS, groupées par environ 200 mètres, plus
  grands là où il y en a plus. La liste de gauche donne d'abord **les plus grands groupes sans
  nom** : la maison est souvent le premier.
- **Cliquez sur un cercle, ou n'importe où sur la carte**, pour nommer un lieu. Donnez-lui un
  nom, réglez son **rayon** avec le curseur (une maison : 100 à 200 mètres ; un village :
  quelques kilomètres), et faites glisser son repère pour le déplacer. Cochez **Maison** pour
  votre maison : les voyages se mesurent à partir d'elle.
- **Chercher une ville** cherche parmi les villes livrées avec l'image, hors ligne, et y zoome.
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

- **`place`** : une photo dont la position est dans le rayon d'un de vos lieux va dans le nom
  du lieu : `2023/Maison`. Sa catégorie est `{place}`, sauf si vous en écrivez une autre, comme
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
  nom anglais, comme `Munich`).

| `[classify]` | Défaut | Sens |
|---|---|---|
| `trip_min_km` | 100 | Plus loin de la maison que cela, un événement est un voyage. |
| `trip_merge_gap_hours` | 48 | Des événements d'un voyage à moins de cet écart ne font qu'un voyage. |
| `trip_merge_max_km` | 120 | …et à moins de cette distance l'un de l'autre. |

Une règle `trip` a besoin d'un lieu avec `home = true` : sans lui, le fichier est refusé à la
lecture, avec le nom de la règle.

Les modèles et les catégories peuvent aussi utiliser `{place}` (le lieu personnel du fichier)
et `{country}`, `{region}`, `{city}` (ceux de son voyage) ; ils sont vides pour les autres
fichiers, et un niveau de dossier vide est omis.

## Une autre carte

Les tuiles de la carte viennent d'OpenStreetMap par défaut. Un autre serveur de tuiles se règle
dans `[places]` ; la page n'autorise que ce serveur :

```toml
[places]
tiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
attribution = "© OpenStreetMap contributors"
```

## Crédits

Villes, régions et pays : [GeoNames](https://www.geonames.org/), sous licence
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). Noms des pays
en anglais et en français : [Unicode CLDR](https://cldr.unicode.org/). La carte :
[Leaflet](https://leafletjs.com/) (licence BSD 2-Clause), livrée avec l'image, et les tuiles du
serveur que vous configurez.

---

← [8. Nommer les sujets avec un modèle local](08-subjects-from-a-local-model.md) · [Documentation](../README.md)
