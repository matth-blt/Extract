# Extract — Extracteur de frames vidéo

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)

Application de bureau multiplateforme pour extraire les frames de fichiers vidéo,
avec tonemapping HDR vers SDR optionnel et détection de changements de scène.
Construite avec [Flet](https://flet.dev) et propulsée par FFmpeg.

## Fonctionnalités

- **Extraction de frames** en PNG, TIFF ou JPEG.
- **Tonemapping HDR** avec détection automatique HDR10 (PQ) et HLG.
- **Détection de scènes** (mode Dataset) pour n'extraire que les frames aux changements de scène.
- **Progression en temps réel** avec barre de progression et pourcentage.
- **Console de logs intégrée** pour surveiller chaque extraction.
- **Thèmes sombre et clair** suivant Material Design 3.

## Prérequis

- Python 3.10 ou plus récent (développé et testé sur 3.13).
- [Flet](https://pypi.org/project/flet/) — `pip install flet`.
- FFmpeg et FFprobe disponibles dans le `PATH`.
- Pour le mode HDR, un FFmpeg compilé avec `libzimg` (fournit le filtre `zscale`).

### Installer FFmpeg

| Plateforme | Commande / Source |
|------------|-------------------|
| macOS      | `brew install ffmpeg` |
| Linux      | `sudo apt install ffmpeg` |
| Windows    | [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (build Essentials ou Full) |

Vérifier le support HDR :

```bash
ffmpeg -filters | grep zscale
```

Si la commande ne renvoie rien, le build FFmpeg installé ne contient pas
`libzimg` et le mode HDR restera désactivé. Installez un build complet qui
l'inclut (macOS : [evermeet.cx](https://evermeet.cx/ffmpeg/) ; Windows : gyan.dev Full).

## Installation

```bash
pip install flet
python Extract.py
```

## Utilisation

1. **Sélectionner l'entrée** — choisir un fichier vidéo (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`).
2. **Sélectionner la sortie** — choisir le dossier de destination.
3. **Choisir un format** — PNG, TIFF ou JPEG.
4. **Activer le mode Dataset** (optionnel) — ajuster le seuil de détection de scène.
5. **Activer le mode HDR** (optionnel) — auto-détecté ; choisir l'opérateur de tonemap et la luminance crête.
6. **Cliquer sur Extract** — suivre la progression et les logs dans l'application.

## Fonctionnement

### Extraction de frames

Chaque frame est écrite comme une image individuelle numérotée avec des zéros
(`00000000.png`, `00000001.png`, ...). Une mise à l'échelle haute qualité est
appliquée (`spline+accurate_rnd+full_chroma_int`).

| Format | Codec          | Format pixel | Cas d'usage         |
|--------|----------------|--------------|---------------------|
| PNG    | png            | rgb24        | Sans perte, édition |
| TIFF   | tiff (deflate) | rgb24        | Archivage           |
| JPEG   | mjpeg          | yuvj420p     | Léger, web          |

### Mode HDR (tonemapping)

L'application analyse la source avec `ffprobe` et détecte le HDR à partir de la
métadonnée `color_transfer` :

| Format HDR | `color_transfer` |
|------------|------------------|
| HDR10 (PQ) | `smpte2084`      |
| HLG        | `arib-std-b67`   |

Lorsque le HDR est détecté et activé, une chaîne de tonemapping HDR vers SDR est
appliquée. Opérateurs disponibles :

| Opérateur  | Description                                       |
|------------|---------------------------------------------------|
| `hable`    | Filmique, bon rendu des hautes lumières (défaut)  |
| `mobius`   | Doux, adapté aux contenus HDR modérés             |
| `reinhard` | Opérateur global simple                           |
| `clip`     | Coupure dure — le plus rapide, qualité moindre    |

Chaîne de filtres FFmpeg :

```
zscale=t=linear:npl=<npl>
  -> format=gbrpf32le
  -> zscale=p=bt709
  -> tonemap=tonemap=<opérateur>:desat=0
  -> zscale=t=bt709:m=bt709:r=tv
  -> format=rgb24   (PNG/TIFF) | yuv420p (JPEG)
```

Le mode HDR nécessite un FFmpeg compilé avec `--enable-libzimg` ; la
disponibilité est vérifiée au démarrage.

### Mode Dataset (détection de scènes)

N'extrait que les frames aux changements de scène, ce qui est utile pour
construire des datasets d'entraînement. Le seuil est ajustable (0.05–0.40, défaut
0.15) et un taux de trame variable (`-vsync vfr`) ignore les frames quasi
identiques. Les modes Dataset et HDR peuvent être combinés.

## Référence des commandes

Extraction SDR standard :

```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -map 0:v -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

Extraction avec tonemapping HDR :

```bash
ffmpeg -hide_banner -progress pipe:1 -i "input_hdr.mkv" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,\
tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24" \
  -c:v png -pix_fmt rgb24 -start_number 0 "output/%08d.png"
```

HDR avec détection de scènes :

```bash
ffmpeg ... -vf "zscale=t=linear:npl=100,...,format=rgb24,\
select='gt(scene,0.15)',showinfo" \
  -vsync vfr -c:v png ...
```

## Dépannage

**`CERTIFICATE_VERIFY_FAILED` au premier lancement (macOS)**
Les builds Python.org ne contiennent pas les certificats CA, donc Flet ne peut
pas télécharger son client de bureau. Lancez l'installateur de certificats fourni
une fois :

```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

**Le mode HDR reste désactivé**
Le FFmpeg installé ne contient pas le filtre `zscale`. Installez un build compilé
avec `libzimg` (voir [Installer FFmpeg](#installer-ffmpeg)).

**`ffmpeg` / `ffprobe` introuvable**
Vérifiez que les deux sont installés et présents dans le `PATH`. L'application
désactive l'extraction au démarrage si l'un des deux manque.

## Structure du projet

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## Licence

Ce projet est open source. Voir [LICENSE](LICENSE) pour les détails.

## Remerciements

- **FFmpeg** — décodage, filtrage et encodage vidéo.
- **Flet** — framework UI Python basé sur Flutter.
- **libzimg / zscale** — conversion d'espace colorimétrique HDR.
