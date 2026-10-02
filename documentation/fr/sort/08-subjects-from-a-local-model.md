# 8. Nommer les sujets avec un modèle local

[Documentation](../README.md) › Trier, étape 8 · 🇬🇧 [English](../../en/sort/08-subjects-from-a-local-model.md)

Les dossiers, les dates et vos règles ([étape 6](06-write-down-what-you-know.md)) trient une
bonne partie d'une collection familiale. Les photos restées dans des dossiers qui ne portent
qu'une date (`Juillet 2016`, `2019-04`, `DCIM`) n'ont toujours pas de sujet : une plage, un
spectacle d'école, des travaux à la maison. Un **modèle de vision qui tourne sur votre propre
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
categories = ["Vacances et sorties", "École", "Sport et loisirs", "Maison et travaux",
              "Animaux", "Nature et paysages"]
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

## Quelques photos par événement

Décrire une photo prend des secondes : environ 4 secondes sur une carte graphique avec un grand
modèle. À ce rythme, 10 000 photos prendraient 11 heures. Chaque **événement** (des photos
prises à peu de temps d'intervalle, [étape 4](04-classify.md#lire-le-résultat)) est donc
représenté par quelques **échantillons**, `samples_per_event` (3 par défaut) : les photos les
plus nettes, réparties sur sa durée. Les autres photos et les vidéos de l'événement les
suivent. Une photo isolée répond pour elle-même.

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
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr classify --sample 50
```

Avec Docker Engine, ajoutez `--add-host=host.docker.internal:host-gateway` après `-it`.

```text
412 événements ou photos isolées n'ont pas de signal plus fort que leur sujet : 1 236 photos
répondent pour eux.
Dont 1 236 à décrire avec qwen2.5vl:7b, environ 1 h 32 min.
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Photo                           ┃ Description                       ┃ Catégorie            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ C:\Photos\2019-04\IMG_0412.jpg  │ Children singing on a school      │ École                │
│                                 │ stage.                            │                      │
│ …                               │ …                                 │ …                    │
└─────────────────────────────────┴───────────────────────────────────┴──────────────────────┘
Par photo : 3.6 s pour décrire, 0.4 s pour choisir la catégorie.
Une exécution complète décrirait encore 1 186 photos : environ 1 h 19 min.
💡 --sample ne propose rien : lancez classify sans lui.
```

Le tableau montre si les catégories conviennent à vos photos ; le temps décide quand lancer.
Les descriptions sont rédigées en anglais, quelle que soit la langue de l'interface : le
modèle les lit, vous n'avez pas à le faire. Celles de l'échantillon sont gardées : l'exécution
complète ne les décrit pas à nouveau.

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

← [7. Trier](07-sort.md) · [Documentation](../README.md)
