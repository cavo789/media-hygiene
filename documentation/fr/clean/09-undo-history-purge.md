# 9. Annuler, historique, purge

[Documentation](../README.md) › Nettoyer, étape 9 sur 14 · 🇬🇧 [English](../../en/clean/09-undo-history-purge.md)

Un nettoyage n'est pas définitif. Le journal retient chaque action : vous pouvez tout remettre en
place, voir ce que chaque nettoyage a fait et, une fois sûr·e, vider la quarantaine pour de bon.

Avec `mh`, les trois commandes ci-dessous tiennent en une ligne. Sans lui, gardez les mêmes
options `-v` que votre `clean` (étape 8) ; seul le dernier mot change.

## Annuler un nettoyage : `undo`

Vous changez d'avis ? Lancez la même commande avec `undo` au lieu de `clean` :

```powershell
mh undo
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr undo
```

</details>

<!-- capture: undo.txt -->
```text
─────────────── Annulation de l'exécution clean 20261025-084936 ────────────────
🛟 Chaque fichier revient où il était, jamais par-dessus un autre ; ce qui ne
peut pas revenir intact est laissé tel quel, et signalé.

Annulation de l'exécution clean
20261025-084936
┌───────────────────────────┬─────────┐
│ Fichiers traités          │      36 │
│ Taille                    │ 15,6 Mo │
│ Ignorés (laissés intacts) │       0 │
│ En échec                  │       0 │
│ Durée                     │     0 s │
└───────────────────────────┴─────────┘
```

- Chaque fichier mis en quarantaine — les copies en trop d'abord — est remis à sa place, jamais
  par-dessus un autre fichier. Les dossiers de quarantaine qu'il laisse vides s'en vont aussi :
  un `undo` mené à son terme ne laisse rien de l'exécution dans la quarantaine.
- Chaque copie supprimée avec `clean --delete` est **reconstruite à partir de la copie gardée**,
  date comprise, même d'un disque à l'autre.
- Sans nom, `undo` restaure la dernière exécution ; `undo <exécution>` restaure celle-là. Les
  noms des exécutions viennent d'`history`, ci-dessous, et des dernières lignes de chaque
  nettoyage.
- Un fichier déjà revenu, ou dont la copie a disparu, est laissé tel quel et listé avec la
  raison : `undo` n'écrase jamais rien et ne devine rien.
- Un [tri](../sort/07-sort.md) s'annule de la même façon : les fichiers reviennent, les dossiers
  qu'il a supprimés reviennent, ceux qu'il a créés s'en vont. Un tri arrêté puis relancé avec le
  même classeur s'annule en entier : tous ses passages, le plus récent d'abord, après une seule
  question (`--yes` la saute).
- `undo` a besoin du même `/journal`, de dossiers non montés en `:ro`, et du même `/quarantine`
  quand l'exécution y a mis des fichiers (fichiers illisibles, fichiers compagnons orphelins,
  quasi-doublons, photos de rafale, copies d'autres fichiers, les `Thumbs.db` et autres qu'un tri a
  écartés). Sinon il refuse avant de modifier quoi que ce soit et nomme l'exécution. Une exécution
  qui n'a fait que supprimer des copies (`--delete`) ou déplacer des fichiers n'a pas besoin de
  quarantaine.

## Voir ce qui a été fait : `history`

```powershell
mh history
```

<!-- capture: history.txt -->
```text
Exécutions (les plus récentes d'abord)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃                 ┃         ┃          ┃        ┃      En ┃ Dossiers ┃         ┃
┃ Exécution       ┃ Comman… ┃ Supprim… ┃ Libéré ┃ quaran… ┃ supprim… ┃ Restau… ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ 20261025-084938 │ clean   │        1 │      0 │      41 │        9 │       0 │
│ 20261025-084936 │ clean   │        1 │      0 │      35 │        7 │      43 │
└─────────────────┴─────────┴──────────┴────────┴─────────┴──────────┴─────────┘
💡 'media-hygiene undo <run>' restaure les fichiers d'une exécution.
```

