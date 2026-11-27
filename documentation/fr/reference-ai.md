# IA locale

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-ai.md)

**media-hygiene fonctionne sans aucune IA à installer ; trois fonctionnalités facultatives sollicitent un modèle local
(Ollama).** Tout le reste s'exécute sur votre processeur, sans carte graphique et sans rien envoyer.

Dans cette documentation, 🤖 marque uniquement ce qui nécessite une IA locale (Ollama). Ce qui est **intégré** ne porte
pas de 🤖 : cela s'exécute à l'intérieur de l'image, sur le processeur.

## Ce qui nécessite quoi

| Fonctionnalité | Modèle | Téléchargé | S'exécute sur | Quitte votre ordinateur | Nécessite |
|---|---|---|---|---|---|
| Doublons, fichiers illisibles, flou, rafales, quasi-doublons, lieux, villes, monuments | aucun : hachages, mesures, la copie GeoNames à l'intérieur de l'image | rien | le processeur | rien | **Intégré** |
| Visages : [`people`](commands/people.md), `/person`, l'orientation devinée | YuNet + SFace (ONNX) | 39 Mo, une fois, dans le cache | le processeur | rien | **Intégré**, sans carte graphique |
| Recherche par le sens : [`tags --meaning`](commands/tags.md) | CLIP image/texte | 894 Mo, une fois, dans le cache | le processeur | rien | **Intégré**, sans carte graphique |
| 🤖 Décrire les photos : [`tags`](commands/tags.md), la règle `subject` de [`classify`](commands/classify.md), [`spots --vision`](commands/spots.md) | un modèle de vision que vous choisissez dans Ollama (`[classify.ai] model`) | par Ollama, sa taille ci-dessous | votre carte graphique, ou le processeur | rien : les photos vont uniquement vers `[classify.ai] url`, gardez-le sur votre ordinateur | **Ollama, facultatif** |

## 🤖 Quel modèle de vision pour votre carte graphique

Un modèle convient si sa taille est inférieure à la mémoire de votre carte graphique (VRAM), avec un peu de marge.
Les tailles sont les tailles de téléchargement affichées sur les pages de la bibliothèque d'Ollama (vérifiées le 2026-11-27 sur
`ollama.com/library/<model>/tags`) ; la mémoire utilisée une fois chargé est proche de celle-ci (mesuré : un
modèle de 17,7 Go a utilisé 17,4 Go dans `ollama ps`).

| Mémoire de la carte graphique | Modèles de vision qui conviennent (taille de téléchargement) | Suggéré |
|---|---|---|
| 2 Go | `moondream:1.8b` (1,7 Go), `qwen3-vl:2b` (1,9 Go) | `qwen3-vl:2b` |
| 4 Go | `llava-phi3:3.8b` (2,9 Go), `qwen2.5vl:3b` (3,2 Go), `qwen3-vl:4b` (3,3 Go), `gemma3:4b` (3,4 Go) | `qwen3-vl:4b` |
| 8 Go | `qwen2.5vl:7b` (6,0 Go), `qwen3-vl:8b` (6,2 Go) | `qwen3-vl:8b` |
| 24 Go | `gemma3:27b` (17 Go), `qwen3-vl:32b` (21 Go) | `qwen3-vl:32b` |

La suggestion est la famille la plus récente de chaque taille ; les réponses des petits modèles sont moins
précises. Mesurez le vôtre avant une exécution complète : `tags --sample 20` affiche le temps par photo et
l'estimation de la collection entière.

Mesuré sur l'ordinateur du mainteneur (carte graphique de 24 Go, 2026-11-27, 6 images synthétiques 768×576,
une phrase + 5 mots chacune) : un modèle de vision 27B (`qwen3.8:27b`, Q4_K_M) a utilisé
17,4 Go de mémoire graphique, a pris 10,9 s pour la première photo (chargement du modèle) puis 1,6 à
2,3 s par photo.

**Sans carte graphique**, Ollama exécute le modèle sur le processeur et dans la mémoire de l'ordinateur
(`ollama ps` affiche alors `100% CPU`) : cela fonctionne, beaucoup plus lentement. Essayez d'abord un petit modèle et
`--sample`.

## Configuration

1. Installez Ollama sur votre ordinateur et téléchargez un modèle, par exemple `ollama pull qwen3-vl:4b`.
2. Dans `config.toml`, `[classify.ai]` : `model = "qwen3-vl:4b"` (`url` est déjà celui de votre ordinateur).
3. `tags --sample 20` 🤖 : le temps par photo et l'estimation.

`model` vide : aucune photo n'est jamais envoyée, et les trois fonctionnalités sont simplement désactivées.
