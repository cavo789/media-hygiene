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
| Écrit | Un `config.toml` commenté dans `/config`, la première fois seulement ; avec `--upgrade`, les réglages qui lui manquent ; avec `--convention`, les dispositions de la convention de tri, une fois votre oui donné ; avec `tidy --apply`, les entrées retirées (une copie dans `/cache/config-backups/` d'abord). |
| Annuler | Supprimez `config.toml` pour revenir aux valeurs par défaut. |
| Avec `mh` | `mh config`. Depuis la page d'accueil, cette étape affiche ce qu'elle écrit dans la page elle-même (rien dans le terminal) ; tapée, elle écrit comme avant. |

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

## La convention de tri : `--convention`

`config.toml` est écrit en entier au premier lancement : une nouvelle disposition par défaut ne
l'atteint donc jamais. Un fichier écrit avant la
[convention de tri](../sort/04-classify.md#la-convention--année-mois-événement) garde
`{year}/{category}` et ses dossiers *À vérifier* / *À trier* ; `classify` le dit en une ligne.
`config --convention` liste chaque disposition qui diffère, ancienne → nouvelle, **demande**,
puis les écrit (commentaires gardés) et relit le fichier :

```powershell
mh config --convention --dry-run   # lister seulement
mh config --convention             # lister, demander, écrire
```

Rien n'est réécrit sans votre oui. Vos règles ne sont pas touchées : une règle dont la catégorie
a plusieurs niveaux de dossiers (`Fêtes/Noël`) est nommée par `classify`, pour que vous la
raccourcissiez.

## Le faire maigrir : `config tidy`

Au fil des années, `config.toml` garde des entrées qui ne pointent plus sur rien : une règle
`match = "path"` dont `sort` a déplacé les photos, un `[[places.folders]]` dont le dossier a
été renommé. `config tidy` les liste, chacune avec sa raison, **sans rien changer** 🔒 :

```powershell
mh config tidy           # lister seulement
mh config tidy --apply   # retirer les entrées cochées
```

| Entrée | Ne pointe plus sur rien quand |
|---|---|
| `[folders]` `preferred`, `protected`, `excluded`, `backups` | le dossier n'existe pas, ou est cité deux fois |
| `[[places.folders]]` | son dossier n'existe pas, ou est cité deux fois |
| `[[classify.rules]]` `match = "path"` / `"camera"` | aucun chemin / aucun appareil de l'index ne correspond à son `pattern` |
| `[[classify.rules]]` `match = "date_range"` | aucune photo indexée n'a été prise à ces dates : montrée **non cochée** (une règle écrite avant un import) ; `--dates` la coche aussi |
| `[[classify.clocks]]` | aucune photo de cet appareil à ces dates |

Un dossier sur un lecteur non monté (une clé USB) n'est **pas jugé**, et c'est dit. Un index
vide ne juge aucune règle : lancez d'abord `audit` sur tous vos dossiers. Vos lieux dessinés à
la main et les endroits écartés ne sont jamais proposés.

`--apply` copie d'abord `config.toml` dans `/cache/config-backups/` (daté), retire les entrées
cochées (commentaires et ordre gardés), puis relit le fichier et dit combien sont parties. Pour
annuler, recopiez ce fichier sur `config.toml` : la console donne la ligne. À la fin de `sort`,
une ligne 💡 dit quand des entrées ne pointent plus sur rien.

Les événements retenus par les pages vivent dans `/config/events/<année>.toml`, pas dans
`config.toml`. Ceux qu'une version plus ancienne a écrits dans `config.toml` (une règle
`date_range` nommée comme sa catégorie, telle `Turin` ou `Turin (juillet 2019)`) sont listés par
`config tidy` et déplacés là par `--apply`, une seule fois, après la même copie datée ; vos règles
écrites à la main restent dans `config.toml`.

## Qui l'emporte ?

De la plus faible à la plus forte : la valeur par défaut, `config.toml`, une variable
d'environnement (`-e MEDIA_HYGIENE_<SECTION>__<CLÉ>=…`, comme
`-e MEDIA_HYGIENE_CLEAN__CONFIRM=false`), puis l'option de la ligne de commande.

## Bon à savoir

- `config` a l'action `tidy` et les options `--upgrade`, `--convention`, `--dry-run`, `--apply`
  et `--dates` ; les options globales s'appliquent aussi (`--locale`, `--verbosity`).
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
 Utilisation : media-hygiene config [OPTIONS] [action]:<tidy>

 🔒 Lecture seule : ne modifie jamais vos photos. Affiche chaque réglage, son
 origine, et les points de montage.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   action      <tidy>  tidy : lister les entrées de config.toml qui ne        │
│                       pointent plus sur rien (dossiers disparus, règles sans │
│                       photo).                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --apply                 Avec tidy : retirer les entrées cochées, après une   │
│                         copie de config.toml.                                │
│ --dates                 Avec tidy : cocher aussi les règles date_range sans  │
│                         photo.                                               │
│ --upgrade               Ajouter à votre config.toml les réglages de cette    │
│                         version, avec leur explication ; vos valeurs et      │
│                         commentaires sont gardés.                            │
│ --convention            Passer les rangements  de votre config.toml à la     │
│                         convention de tri année/année-mois/événement :       │
│                         montre chaque changement, demande, écrit.            │
│ --dry-run               Avec --upgrade ou --convention : lister ce qui       │
│                         changerait, sans rien écrire.                        │
│ --help        -h        Affiche ce message et quitte.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
