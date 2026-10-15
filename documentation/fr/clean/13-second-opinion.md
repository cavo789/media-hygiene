# 13. Un second avis

[Documentation](../README.md) › Nettoyer, étape 13 sur 13 · 🇬🇧 [English](../../en/clean/13-second-opinion.md)

Avant de supprimer des photos de famille, un second avis rassure.
[Czkawka](https://github.com/qarmin/czkawka) est un détecteur de doublons indépendant et open
source, écrit différemment et avec une autre fonction de hachage. Deux outils écrits
indépendamment font rarement la même erreur : s'ils sont d'accord, vous pouvez nettoyer en
confiance.

Cette étape est facultative : `clean` ne l'exige jamais.

## Lancer `crosscheck`

Avec les mêmes dossiers que l'audit (`mh` les monte) :

```powershell
mh crosscheck
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr crosscheck
```

</details>

Czkawka est livré dans l'image : rien d'autre à installer, rien à coller. `crosscheck` refait
l'audit (rapidement, grâce au cache), puis lance Czkawka sur les mêmes dossiers : mêmes
extensions, mêmes dossiers exclus, toutes les tailles de fichier. Czkawka ne fait que lire, et
affiche ses propres messages. Sur des dizaines de milliers de photos, comptez quelques minutes la
première fois ; avec `/cache`, il y garde son propre cache et les fois suivantes ne relisent que
ce qui a changé (`--fresh` relit tout). Ses résultats, `czkawka.json`, vont dans votre dossier de
rapports.

<details>
<summary>Vous préférez lancer Czkawka vous-même ?</summary>

`crosscheck --print-command` ne lance pas Czkawka : il affiche la commande qui le lance dans sa
propre image (l'image communautaire `jlesage/czkawka`, environ 500 Mo), avec vos dossiers. Là où
elle indique `<le dossier que vous montez sur /reports>`, écrivez votre dossier de rapports. Elle
ressemble à ceci :

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v "$HOME\media-hygiene\reports:/out" `
  jlesage/czkawka:v26.09.2 czkawka_cli dup -d /data -m 1 -W -N -C /out/czkawka.json `
  -x 3g2,3gp,arw,avi,avif,bmp,cr2,cr3,dng,flv,gif,heic,heif,jpe,jpeg,jpg,m2ts,m4v,mkv,mov,mp4,mpeg,mpg,mts,nef,orf,pef,png,raf,rw2,srw,tif,tiff,ts,webm,webp,wmv
```

Depuis WSL, écrivez vos dossiers `/mnt/c/...` au lieu de `C:\...`. Une fois qu'il a tourné,
`crosscheck --print-command` compare ses résultats.

</details>

## Lire le verdict

Après le résumé habituel et le passage de Czkawka, les deux outils sont comparés groupe par
groupe :

<!-- capture: crosscheck.txt|re:^Résultats de Czkawka|d'accord -->
```text
Résultats de Czkawka du 2026-10-15 16:23 UTC.
✅ Czkawka est d'accord : les mêmes 32 copies en trop dans 20 groupes.
```

- *Czkawka est d'accord : les mêmes N copies en trop dans G groupes* : les deux outils ont trouvé
  exactement les mêmes doublons.
- Ou *Czkawka n'est pas d'accord sur N groupes*, suivi de chaque groupe trouvé par un seul des
  deux outils. Regardez-les avant de nettoyer.

Les fichiers que media-hygiene laisse volontairement de côté ne sont pas comparés : ils sont
comptés, pas signalés comme des différences. Ce sont les autres types de fichiers, les dossiers
exclus ou système (corbeille, vignettes), les fichiers cassés. Rien à faire de votre côté. Les
dossiers jamais analysés sont nommés, ceux qui contiennent le plus de fichiers d'abord : vous voyez
tout de suite où Czkawka a cherché et media-hygiene non.

Si des photos ont été déplacées ou supprimées depuis le passage de Czkawka (par un `clean`, par
exemple), ses résultats ne sont plus à jour : un `audit` ou un `clean` suivant les ignore, et le
message donne les deux façons d'en sortir. Soit vous relancez `crosscheck` ; soit vous supprimez le
fichier `czkawka.json` qu'il nomme (dans votre dossier des rapports) si vous ne voulez plus de
second avis.

## Où apparaît le verdict

- Dans le rapport HTML du `crosscheck`, en haut.
- Dans chaque `clean` suivant, juste avant sa question (*Résultats de Czkawka du … UTC*), comme
  rappel.
- Dans le rapport de nettoyage :

![Le haut d'un rapport de nettoyage avec la note : Czkawka est d'accord : les mêmes 32 copies en trop dans 20 groupes](../images/clean-report.webp)

C'est une information : `clean` ne l'exige jamais.

## Vous avez tout vu

C'est tout l'outil. Désormais, les [pages de référence](../README.md#référence) répondent aux
questions précises : chaque option, les points de montage, ce qui est vérifié avant chaque
suppression.

---

← [12. Décider paire par paire](12-decide-pair-by-pair.md) · [Documentation](../README.md)
