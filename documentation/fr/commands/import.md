# `import` : récupérer ce que seul votre NAS contient

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `import` · 🇬🇧 [English](../../en/commands/import.md)

## En bref

**Copier dans vos photos les photos et vidéos qu'une sauvegarde est seule à avoir encore : jamais
celles que vous avez mises de côté ou supprimées exprès.**

Votre NAS (ou un ancien disque) est un [dossier de sauvegarde](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque) :
l'audit le compare à vos photos et dit ce qu'il est seul à contenir. `import` copie ces fichiers
dans vos photos, chacun vérifié, pour ne plus dépendre du NAS pour les garder.

**Quand** : une fois un dossier de sauvegarde ajouté (`mh folders add --backup \\NAS\Photos`),
après un [`audit`](audit.md) qui dit *fichiers sont seulement là, jamais dans vos photos*.

**Essayez** :

```powershell
mh import
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit : copie des fichiers **dans** vos photos (sous `From NAS`), n'en modifie jamais un. |
| La sauvegarde | Seulement lue (montée `:ro`) : rien n'est écrit, déplacé ni supprimé sur le NAS. |
| Besoin | Un dossier de sauvegarde ; vos dossiers de photos **sans** `:ro` ; `/journal` ; `/cache`. |
| Annuler | [`undo <run>`](undo.md) retire les copies (une copie modifiée depuis est gardée). |
| Avec `mh` | `mh import`, `mh import --yes`. |

## Ce qui est copié, ce qui ne l'est pas

`import` fait d'abord un audit, avec la sauvegarde, puis trie ce qu'elle est seule à contenir :

- **Copiés** : les fichiers dont le contenu n'a jamais été dans vos photos.
- **Pas proposés, comptés à part** : ceux que vous avez **mis de côté** avant (une photo de
  rafale, une quasi-copie, une photo choisie ou indésirable, en quarantaine ou purgée depuis), et
  ceux que vous avez **supprimés** dans l'Explorateur, confirmés ou en attente de
  [`review --gone`](review.md). L'audit dit combien : *2 autres fichiers sont des fichiers que
  vous avez mis de côté ou supprimés avant : pas proposés.* Une suppression par erreur ? Le
  fichier est toujours sur le NAS : copiez-le à la main.
- **Listés à part** : une photo dont une **quasi-copie** est dans vos photos (une autre taille ou
  un autre format, un HEIC sur le NAS et son JPG sur le PC) : *probablement déjà dans vos
  photos*, pas copiée.
- **Une seule fois** : deux fichiers identiques de la sauvegarde (même taille, même début et même
  fin) sont copiés une fois.

Les copies vont dans **`From NAS`** dans votre premier dossier de photos, les dossiers du NAS
gardés en dessous (`C:\Photos\From NAS\2019\Été\IMG_0007.jpg`), ou dans le dossier de `--to`.
Triez-les ensuite avec [`classify`](classify.md) et [`sort`](sort.md), comme n'importe quel
dossier.

## Comment une copie est faite

Chaque fichier est d'abord noté dans le journal, copié sous un nom temporaire (le NAS est lu une
seule fois, l'empreinte calculée pendant la lecture), relu et comparé à la source (SHA-256), puis
reçoit son nom et sa date de modification. Un nom pris entre-temps n'est jamais remplacé. L'audit
suivant voit les copies comme vos photos : il ne reste rien à importer.

## Vitesse

Par le réseau, seule la liste des fichiers du NAS est lue pour la plupart d'entre eux (taille,
date : 253 fichiers en 0,1 s, mesuré). D'un fichier de même taille qu'une de vos photos, seuls
ses 64 premiers et 64 derniers Ko sont lus : même taille, même début et même fin, il est dans
vos photos. Le NAS n'est jamais lu en entier, seuls les fichiers vraiment copiés le sont. À
travers Docker Desktop, un NAS se lit à environ **15 Mo/s** (mesuré sur un Synology en
Ethernet) : 300 Go de photos de 5 Mo, environ 8 minutes pour une première comparaison au lieu
de 5 h 30 en lisant tout (estimé à partir de ce débit) ; les suivantes ne lisent que ce qui a
changé.

Le compromis : un fichier du NAS dont le début et la fin sont ceux d'une de vos photos mais dont
le milieu diffère compte comme présent dans vos photos. Il reste sur le NAS : rien n'est perdu.

## Options

| Option | Ce qu'elle fait |
|---|---|
| `--to CHEMIN` | Dossier qui reçoit les copies (chemin de l'hôte) ; par défaut : `From NAS` dans votre premier dossier de photos. |
| `--yes`, `-y` | Copier sans demander. |
| `--backup CHEMIN` | Le dossier de sauvegarde d'où importer, s'il n'est pas dans `config.toml` (`mh` passe les vôtres). |

## Bon à savoir

- **Un NAS avec un ancien SMB** : Docker Desktop ne lit un NAS qu'en SMB 3. Si `mh` dit que le NAS
  propose une version plus ancienne, dans DSM (Synology) : *Panneau de configuration → Services
  de fichiers → SMB → Paramètres avancés → Protocole SMB maximum : SMB3*.
- **Le NAS éteint** : `import` le dit ; l'audit continue sans lui.
- **Sûr** : refusé sans journal, ou avec vos dossiers de photos en lecture seule, comme toute
  commande qui modifie des fichiers.

## Pour aller plus loin

- [Comparer une sauvegarde ou un ancien disque](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque)
- [Plusieurs dossiers](../start/03-several-folders.md)

## L'aide intégrée

<details>
<summary><code>import --help</code></summary>

<!-- capture: help-import.txt -->
```text
 Utilisation : media-hygiene import [OPTIONS]

 Copie dans vos photos ce qu'une sauvegarde (un NAS) est seule à contenir,
 jamais ce que vous avez mis de côté ou supprimé avant ; chaque copie prouvée
 (journalisé, annulable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --to            <str>  Dossier qui reçoit les copies (chemin de l'hôte) ;    │
│                        par défaut : « From NAS » dans votre premier dossier  │
│                        de photos, les dossiers de la sauvegarde gardés en    │
│                        dessous.                                              │
│ --yes   -y             Copier sans demander d'abord.                         │
│ --help  -h             Affiche ce message et quitte.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque : comparé, jamais  │
│                        modifié. Dit ce qui lui manque et ce que lui seul     │
│                        contient. Répétable.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
