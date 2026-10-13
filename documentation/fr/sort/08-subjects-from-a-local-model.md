# 8. Nommer les sujets avec un modèle local

[Documentation](../README.md) › Trier, étape 8 · 🇬🇧 [English](../../en/sort/08-subjects-from-a-local-model.md)

Les dossiers, les dates et vos règles ([étape 6](06-write-down-what-you-know.md)) trient une
bonne partie d'une collection familiale. Les photos restées dans des dossiers qui ne portent
qu'une date (`Juillet 2016`, `2019-04`, `DCIM`) n'ont toujours pas de sujet : une plage, un
spectacle d'école, un jeu à la maison. Un **modèle de vision qui tourne sur votre propre
ordinateur** peut les regarder et le dire. Cette étape est **facultative** : sans elle, tout le
reste fonctionne de la même façon.

## Ce qui quitte votre ordinateur

Les photos sont envoyées au serveur de modèle que vous configurez, et seulement là. Faites
tourner ce serveur sur votre propre ordinateur ([Ollama](https://ollama.com)), et aucune photo
ne le quitte. Rien n'est jamais envoyé tant que `config.toml` ne contient pas une règle
`subject` **et** un `model` : l'outil n'appelle jamais un modèle de lui-même.

## Installer un modèle de vision

1. Installez [Ollama](https://ollama.com) sur votre ordinateur.
2. Téléchargez un modèle qui **voit les images**, par exemple `ollama pull qwen2.5vl:7b`. Un
   modèle plus grand décrit mieux, et plus lentement. Un modèle sans la capacité *vision* est
   refusé, avec son nom.
3. Laissez le conteneur l'atteindre :
   - **Docker Desktop** (Windows, macOS) : rien à faire, `host.docker.internal` est
     l'ordinateur.
   - **Docker Engine** (Linux, WSL sans Docker Desktop) : ajoutez
     `--add-host=host.docker.internal:host-gateway` à `docker run`, et démarrez Ollama avec
     `OLLAMA_HOST=0.0.0.0` pour qu'il écoute au-delà de `127.0.0.1`.

Gardez `/cache` monté ([premiers pas, étape 2](../start/02-keep-the-cache.md)) : les
descriptions sont gardées dans son index, et une photo n'est jamais décrite deux fois.

## Écrire la règle

Dans `config.toml`, indiquez le modèle dans `[classify.ai]`, puis ajoutez une règle `subject`
avec les catégories parmi lesquelles le modèle peut choisir :

```toml
[classify.ai]
url = "http://host.docker.internal:11434"
model = "qwen2.5vl:7b"

[[classify.rules]]
name = "Dossiers existants"
match = "existing_folder"

# … vos règles de dates, de chemins et d'appareils …

[[classify.rules]]
name = "Sujet"
match = "subject"
categories = [
    "Vacances et sorties = voyages, journées dehors : plage, montagne, visites",
    "Fêtes = anniversaires, Noël, communions, mariages ; pas un déguisement seul",
    "École = classe, excursions, spectacles et fêtes de l'école",
    "Sport et loisirs = sports et loisirs, pratiqués ou regardés : matchs, natation",
    "À la maison = la vie de tous les jours : jeux, repas, enfants, canapé, jardin",
    "Animaux = un animal de compagnie ou un animal comme sujet principal",
    "Nature et paysages = paysages, plantes et ciel, sans personne au premier plan",
]
```

- Le modèle choisit **une** des `categories`, ou aucune : une photo qui n'entre dans aucune
  reste aux autres règles.
- Il ne parle que là où **les signaux plus forts se taisent** : un fichier déjà décidé par un
  dossier, une date, un chemin, un appareil ou un genre n'est jamais envoyé. Placez la règle
  bas dans la liste.
- Les occasions se disent mieux par les dates : le modèle voit un gâteau, pas un anniversaire.
  Écrivez les anniversaires et Noël en règles `calendar`
  ([étape 6](06-write-down-what-you-know.md#les-dates)).
- Les captures d'écran et les documents viennent de la règle `kind` : le modèle n'y est pas
  fiable.
- Évitez une catégorie « Famille » ou « Portraits » : le modèle y mettrait la plupart des
  photos.

### Définir chaque catégorie

Écrivez chaque catégorie sous la forme `"Nom = définition"`. Le **nom** est le dossier ; la
**définition** dit au modèle ce que vous entendez par là, et n'apparaît nulle part ailleurs. Un
nom seul fonctionne encore, mais le modèle ne juge alors que sur ses mots. Sur une vraie
collection, avec les noms seuls, 7 des 10 photos vérifiées étaient dans la mauvaise catégorie :

- cinq scènes à la maison (une enfant dans les bras de son père, un ours en peluche, un canapé,
  un jeu vidéo, la terrasse) sont allées dans « Maison et travaux », à cause du mot *maison* :
  rien à voir avec des travaux ;
- un repas de famille chez les grands-parents est allé dans « Vacances et sorties » : *sorties*
  attirait tous les repas ;
- deux enfants coiffées d'un bonnet de père Noël dans un jardin en septembre sont allées dans
  « Fêtes ».

Une définition dit ce qui entre, et ce qui n'entre pas (« pas un déguisement seul »). Le modèle
répond « aucune » plutôt que de forcer une catégorie : une telle photo reste aux autres règles.
Changer une définition ne redécrit rien : seul le choix des catégories, en texte seul, est
refait.

## Quelques photos par événement

Décrire une photo prend des secondes : environ 4 secondes sur une carte graphique avec un grand
modèle. À ce rythme, 10 000 photos prendraient 11 heures. Chaque **événement** (des photos
prises à peu de temps d'intervalle, [étape 4](04-classify.md#lire-le-résultat)) est donc
représenté par quelques **échantillons**, `samples_per_event` (3 par défaut) : les photos les
plus nettes, réparties sur sa durée. Les autres photos et les vidéos de l'événement les
suivent. Une photo isolée répond pour elle-même.

Vous avez déjà lancé [`tags`](../reference-tags.md#les-mots-dun-modèle-de-vision-local) avec le
même `model` ? Ses réponses sont réutilisées : un échantillon décrit par `tags` n'est pas
renvoyé, seuls sa phrase et ses mots sont rapprochés de vos catégories (quelques secondes, du
texte seulement).

La **confiance** vient des échantillons, jamais de ce que le modèle dit de lui-même :

| Échantillons | Proposition |
|---|---|
| Tous d'accord (3 sur 3) | Sûre : `année/catégorie` |
| Une majorité (2 sur 3), ou une seule photo | À vérifier : `année/À vérifier/catégorie` |
| La plupart n'entrent dans aucune catégorie | Pas de sujet : les autres règles décident |

`per_photo = true` sur la règle décrit **chaque** photo à la place, chacune avec sa propre
catégorie : bien plus long. Les photos plus petites que `min_edge` pixels (512 sur leur côté le
plus court) ne sont jamais envoyées : sur une vignette, le modèle invente des détails.

## Mesurer d'abord : `--sample`

Avant une longue exécution, décrivez quelques photos prises au hasard et lisez le coût :

```powershell
mh classify --sample 50
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr classify --sample 50
```

</details>

Avec Docker Engine, `mh` ne joint pas Ollama : utilisez la commande complète, avec
`--add-host=host.docker.internal:host-gateway` après `-it`.

```text
412 groupes de photos (événements ou photos seules) ne sont pris par aucune de vos règles :
le modèle en regardera 1 236 (jusqu'à 3 par événement, les autres suivent).
1 186 à décrire avec qwen2.5vl:7b (50 déjà dans le cache), environ 1 h 29 min.
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Photo                           ┃ Description                       ┃ Catégorie            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ C:\Photos\2019-04\IMG_0412.jpg  │ Des enfants chantent sur une      │ École                │
│                                 │ scène d'école.                    │                      │
│ …                               │ …                                 │ …                    │
└─────────────────────────────────┴───────────────────────────────────┴──────────────────────┘
Par photo : 3.6 s pour décrire, 0.4 s pour choisir la catégorie.
Une exécution complète décrirait encore 1 186 photos : environ 1 h 19 min.
💡 --sample ne propose rien : lancez classify sans lui.
```

Le tableau montre si les catégories conviennent à vos photos ; le temps décide quand lancer.
Les descriptions sont rédigées dans la langue de l'interface (`locale`) : changez-la, et les
photos sont décrites à nouveau dans la nouvelle langue. Celles de l'échantillon sont gardées :
l'exécution complète ne les décrit pas à nouveau.

Après l'exécution complète, une ligne par règle `subject` dit ce qu'elle a décidé :

```text
✅ 1 186 photos décrites ; gardées dans le cache.
Règle 'Sujet' : 3 904 fichiers rangés d'après ce qu'a vu le modèle ; 37 groupes sans sujet →
vos autres règles, sinon À trier.
```

Un groupe sans sujet est un groupe pour lequel le modèle n'a trouvé aucune catégorie, ou dont
les échantillons ne s'accordaient pas.

## La longue exécution, jamais une surprise

- Avant de décrire, `classify` affiche combien de photos il va envoyer et le temps estimé.
  Au-delà de `confirm_above` photos (200 par défaut), il **demande d'abord** ; `--yes` ne
  demande pas. Refusé, ou sans terminal, il n'utilise que le cache.
- **Ctrl+C** arrête entre deux photos : ce qui est décrit est gardé, et le `classify` suivant
  reprend là où celui-ci s'est arrêté.
- `--no-describe` ne demande **rien de nouveau** au modèle : la règle `subject` lit les
  descriptions déjà dans le cache. Changez les catégories ou les autres règles et relancez en
  quelques secondes ; les événements pas encore décrits restent aux autres règles.

Changer les `categories` ne décrit rien à nouveau : les descriptions n'en dépendent pas. Seule
la seconde étape, en texte seulement, tourne à nouveau : choisir une catégorie pour chaque
description, plusieurs à la fois.

## Tous les réglages

| `[classify.ai]` | Défaut | Sens |
|---|---|---|
| `url` | `http://host.docker.internal:11434` | Le serveur Ollama. |
| `model` | vide | Le modèle de vision. Vide : aucune photo n'est jamais envoyée. |
| `map_model` | vide | Un modèle de texte qui choisit les catégories ; vide : `model`. |
| `samples_per_event` | 3 | Photos qui décrivent chaque événement. |
| `min_edge` | 512 | Les photos plus petites (côté le plus court, en pixels) ne sont jamais envoyées. |
| `confirm_above` | 200 | Au-delà de ce nombre de photos à décrire, demander d'abord. |
| `concurrency` | 1 | Photos décrites à la fois : une convient à une carte graphique. |
| `image_edge` | 768 | Le plus grand côté de l'image envoyée, en pixels. |
| `timeout_seconds`, `retries` | 180, 2 | Patience envers un serveur lent ou occupé. |
| `batch_size` | 20 | Descriptions par appel de choix de catégorie. |
| `seconds_per_photo` | 4.5 | L'estimation tant que cet ordinateur n'a décrit aucune photo. |

Dans une variable d'environnement, la table est un seul objet JSON :
`-e MEDIA_HYGIENE_CLASSIFY__AI='{"model": "qwen2.5vl:7b"}'`.

---

← [7. Trier](07-sort.md) · [Documentation](../README.md) · Suite : **[9. Lieux et voyages grâce au GPS](09-places-from-gps.md)** →
