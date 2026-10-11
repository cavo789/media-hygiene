# Les personnes

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-people.md)

`people` trouve les **visages** de vos photos, regroupe ceux qui se ressemblent, et montre les
groupes dans votre navigateur : sans doute une personne par groupe. Il lit les photos que les
audits ont listées, depuis le cache : lancez d'abord un [audit](start/01-first-audit.md), avec
`/cache` monté ([étape 2](start/02-keep-the-cache.md)). Les visages restent **dans le cache**,
sur votre ordinateur.

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  -p 127.0.0.1:8088:8088 `
  cavo789/media-hygiene --locale fr people
```

```text
🔒 Lecture seule : vos photos et vidéos ne sont pas touchées.
🔒 Les visages sont des données personnelles : ils restent dans le cache (/cache), rien n'est
envoyé nulle part. 'people --forget' les supprime tous.
Téléchargement des deux modèles de visages dans le cache, une seule fois (39 Mo) : ils tournent
sur cet ordinateur, rien de vos photos n'est envoyé.
2 000 photos sur 2 000 à analyser ; les prochaines exécutions n'analysent que les nouvelles.
✅ 2 000 photos analysées : 1 436 visages, 0,21 s par photo.
✅ 1 436 visages dans 2 000 photos : 37 groupes de visages semblables, les plus grands 212, 140,
96, 51, 33 ; 288 vus une seule fois.
Laissés de côté : 301 visages de moins de 40 pixels, 64 plus flous que 30.
✅ Nommés : Chloé : 412 photos, Manon : 236 photos.
✅ Visages prêts, ouvrez http://127.0.0.1:8088/ dans votre navigateur pour les nommer ; chaque
nom est enregistré aussitôt dans config.toml. Ctrl+C l'arrête ; les photos ne sont pas modifiées.
```

La page montre d'abord les personnes déjà nommées, puis les groupes, du plus grand au plus petit,
quelques dizaines de visages chacun ; un clic sur un visage ouvre sa photo. **Tapez un nom** sur
un groupe pour le nommer (ci-dessous). Les photos ne sont jamais modifiées : les noms vont dans
votre `config.toml` (`/config`). Sans `/config` monté, la page montre les groupes et les noms
déjà donnés, et n'en enregistre aucun.

## Nommer les groupes

| Sur un groupe | Ce que ça fait |
|---|---|
| Taper un nom, puis Entrée | Les visages montrés sont ceux de cette personne. Les noms déjà donnés sont proposés pendant la frappe. Un deuxième groupe nommé comme une personne existante **s'ajoute** à ses visages : un enfant à tous les âges. |
| Choisir (`x`), puis nommer | Nommer plusieurs groupes d'un coup : la même personne coupée en deux groupes. |
| × sur un visage | Ce visage n'est pas cette personne : il est retiré du groupe, et ne reçoit plus jamais ce nom. |
| Ignorer (`i`) | Des inconnus, des affiches, des statues : le groupe n'est plus montré, ni les visages qui lui ressemblent. |
| Oui, c'est … (`y`) | Confirme une suggestion : un groupe dont les visages ressemblent à quelqu'un de déjà nommé, montré « Chloé ? ». |

Le clavier suffit : ↑ ↓ (ou `j` `k`) passent d'un groupe à l'autre, Entrée tape un nom. Chaque
changement est écrit dans `config.toml`, puis **relu dans le fichier** et affiché en haut de la
page (« Enregistré dans config.toml, relu : Chloé, 58 visages confirmés. »). Les noms ressemblent
à ceci :

```toml
[[people.person]]
name = "Chloé"
faces = [
    "/data/c/Photos/2019/IMG_0412.jpg#0",
    "/data/c/Photos/2023/IMG_7781.jpg#1",
]
```

Chaque visage est écrit par sa photo et son numéro dans la photo, jamais par son groupe : un
nouveau regroupement (de nouvelles photos, un autre `similarity`) garde tous les noms. Les autres
visages reçoivent le nom du **visage confirmé le plus proche**, s'ils lui ressemblent assez
(`similarity`) ; en dessous, ils restent sans nom. Les suggestions (« Chloé ? ») ne comptent
jamais avant que vous les confirmiez.

## Les retrouver : `search`

