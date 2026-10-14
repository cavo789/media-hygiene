# `config` : chaque réglage, et d'où il vient

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `config` · 🇬🇧 [English](../../en/commands/config.md)

## En bref

**Vérifier ce que l'outil va utiliser avant qu'il agisse : chaque réglage avec son origine,
chaque dossier avec son état.**

`config` montre chaque réglage, **d'où vient chacun** (la valeur par défaut, `config.toml`, une
variable d'environnement, la ligne de commande), et l'état de chaque point de montage. La
première fois, il crée aussi un `config.toml` commenté, à remplir.

**Quand** : une fois au début, pour obtenir ce `config.toml` ; puis chaque fois qu'un réglage
semble ne pas s'appliquer ou qu'un dossier n'est pas vu.

**Essayer** :

```powershell
mkdir -Force "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene --locale fr config
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées. |
| Il faut | Rien. |
| Conseillé | `/config`, et les mêmes options `-v` que votre commande habituelle, pour voir leur état. |
| Écrit | Un `config.toml` commenté dans `/config`, la première fois seulement ; avec `--upgrade`, les réglages qui lui manquent. |
| Annuler | Supprimez `config.toml` pour revenir aux valeurs par défaut. |
| Avec `mh` | `mh config`. |

## Lancer

```powershell
mkdir -Force "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene --locale fr config
```

La première exécution dit *💡 Un fichier de configuration commenté a été créé :
/config/config.toml*. Ouvrez-le dans `C:\Users\<vous>\media-hygiene\config` avec n'importe quel
éditeur de texte. Créé avec `--locale fr`, il est commenté en français.

## Lire le résultat

- **Réglages effectifs** : une ligne par réglage (`general.timezone`, `folders.preferred`,
  `clean.confirm`…), sa valeur et son *Origine* : `défaut`, `config.toml`, `environnement` ou
  `ligne de commande`.
- **Catégories d'extensions (--ext)** : ce que contiennent `photo`, `raw`, `video`, `media` et vos
  propres catégories.
- **Points de montage** : `/data/…`, `/config`, `/journal`, `/quarantine`, `/reports`, `/cache`,
  chacun *monté*, *lecture seule* ou *non monté* (*rien n'est conservé après l'exécution* pour un
  dossier de l'outil), avec le dossier de votre ordinateur derrière lui quand Docker Desktop le
  donne.

## Après une mise à jour : `--upgrade`

Une version plus récente peut apporter de nouveaux réglages. Votre `config.toml` fonctionne
toujours sans eux (chacun prend sa valeur par défaut), mais ses commentaires n'en disent rien.
`config` le signale en une ligne, *💡 config.toml a été écrit par la version 0.3.0 : 3 nouveaux
réglages depuis.*, puis :

```powershell
# Lister ce qui serait ajouté, sans rien écrire
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene --locale fr config --dry-run

# Les ajouter, chacun avec son explication
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene --locale fr config --upgrade
```

Chaque réglage manquant est ajouté avec son commentaire, après le réglage qui le précède ; une
table manquante est ajoutée entière. **Vos valeurs, vos commentaires et vos règles sont gardés**,
rien n'est déplacé ni supprimé, et les commentaires ajoutés sont dans la langue de votre fichier.
Le fichier est relu sur le disque et la console liste ce qu'il contient désormais. `/config`
monté avec `:ro` est refusé (`--dry-run` fonctionne toujours) ; aucune sauvegarde n'est laissée
dans `/config`.

## Qui l'emporte ?

De la plus faible à la plus forte : la valeur par défaut, `config.toml`, une variable
d'environnement (`-e MEDIA_HYGIENE_<SECTION>__<CLÉ>=…`, comme
`-e MEDIA_HYGIENE_CLEAN__CONFIRM=false`), puis l'option de la ligne de commande.

## Bon à savoir

- `config` a deux options à lui, `--upgrade` et `--dry-run` ; les options globales s'appliquent
  aussi (`--locale`, `--verbosity`).
- `/config` contient `config.toml` **seulement** : n'y mettez jamais rien d'autre.
- Un réglage inconnu de cette version est signalé, avec sa ligne : voir le
  [dépannage](../reference-troubleshooting.md#un-réglage-de-configtoml-est-inconnu-de-cette-version).
  Plusieurs problèmes sont listés un par ligne ; celui d'une règle ou d'un lieu la nomme par son
  numéro et son `name` (`[[classify.rules]] n° 2 (« Anniversaire »)`).

## Pour aller plus loin

- [7. Le fichier de configuration](../clean/07-configuration-file.md#vérifier-ce-que-loutil-utilise--config)
- [Points de montage](../reference-mount-points.md)

## L'aide intégrée

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Utilisation : media-hygiene config [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Affiche chaque réglage, son
 origine, et les points de montage.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --upgrade            Ajouter à votre config.toml les réglages de cette       │
│                      version, avec leur explication ; vos valeurs et         │
│                      commentaires sont gardés.                               │
│ --dry-run            Avec --upgrade : lister les réglages qu'il ajouterait,  │
│                      sans rien écrire.                                       │
│ --help     -h        Affiche ce message et quitte.                           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
