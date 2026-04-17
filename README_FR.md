# Extract - Extracteur de Frames Vidéo

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)

Une application GUI moderne pour extraire des frames de vidéos avec tonemapping HDR optionnel et détection de scènes.

## Fonctionnalités

- ✅ **Extraction de Frames** — Extraire toutes les frames d'une vidéo (PNG, TIFF, JPEG)
- ✅ **Mode HDR** — Détection automatique HDR (HDR10/PQ, HLG) avec tonemapping HDR→SDR
- ✅ **Détection de Scènes** — Mode Dataset avec détection automatique des changements de scène
- ✅ **Progression en Temps Réel** — Barre de progression live avec pourcentage
- ✅ **Logs Intégrés** — Console intégrée pour surveiller l'extraction
- ✅ **Thème Sombre/Clair** — Basculer entre les modes Material Design
- ✅ **Interface Moderne** — Material Design 3 avec Flet

## Installation

### Pour les Utilisateurs
```bash
pip install flet
python Extract.py
```

### Prérequis
- **Python 3.10+**
- **Flet** — `pip install flet`
- **FFmpeg** installé et disponible dans le PATH (avec `libzimg` pour le mode HDR)
- **FFprobe** (inclus avec FFmpeg)

#### Installer FFmpeg
- **Windows** : Télécharger depuis [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (build Essentials ou Full — inclut libzimg)
- **macOS** : `brew install ffmpeg`
- **Linux** : `sudo apt install ffmpeg`

> **Vérifier le support HDR :** `ffmpeg -filters | grep zscale` — doit retourner un résultat.

## Structure du Projet

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## Fonctionnalités Détaillées

### Extraction de Frames
Extrait toutes les frames d'une vidéo en images individuelles.
- **Formats** : PNG (Sans perte), TIFF (Archivage), JPEG (Léger)
- **Mise à l'échelle** : Haute qualité (`spline+accurate_rnd+full_chroma_int`)
- **Numérotation** : Séquentielle avec zéros (`00000001.png`, `00000002.png`, ...)

### Mode HDR (Tonemapping)
Détecte automatiquement les vidéos HDR et applique un tonemapping HDR→SDR pour une sortie compatible SDR.

**Détection automatique** via `ffprobe` :
| Format HDR | Valeur `color_transfer` |
|---|---|
| HDR10 (PQ) | `smpte2084` |
| HLG | `arib-std-b67` |

**Opérateurs de tonemapping disponibles :**
| Opérateur | Description |
|---|---|
| `hable` | Filmique, bon rendu des hautes lumières (défaut) |
| `mobius` | Doux, adapté aux contenus HDR modérés |
| `reinhard` | Opérateur global simple |
| `clip` | Coupure dure — le plus rapide, qualité moindre |

**Chaîne de filtres FFmpeg utilisée :**
```
zscale=t=linear:npl=<npl>
→ format=gbrpf32le
→ zscale=p=bt709
→ tonemap=tonemap=<opérateur>:desat=0
→ zscale=t=bt709:m=bt709:r=tv
→ format=rgb24   (PNG/TIFF) | yuv420p (JPEG)
```

> ⚠️ Le mode HDR nécessite un FFmpeg compilé avec `--enable-libzimg`. L'application vérifie la disponibilité au démarrage.

### Mode Dataset (Détection de Scènes)
Extrait automatiquement uniquement les frames lors des changements de scène — idéal pour créer des datasets d'entraînement.
- **Seuil** : Slider ajustable (0.05–0.40, défaut 0.15)
- **Sortie** : Taux de trame variable (`-vsync vfr`)

Le Mode HDR et le Mode Dataset sont entièrement compatibles et peuvent être combinés.

### Formats Supportés

| Format | Codec | Format Pixel | Cas d'usage |
|--------|-------|--------------|-------------|
| PNG | png | rgb24 | Sans perte, édition |
| TIFF | tiff (deflate) | rgb24 | Archivage |
| JPEG | mjpeg | yuvj420p | Léger, web |

## Utilisation

1. **Sélectionner l'entrée** — Parcourir jusqu'au fichier vidéo (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`)
2. **Sélectionner la sortie** — Choisir le dossier de destination
3. **Choisir le format** — PNG, TIFF ou JPEG
4. **Activer le Mode Dataset** (optionnel) — Ajuster le seuil de détection
5. **Activer le Mode HDR** (optionnel) — Auto-détecté ; choisir l'opérateur de tonemap et la luminance crête
6. **Cliquer sur Extract** — Surveiller la progression et les logs

## Détails Techniques

### Extraction SDR standard
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -map 0:v -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

### Extraction avec tonemapping HDR
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input_hdr.mkv" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,
       tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24" \
  -c:v png -pix_fmt rgb24 -start_number 0 "output/%08d.png"
```

### HDR + Détection de Scènes
```bash
ffmpeg ... -vf "zscale=t=linear:npl=100,...,format=rgb24,
                select='gt(scene,0.15)',showinfo" \
  -vsync vfr -c:v png ...
```

## Licence

Ce projet est open source. Voir [LICENSE](LICENSE) pour les détails.

## Remerciements

- **FFmpeg** — Le moteur du traitement vidéo
- **Flet** — Framework UI Python moderne (propulsé par Flutter)
- **libzimg / zscale** — Conversion d'espace colorimétrique HDR
