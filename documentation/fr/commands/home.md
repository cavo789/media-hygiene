# `home` : la page d'accueil, dans votre navigateur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `home` · 🇬🇧 [English](../../en/commands/home.md)

## En bref

**Une page dans votre navigateur : où vous en êtes, l'étape suivante en un gros bouton, toutes
les étapes des guides, vos rapports.**

`home` montre dans votre navigateur ce que [`status`](status.md) et [`menu`](menu.md) montrent
dans le terminal : le dernier audit, la quarantaine, les passages encore annulables, les revues
pas encore appliquées ; l'étape qui suit en un gros bouton ; chaque étape des trois guides
([nettoyer](../clean/quick-guide.md), [trier](../sort/quick-guide.md),
[retrouver](../find/quick-guide.md)) avec sa commande `mh` et ses badges ; vos rapports, et
quelques images trouvées par le dernier audit. Elle peut aussi lancer l'audit elle-même, sa
progression affichée dans la page.

**Quand** : chaque fois que vous préférez cliquer plutôt que taper, ou que vous ne savez plus
quelle est la suite.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene home
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées par la page : montez-les en `:ro`. L'audit lancé depuis la page ne fait que les lire. |
| Il faut | Les dossiers de l'outil (`/reports`, `/journal`, `/quarantine`, `/cache`), comme pour `status` ; vos dossiers pour l'audit ; `-p 127.0.0.1:8088:8088` pour la page. |
| Écrit | Rien par elle-même ; l'audit lancé depuis la page écrit son cache et son rapport, comme `audit`. |
| Annuler | Rien à annuler ; chaque étape garde sa propre annulation. |
| Avec `mh` | `mh home`. |

## Ce que montre la page

- **Étape suivante** : pourquoi, et la commande complète en gros bouton : *le dernier audit a
  trouvé des copies en trop : 'clean' les met de côté*, **mh clean**. Quand tout est appliqué, la
  page le dit.
- **Auditer dans cette page** 🔒 : **Auditer maintenant** lit vos dossiers comme `mh audit`, avec
  les mêmes réglages. Chaque étape (liste, empreintes, comparaison, preuve d'identité…) s'affiche
  avec ses comptes au fil de l'eau ; à la fin, les chiffres de l'audit, le temps de chaque étape
  (*Temps par étape : liste 1,2 s · vérifications 3,4 s · …*, la ligne qu'affiche
  `mh --verbosity verbose audit`), *Ce que vous pouvez faire*, et le lien vers le nouveau rapport. Un audit à la fois ; **Arrêter l'audit** l'arrête
  entre deux fichiers : le cache garde ce qu'il a lu, et l'audit suivant repart de là.
- **Où vous en êtes** : les lignes de [`status`](status.md), et le passage que `mh undo` remet
  encore en place.
- **Ce que le dernier audit a trouvé** : quelques aperçus de son rapport.
- **Rapports** : le dernier audit et le dernier nettoyage, et *Tous les rapports*
  (`index.html`), ouverts dans un nouvel onglet depuis la page elle-même.
- **Les étapes des trois guides**, numérotées comme dans [`mh menu`](menu.md) : **👉** l'étape
  proposée, **✅** une étape que les dossiers de l'outil prouvent faite, les badges 🔒 photos
  intactes, ↩️ annulable, ⚠️ définitif, *facultatif*, 🤖 quand un modèle local est réglé. Une
  étape que `mh` ne peut pas remplir pour vous (`mh album "Noël" --category …`) montre la
  commande à taper.

## Lancer une étape

La page ne modifie jamais vos photos elle-même. Ce que fait le bouton d'une étape dépend du `mh`
qui a ouvert la page :

- **`mh` seul** (et donc le raccourci du Bureau et le clic droit sur un dossier), qui lance les
  étapes de la page et le lui dit : **Lancer** (ou le gros
  bouton) ferme la page et confie l'étape à `mh`, dans la fenêtre où `mh` tourne (PowerShell sous Windows), avec les dossiers
  dont cette étape a besoin. La page affiche *En cours dans la fenêtre où mh tourne : cette page
  revient quand c'est fini* ; quand `mh` rouvre la page d'accueil, la page se recharge d'elle-même.
  L'étape choisie est le code de sortie de la commande, `100 + n` pour l'étape `n` de `mh menu` :
  c'est ainsi que `mh` sait quoi lancer.
- **Sinon** (`mh home` tapé, un `mh` plus ancien, ou `docker run` seul) : le bouton s'appelle **Copier**. Il
  copie la commande (*Copiée : mh clean*) et la page continue de tourner ; arrêtez-la avec Ctrl+C
  dans la fenêtre où `mh` tourne (PowerShell sous Windows), collez-y la commande (clic droit) et appuyez sur Entrée. Quand le
  navigateur refuse de copier (page ouverte à une autre adresse que `127.0.0.1` ou `localhost`),
  la commande est sélectionnée : appuyez vous-même sur Ctrl+C.

Chaque autre page ([`review`](review.md), [`review-sort`](review-sort.md),
[`places`](places.md), [`search`](search.md), [`browse`](browse.md), [`people`](people.md))
porte un lien **⌂ Accueil** en bas à droite : il ferme cette page (ce que vous y avez décidé est
déjà enregistré) et attend la page d'accueil à la même adresse.

## Options

| Option | Rôle |
|---|---|
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- La page ne répond qu'à `127.0.0.1` ou `localhost`, et seulement à ses propres boutons : un
  autre site ne peut pas choisir une étape à votre place.
- Ctrl+C dans le terminal ferme la page ; un audit en cours s'arrête entre deux fichiers.
- Les étapes sont relues dans les dossiers de l'outil à chaque chargement de la page : ce
  qu'une autre fenêtre a fait apparaît au rechargement suivant. Un bouton d'une page dessinée
  avant un tel changement est refusé (*Les étapes ont changé depuis l'affichage de la page*) et
  la page remontre les étapes.

## Aller plus loin

- [`menu` : les mêmes étapes dans le terminal](menu.md)
- [`status` : où vous en êtes, en une seconde](status.md)

## L'aide intégrée

<details>
<summary><code>home --help</code></summary>

<!-- capture: help-home.txt -->
```text
 Utilisation : media-hygiene home [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. La page d'accueil dans votre
 navigateur : où vous en êtes, l'étape suivante en un bouton, toutes les étapes
 des guides, les rapports.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut : 8088.                       │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
