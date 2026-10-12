# 0. Installer Docker

[Documentation](../README.md) › Pour commencer, avant l'étape 1 · 🇬🇧 [English](../../en/start/00-install-docker.md)

media-hygiene ne s'installe pas comme un programme habituel : il vient sous forme d'*image*
Docker, une boîte qui contient déjà tout ce dont il a besoin (Python, les décodeurs de photos et
de vidéos…). Docker est le programme qui ouvre cette boîte sur votre ordinateur. Vous installez
Docker **une fois** ; ensuite, chaque commande `docker run …` de ce guide télécharge et démarre
l'outil toute seule.

Déjà fait ? `docker run --rm hello-world` affiche *Hello from Docker!* : passez directement à
l'[étape 1](01-first-audit.md).

## Sous Windows

Il vous faut Windows 10 ou 11, 64 bits, à jour, et environ 5 Go d'espace libre pour Docker et
l'outil.

### 1. Installer Docker Desktop

1. Téléchargez **Docker Desktop for Windows** sur
   [docker.com](https://www.docker.com/products/docker-desktop/) (la version *AMD64* sur presque
   tous les PC ; *ARM64* seulement sur un ordinateur Windows ARM, comme une Surface à processeur
   Snapdragon).
2. Lancez l'installation et gardez cochée l'option **Use WSL 2 instead of Hyper-V**. WSL 2 est
   le petit Linux que Windows fait tourner pour Docker : l'installation le met en place pour
   vous.
3. Redémarrez l'ordinateur quand il le demande.

Ou, dans une fenêtre PowerShell, la même chose en une ligne :

```powershell
winget install --exact --id Docker.DockerDesktop
```

### 2. Le démarrer

Ouvrez **Docker Desktop** depuis le menu Démarrer. La première fois, acceptez les conditions
d'utilisation ; un compte n'est **pas** nécessaire : passez la connexion (*Skip*). Attendez que le
coin inférieur gauche affiche *Engine running*, en vert.

> 💡 Docker Desktop doit être **démarré** pour chaque commande de ce guide : son icône de baleine
> 🐳 se trouve dans la zone de notification, à côté de l'horloge. Pour qu'il soit toujours prêt,
> cochez *Start Docker Desktop when you sign in to your computer* dans *Settings › General*.

Docker Desktop est gratuit pour un usage personnel, l'enseignement et les petites entreprises
(moins de 250 employés *et* moins de 10 millions de dollars de chiffre d'affaires annuel) ; les
plus grandes ont besoin d'un abonnement payant ([les conditions](https://www.docker.com/pricing/faq/)).

### 3. Le vérifier

Ouvrez une **nouvelle** fenêtre PowerShell (menu Démarrer, tapez *PowerShell*) et tapez :

```powershell
docker run --rm hello-world
```

*Hello from Docker!* et quelques lignes d'explication : Docker fonctionne. Vos lecteurs `C:`,
`D:`… sont accessibles à Docker tels quels : rien d'autre à régler.

### Si ça ne marche pas

| Vous voyez | Que faire |
|---|---|
| *docker : Le terme « docker » n'est pas reconnu* | L'installation n'est pas finie, ou la fenêtre a été ouverte avant : ouvrez une nouvelle fenêtre PowerShell. Redémarrez l'ordinateur si besoin. |
| *error during connect* … *The system cannot find the file specified* | Docker Desktop n'est pas démarré : ouvrez-le, et attendez *Engine running*. |
| *Virtualization support not detected*, ou *WSL 2 requires an update* | Lancez `wsl --update` dans PowerShell. Si le message reste, la virtualisation est désactivée dans le micrologiciel de l'ordinateur (BIOS/UEFI : *Intel VT-x*, *AMD-V* ou *SVM*) : la documentation du fabricant explique comment l'activer. |
| Docker Desktop reste sur *Starting the Docker Engine…* | Quittez-le (clic droit sur la baleine › *Quit Docker Desktop*), puis rouvrez-le ; sinon, redémarrez l'ordinateur. |

### Avec WSL

Vous préférez un terminal WSL (Ubuntu…) ? Docker Desktop le sert aussi : dans *Settings ›
Resources › WSL integration*, activez votre distribution, puis tapez `docker run --rm
hello-world` dedans. N'installez **pas** en plus Docker dans WSL avec les étapes Linux
ci-dessous : deux moteurs Docker sur un même ordinateur se gênent.

## Sous Linux

Sous Linux, Docker Engine suffit : pas besoin de Docker Desktop. Les commandes ci-dessous valent
pour **Ubuntu** et **Debian**, et leurs dérivées (Linux Mint, Pop!_OS…) ; pour une autre
distribution, suivez [les instructions officielles](https://docs.docker.com/engine/install/).

### 1. Installer Docker Engine

Le script de Docker ajoute son dépôt de paquets et installe la dernière version :

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Vous préférez voir chaque étape ? [Install using the apt
repository](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) fait la
même chose à la main.

> ⚠️ Sous Ubuntu, évitez le paquet **snap** (`snap install docker`, ou la case cochée en
> installant Ubuntu Server) : par défaut, il ne voit pas les dossiers hors de votre dossier
> personnel, comme un disque USB sous `/media`. `snap list docker` dit si vous l'avez ;
> `sudo snap remove docker` le retire.

### 2. L'utiliser sans `sudo`

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

La première ligne démarre Docker maintenant et à chaque démarrage. La seconde vous permet de
lancer `docker` sans `sudo` : **déconnectez-vous puis reconnectez-vous** pour qu'elle
s'applique. Les membres du groupe `docker` contrôlent entièrement Docker, comme un administrateur
le ferait : ajoutez-y seulement vous-même
([pourquoi](https://docs.docker.com/engine/security/#docker-daemon-attack-surface)).

### 3. Le vérifier

```bash
docker run --rm hello-world
```

*Hello from Docker!* : Docker fonctionne.

### Si ça ne marche pas

| Vous voyez | Que faire |
|---|---|
| *permission denied while trying to connect to the Docker daemon socket* | Le groupe `docker` n'est pas encore actif : déconnectez-vous puis reconnectez-vous (ou redémarrez). |
| *Cannot connect to the Docker daemon … Is the docker daemon running?* | `sudo systemctl start docker`. |
| *docker: command not found* | L'installation a échoué : relancez le script et lisez ses dernières lignes. |

### Votre première commande sous Linux

Le guide montre des chemins Windows. Sous Linux, montez votre dossier sous `/data`, suivi de son
propre chemin, et lancez l'outil en votre nom pour que les fichiers qu'il crée vous appartiennent :

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "$HOME/Images:/data$HOME/Images:ro" \
  cavo789/media-hygiene --locale fr audit
```

`$HOME/Images` devient `/data/home/<vous>/Images`, et l'outil montre vos dossiers par leur vrai
chemin, `/home/<vous>/Images`. Un `\` en fin de ligne continue la commande sur la suivante.

## Sur un Mac

Installez [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (*Apple
Silicon* ou *Intel*, comme l'indique *À propos de ce Mac*), ouvrez-le, puis `docker run --rm
hello-world` dans le Terminal. Les commandes de ce guide suivent le modèle Linux ci-dessus.

## Mettre à jour

- **Docker** : Docker Desktop propose lui-même ses mises à jour ; sous Linux, vos mises à jour
  système habituelles (`sudo apt upgrade`) l'incluent.
- **L'outil** : `docker pull cavo789/media-hygiene` récupère sa dernière version.

---

[Documentation](../README.md) · Suivant : **[1. Votre premier audit](01-first-audit.md)** →
