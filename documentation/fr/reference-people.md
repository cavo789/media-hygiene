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
✅ Visages prêts, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Ctrl+C l'arrête ; rien
n'est modifié.
```

La page montre les groupes, du plus grand au plus petit, quelques dizaines de visages chacun ;
un clic sur un visage ouvre sa photo. Rien n'y est encore nommé ni modifié : cette première
version **trouve et regroupe**. Nommer les groupes (« Mamie », un dossier par enfant) viendra
ensuite.

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
- **`people --forget`** supprime tous les visages du cache (leur place dans le fichier est
  écrasée), puis relit l'index pour montrer qu'il n'en reste aucun.

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

Ils choisissent seulement quels visages sont regroupés, et comment : les changer ne fait rien
analyser à nouveau. Pour essayer une autre valeur une fois :
`-e MEDIA_HYGIENE_PEOPLE__SIMILARITY=0.45`.

## Pas encore là

- Nommer les groupes dans la page (fusionner deux groupes, retirer un visage erroné, ignorer les
  inconnus).
- Utiliser les noms : une règle `person` dans `classify`, une colonne dans l'inventaire, un mot
  pour `search` et les fichiers compagnons `.xmp`.
- Les visages des vidéos.

Pour **retrouver** les photos de quelqu'un, un gestionnaire de photos comme Immich le fait déjà
bien ; `people` est là pour les **ranger** selon qui y figure, avec `classify` et `sort`.