Une ligne par exécution, la plus récente d'abord : la commande qui l'a faite, combien de fichiers
elle a supprimés, l'espace libéré, combien de fichiers elle a mis en quarantaine, et combien ont
été restaurés depuis. Une colonne *Déplacés* apparaît dès qu'une exécution a déplacé des fichiers
vers un autre de vos dossiers. Ici le premier nettoyage a été entièrement annulé (36 fichiers
restaurés), puis refait.

## Vider la quarantaine : `purge`

La quarantaine garde ce que `clean` a déplacé : les copies en trop, les fichiers illisibles, les
fichiers compagnons orphelins et, si vous l'avez demandé, quasi-doublons et photos de rafale.
Leur place n'est libérée que maintenant : une fois que vous les avez vérifiés (ouvrez le dossier
de quarantaine dans l'Explorateur), `purge` les supprime **pour de bon**. C'est la seule commande
qui efface du contenu (avec `clean --delete`, si vous l'utilisez), et elle le dit avant de
demander :

```powershell
mh purge
```

<!-- capture: purge.txt -->
```text
⚠️  'purge' efface pour de bon : ces fichiers ne pourront pas revenir, même avec
'undo'. C'est, avec 'clean --delete', la seule façon dont l'outil supprime du
contenu.
❓ Effacer la quarantaine de 20261025-084938 (41 fichiers, 16,4 Mo) ? [o/N] o
✅ Quarantaine vidée : 16,4 Mo libérés.
💡 'undo' ne pourra plus restaurer ces fichiers.
```

- Sans nom, `purge` vide la quarantaine de tous les nettoyages ; `purge <exécution>` seulement
  celle-là.
- Il demande d'abord, comme `clean` ; `--yes` saute la question.
- Après une purge, `undo` ne peut plus ramener ces fichiers. La date de la purge est écrite à
  côté du journal de l'exécution (`<exécution>.purged.json`, le journal lui-même n'est jamais
  réécrit) : `mh import --phone --free` la donne sur la vignette d'une photo mise de côté par celle-ci.
- Plutôt garder une copie ? `purge --to <dossier>` copie d'abord la quarantaine sur un NAS, un
  disque ou le dossier synchronisé d'un cloud, vérifie chaque octet, puis la vide — voir
  [`purge`](../commands/purge.md).

Où va le reste de la place ? **⚖ Fichiers les plus lourds** dans
[`browse`](../commands/browse.md) liste les fichiers les plus lourds de toute la photothèque, les
vidéos d'abord ; [`shrink`](../commands/shrink.md) allège les vidéos des anciens appareils,
les originaux en quarantaine.

## Où en suis-je ? `status`

De retour après quelques jours, vous ne savez plus quelle exécution est en quarantaine, ni si un
tri a été appliqué ? `status` lit les dossiers de l'outil, sans analyser vos photos (une seconde
environ), et dit :

- le dernier audit ou nettoyage : quand, et ce qu'il a trouvé ;
- la quarantaine : combien de fichiers, quelle place, depuis quand ;
- les exécutions que `undo` peut encore restaurer, avec la commande `undo` complète ;
- les séries de rafales encore à voir et les décisions de `review` pas encore appliquées ;
- la dernière proposition de `classify`, et si `sort` l'a appliquée ;

puis **une** étape suivante, en commande complète. Une quarantaine de plus de 30 jours
(`purge_hint_days`, dans la section `[clean]` de `config.toml`) est la première chose qu'il
propose de purger. Montez les mêmes dossiers que pour `clean` (ou tapez `mh status`) : un dossier
non monté est signalé, jamais une erreur.

## Ce que vous avez mis de côté reste de côté

Vous avez mis de côté des photos de rafale, des quasi-doublons, des photos choisies dans
[`search`](../commands/search.md) ou [`review --junk`](../commands/review.md) ; des mois plus
tard, une sauvegarde de téléphone les ramène, sous d'autres noms. Le journal se souvient du
contenu de chaque fichier mis de côté par un tel choix (sa taille et son SHA-256), même après
`purge` : l'audit suivant les reconnaît, quel que soit leur nom aujourd'hui, et le dit sur une
ligne à part :