Une fois nommées, les personnes sont des mots de [`search`](commands/search.md), sans rien
lancer d'autre :

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr search Chloé montagne
```

`Chloé montagne` trouve les photos avec Chloé où « montagne » vient de n'importe quelle source
(dossier, ville, ce que le modèle de vision a vu) ; `person:chloe` cherche parmi les personnes
seulement (la casse et les accents ne comptent pas) ; `person:"Mamie Jeanne"` est un nom de deux
mots. Un nom que personne ne porte encore est signalé en une ligne : nommez d'abord le groupe
dans la page.

## Les ranger : une règle `person`

Une fois nommées, les personnes peuvent aussi ranger les photos : une règle `person` de
`classify` ([tri, étape 6](sort/06-write-down-what-you-know.md#les-personnes)) donne une catégorie
aux événements où quelqu'un apparaît.

```toml
[[classify.rules]]
name = "Avec Chloé"
match = "person"
names = ["Chloé"]
category = "Personnes/Chloé"
```

Un événement va à la règle quand au moins **10 %** de ses photos montrent Chloé
(`min_share = 10` : c'est peut-être elle qui prend les photos) ; une photo hors de tout
événement y va quand elle la montre. `names = ["Chloé", "Manon"]` prend les événements avec
l'une ou l'autre ; ajoutez `all = true` pour ceux avec les deux. Les noms sont ceux de la page :
les visages confirmés, et les visages assez proches d'eux, comme `search` les trouve ; les
suggestions ne comptent pas. Un nom que personne ne porte encore arrête `classify` avant toute
lecture, et nomme la règle.

Tout le chemin, du premier `people` aux dossiers triés, pas à pas : [tri, étape
10](sort/10-sort-by-person.md).

## Pendant l'audit : `audit --people`

`audit --people` lance l'audit, puis compte les photos dont les visages n'ont pas encore été
cherchés, en mesure quelques-unes sur votre ordinateur, dit combien de temps prendra le reste,
et **demande** avant de continuer. `--yes` ne demande pas ; sans terminal (pas de `-it`), rien
n'attend : l'audit se termine sans les visages. Aucune page ne s'ouvre : lancez ensuite `people`
pour voir les groupes. `[people] with_audit = true` le fait à chaque audit.

## Comment ça marche

| Étape | Ce qui se passe | Où |
|---|---|---|
| Trouver | YuNet (OpenCV Zoo, licence MIT) trouve chaque visage : un cadre et cinq points (yeux, nez, bouche). | Votre ordinateur |
| Décrire | SFace (OpenCV Zoo, licence Apache 2.0) transforme chaque visage, redressé, en 128 nombres : des nombres proches, sans doute la même personne. | Votre ordinateur |
| Regrouper | Les visages aux nombres assez proches sont regroupés, à nouveau à chaque exécution, en quelques secondes : un nouveau réglage regroupe autrement sans rien analyser à nouveau. | Votre ordinateur |
| Montrer | La page découpe chaque visage dans sa photo quand votre navigateur le demande ; rien n'est écrit. | `127.0.0.1` seulement |

Chaque photo est analysée **une seule fois** : les exécutions suivantes n'analysent que les
photos nouvelles ou modifiées. Ctrl+C s'arrête entre deux photos et garde ce qui est fait. Les
vidéos ne sont pas encore analysées. Une grande collection prend du temps la première fois :
mesurez d'abord (ci-dessous).

## Votre vie privée

Les nombres qui décrivent un visage sont des **données biométriques**, le type de données
personnelles le plus sensible (RGPD, article 9). L'outil les traite comme telles :

- ils restent dans l'index du cache (`/cache`), jamais dans vos photos, jamais dans les rapports ;
- rien n'est envoyé nulle part : les modèles tournent sur votre ordinateur, la page n'est servie
  que sur `127.0.0.1`, et les visages qu'elle montre sont découpés dans les photos à la demande,
  jamais enregistrés ;
- le seul accès au réseau est le **téléchargement, une seule fois, des deux modèles** depuis
  OpenCV Zoo sur GitHub, vérifiés par leur SHA-256. Il n'envoie rien de vos photos. Sans réseau,
  l'erreur nomme les deux fichiers à enregistrer à la main dans le dossier `models` du cache ;
- les noms sont dans votre `config.toml`, en texte : les visages qu'ils nomment y sont écrits par
  photo et numéro, jamais sous forme de nombres qui décrivent un visage ;
- **`people --forget`** supprime tous les visages du cache (leur place dans le fichier est
  écrasée), puis relit l'index pour montrer qu'il n'en reste aucun. Il demande ensuite si les
  noms de `config.toml` partent aussi, et relit le fichier pour le montrer.

## Mesurer d'abord : `--sample`

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr people --sample 200
```

`--sample N` analyse N photos prises au hasard, affiche le temps par photo et l'estimation d'une
exécution complète, puis s'arrête. Les visages trouvés sont gardés : l'exécution complète repart
de là.

## Un dossier d'abord : `--path`

`--path "C:\Photos\2019"` n'analyse et ne regroupe que les photos sous ce dossier (chemin de
l'hôte, tel que vous l'avez monté) ; à répéter pour plusieurs dossiers.

## Réglages : `[people]`

| Réglage | Par défaut | Sens |
|---|---|---|
| `similarity` | `0.363` | À quel point deux visages doivent se ressembler (cosinus, de 0 à 1) pour être la même personne. Plus haut : des groupes plus nombreux et plus petits ; plus bas : des personnes mélangées. `0.363` est la valeur documentée de SFace. |
| `min_face` | `40` | Les visages plus petits que ce nombre de pixels (petit côté de leur cadre) sont laissés de côté : trop petits pour être reconnus. |
| `min_sharpness` | `30` | Les visages plus flous sont laissés de côté : un visage flou s'éloigne du même visage vu net. |
| `with_audit` | `false` | `true` : chaque `audit` cherche aussi les visages, après avoir demandé, comme `audit --people`. |
| `ignored`, `[[people.person]]` | aucun | Écrits par la page : les visages ignorés, et pour chaque personne son nom, ses visages confirmés (`faces`) et ceux qui lui ont été retirés (`rejected`). |

Ils choisissent seulement quels visages sont regroupés, et comment : les changer ne fait rien
analyser à nouveau. Pour essayer une autre valeur une fois :
`-e MEDIA_HYGIENE_PEOPLE__SIMILARITY=0.45`.

## Pas encore là

- Une colonne dans l'inventaire ; les noms dans les fichiers compagnons `.xmp`.
- Les visages des vidéos.

Pour **retrouver** les photos de quelqu'un, un gestionnaire de photos comme Immich le fait déjà
bien ; `people` est là pour les **ranger** selon qui y figure, avec `classify` et `sort`.
