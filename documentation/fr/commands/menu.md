# `menu` : chaque étape, la prochaine en premier

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `menu` · 🇬🇧 [English](../../en/commands/menu.md)

## En bref

**Perdu ? Tapez `mh menu` : chaque étape des guides dans le terminal, la prochaine proposée,
Entrée la lance.** `mh` seul montre les mêmes étapes sur la [page d'accueil](home.md), dans votre
navigateur.

Inutile de retenir le nom des commandes. `mh menu` montre les étapes des trois guides
([nettoyer](../clean/quick-guide.md), [trier](../sort/quick-guide.md),
[retrouver](../find/quick-guide.md)) dans l'ordre, chacune avec sa commande `mh …` complète, et en
propose **une** : celle que donnerait [`status`](status.md). Appuyez sur Entrée pour la lancer, ou
tapez le numéro d'une autre étape. La commande choisie est ensuite rappelée, *La prochaine fois,
tapez-la directement : mh clean* : vous apprenez les commandes en vous en servant.

**Quand** : chaque fois que vous ne savez plus quelle est la suite.

**Essayer** (une fois `mh` écrit, [étape 0 des guides](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh)) :

```powershell
mh menu
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Le menu lui-même ne les modifie jamais, ne les lit même pas. L'étape choisie dit ce qu'elle risque : 🔒, ↩️ ou ⚠️. |
| Il faut | `mh` : le menu lance par lui l'étape choisie, avec les bons dossiers. |
| Écrit | Rien. |
| Annuler | Rien à annuler ; chaque étape garde sa propre annulation. |
| Avec `mh` | `mh menu`. |

## Ce qu'il montre

Sous *Où vous en êtes* (le dernier audit, la quarantaine), une ligne par étape :

- **👉** l'étape proposée, celle que lance Entrée ; **✅** une étape que les dossiers de l'outil
  prouvent faite (un audit vu, plus aucune copie, un tri appliqué, des mots ou des visages
  trouvés). Rien n'est marqué quand l'outil ne peut pas le savoir.
- le **numéro** à taper, puis la **commande** que vous taperez plus tard vous-même ;
- ce que fait l'étape, et son badge : 🔒 photos intactes, ↩️ annulable, ⚠️ définitif,
  *facultatif* ; 🤖 à côté de `classify` et `tags` quand un modèle local est indiqué
  (`[classify.ai] model`). La ligne sous le tableau rappelle ce que veulent dire 🔒, ↩️ et ⚠️.
- Une étape que l'outil remplit d'après ce qu'il sait prend son argument (`mh purge <exécution>`,
  `mh undo <exécution>`) ; sans rien à purger ni à annuler, elle n'a pas de numéro. Un album
  demande des mots que vous seul connaissez (`mh album "Noël" --category …`) : à taper vous-même.

Tant qu'une étape de nettoyage est proposée, celles du tri et de la recherche sont estompées :
elles viennent après. Le menu prend la largeur de votre fenêtre ; *Lecture de là où vous en
êtes…* s'affiche pendant qu'il compte la quarantaine, ce qui prend quelques secondes quand elle
contient des milliers de fichiers.

La dernière section, sous Windows, rend `mh` plus facile à atteindre : `mh shortcut` (une icône sur
le Bureau) et `mh explorer` (le clic droit d'un dossier). `mh open`, après `mh audit`, montre les
rapports dans votre navigateur. `mh` lance ces trois-là lui-même : [ce que `mh` fait
lui-même](launcher.md#ce-que-mh-fait-lui-même).

<!-- capture: menu.txt -->
```text
─────────────────────── media-hygiene — où vous en êtes ────────────────────────
Dernier audit: 2026-10-16 19:26 (aujourd'hui) — 10 fichiers, 4 copies en trop
(5,9 Mo), 1 illisibles.
Quarantaine : vide.

      Nettoyer les doublons
✅  1 mh audit                            Trouver les doublons et  🔒
                                          les fichiers abîmés
    2 mh open                             Lire les rapports dans   🔒
                                          votre navigateur
👉  3 mh clean                            Mettre les copies en     ↩️
                                          trop de côté (demande
                                          d'abord)
    4 mh history                          Ce qu'a fait chaque      🔒
                                          exécution
      mh undo                             Remettre les fichiers de ↩️
                                          la dernière exécution
                                          (rien à faire pour
                                          l'instant)
    5 mh review                           Choisir les meilleures   🔒 facultatif
                                          photos de chaque rafale,
                                          dans le navigateur
    6 mh clean --tier near --decisions    Appliquer vos choix : ce ↩️ facultatif
                                          que vous avez écarté va
                                          en quarantaine
      mh purge                            Libérer la place de la   ⚠️
                                          quarantaine,
                                          définitivement (rien à
                                          faire pour l'instant)
      Trier les photos
✅  7 mh classify                         Proposer une             🔒
                                          arborescence rangée,
                                          dans un classeur que
                                          vous corrigez
    8 mh review-sort                      Nommer les événements    🔒 facultatif
                                          dans le navigateur
    9 mh places                           Nommer vos lieux sur une 🔒 facultatif
                                          carte
   10 mh people                           Nommer les visages       🔒 facultatif
   11 mh sort                             Déplacer les photos      ↩️
                                          comme le dit le classeur
      mh album "Christmas" --category …   Réunir une sélection     ↩️ facultatif
                                          dans un album de liens
                                          (à taper vous-même)
      Retrouver une photo
   12 mh tags                             Donner des mots à vos    🔒
                                          photos
   13 mh search                           Retrouver une photo par  🔒
                                          ses mots, dans le
                                          navigateur
   14 mh xmp                              Emporter les mots dans   ↩️ facultatif
                                          d'autres logiciels photo
   15 mh inventory                        Toutes les photos et     🔒 facultatif
                                          vidéos dans un classeur
                                          Excel
      Ouvrir mh sans rien taper (Windows)
   16 mh shortcut                         Une icône sur le Bureau  🔒 facultatif
                                          et dans le menu Démarrer
                                          ouvre ce menu
   17 mh explorer                         Clic droit sur un        🔒 facultatif
                                          dossier dans
                                          l'Explorateur : ce menu,
                                          sur ce dossier

🔒 vos photos ne sont pas touchées · ↩️ peut être annulé · ⚠️ définitif
🤖 classify et tags peuvent aussi interroger un modèle d'IA local : indiquez
[classify.ai] model dans config.toml (mh config).
Une étape à taper vous-même demande des mots que vous seul connaissez :
https://cavo789.github.io/media-hygiene/fr/sort/quick-guide/
Vos dossiers : mh folders. Une nouvelle version : mh update.
Entrée lance l'étape 3 (mh clean). Un autre numéro lance cette étape. Ctrl+C
pour quitter.
⚠️  Le menu lance ses étapes par mh : écrivez-le une fois avec 'launcher' (étape
0 des guides), puis tapez mh seul.
```

## Bon à savoir

- `menu` n'a pas d'option.
- Le menu ne répond jamais à votre place : `clean`, `sort` et `purge` demandent toujours avant
  d'agir.
- Après l'étape, le menu ne revient pas : tapez de nouveau `mh menu`, il montre où vous en êtes
  désormais. La [page d'accueil](home.md) (`mh` seul), elle, revient après chaque étape.
- Pour une session à distance, un PC lent ou sans navigateur : `mh menu` n'ouvre aucune page.
- `docker run … cavo789/media-hygiene` sans commande affiche toujours le `--help` : seul `mh` peut
  lancer l'étape choisie avec les bons dossiers.
- `docker run -it … menu` montre le menu mais ne peut lancer aucune étape : écrivez d'abord `mh`.

## Aller plus loin

- [`status`](status.md) : où vous en êtes, en détail.
- [`launcher`](launcher.md) : écrire `mh`.

## L'aide intégrée

<details>
<summary><code>menu --help</code></summary>

<!-- capture: help-menu.txt -->
```text
 Utilisation : media-hygiene menu [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Chaque étape des guides avec
 sa commande, la prochaine en premier : ce que montre 'mh' seul, Entrée la
 lance.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