```text
↩️ 23 photos et vidéos que vous aviez mises de côté sont revenues (45 Mo) : 'clean' les remet de côté.
```

Le rapport les liste dans une section à part (*Revenus après une mise de côté*), chacune avec
son aperçu, quand et pourquoi elle a été mise de côté, et où elle se trouvait alors. `clean` les
remet en quarantaine avec le reste de son plan, sans autre question : sa question habituelle les
compte sur une ligne à part (*↩️ 23 photos et vidéos que vous aviez déjà mises de côté sont
revenues (45 Mo) : retour en quarantaine.*), et `history` les compte à part (*Dont revenus*).

- Pour en garder une finalement : `undo` de ce nettoyage. Le dernier mot est alors le vôtre :
  elle n'est plus proposée.
- Seul ce que vous avez mis de côté **par un choix** est retenu : une copie identique qui
  revient est un simple doublon (son contenu est toujours gardé ailleurs) ; un fichier abîmé
  n'est pas retenu.
- Une version redimensionnée ou recompressée d'une photo (d'autres octets) n'est pas reconnue.
  Un fichier supprimé dans l'Explorateur l'est, une fois que vous le confirmez (ci-dessous).
- Un fichier revenu dans un dossier [protégé](07-configuration-file.md) n'est jamais touché.
- `returned = false` dans la section `[clean]` de `config.toml` ne les cherche jamais.

### Supprimés dans l'Explorateur ?

Le journal ne connaît pas les photos supprimées dans l'Explorateur. L'index, lui, voit qu'elles
ont disparu : un fichier qu'un audit ne trouve plus là où il était, ni ailleurs (un dossier
renommé dans l'Explorateur est suivi, jamais compté), sous un dossier monté cette fois.
Supprimé exprès, ou déplacé sur un disque non branché ? Vous seul pouvez le dire, alors l'audit
demande :

```text
🗑️ 312 photos et vidéos ont disparu depuis le dernier audit (supprimées dans l'Explorateur ?) : dites lesquelles vous avez supprimées exprès, pour que media-hygiene les mette de côté si elles reviennent.
```

Quand il n'y a ni copie à mettre de côté ni rafale à trier, l'audit se termine en vous
menant là : *👉 Et maintenant : dites dans 'review --gone' quels fichiers disparus vous avez
supprimés exprès*, avec la commande complète. Lancé par `mh`, l'audit vous demande en plus
*Ouvrir maintenant la revue des fichiers disparus ?* : répondez `o` et la page s'ouvre.

`mh review --gone` les montre par dossier et par jour, chacune avec son aperçu quand le cache en
garde un (sinon son nom, sa date, sa taille et son appareil) : `D` supprimé exprès, `M` déplacé
ailleurs, `G` tout le groupe supprimé exprès. Vos réponses sont enregistrées dans
`decisions.json` ; le `clean --decisions` suivant retient les fichiers supprimés exprès (rien ne
bouge : une ligne dans le journal, comptée par `history` sous *Supprimés dans l'Explorateur*) et
oublie les autres. Quand l'un d'eux revient, il est proposé comme un fichier que vous aviez mis
de côté. `undo` de ce nettoyage les oublie. Un fichier disparu dont le contenu est toujours là
(une copie ailleurs) ou réapparaît plus tard (un disque rebranché) quitte la liste tout seul :
supprimer l'une de deux copies ne perd rien.

## Gardez le dossier du journal

Le journal est léger, et c'est lui qui rend `undo` possible, et qui permet à l'audit de
reconnaître les fichiers mis de côté s'ils reviennent. Ne le supprimez jamais tant que vous
pourriez encore vouloir restaurer un nettoyage.

---

← [8. Nettoyer](08-clean.md) · [Documentation](../README.md) · Suivant : **[10. Trier les rafales dans le navigateur](10-review-bursts.md)** →
