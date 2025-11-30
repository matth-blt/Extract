# 🎬 Extract - Extracteur d'Images Vidéo

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)

Une application graphique légère pour extraire des images depuis des vidéos avec détection de scènes optionnelle.

## 📋 Fonctionnalités

- ✅ **Extraction d'Images** - Extraire toutes les images d'une vidéo (PNG, TIFF, JPEG)
- ✅ **Détection de Scènes** - Mode Dataset avec détection automatique des changements de scène
- ✅ **Progression en Temps Réel** - Barre de progression avec pourcentage et compteur d'images
- ✅ **Logs Intégrés** - Console intégrée pour suivre le processus d'extraction
- ✅ **Thème Clair/Sombre** - Basculer entre les modes clair et sombre
- ✅ **Interface Moderne** - Interface épurée construite avec CustomTkinter

## 🚀 Installation

### Pour les Utilisateurs
1. Télécharger la dernière version
2. Installer les dépendances : `pip install customtkinter`
3. Lancer `python Extract.py`

### Prérequis
- **Python 3.10+**
- **FFmpeg** installé et disponible dans le PATH
- **FFprobe** (inclus avec FFmpeg)

#### Installer FFmpeg
- **Windows** : Télécharger depuis [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) et ajouter `ffmpeg/bin` au PATH
- **macOS** : `brew install ffmpeg`
- **Linux** : `sudo apt install ffmpeg`

## 📦 Structure du Projet

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## 🎨 Fonctionnalités Détaillées

### 1️⃣ Extraction d'Images
Extrait toutes les images d'une vidéo en fichiers individuels.
- **Formats** : PNG (Sans perte), TIFF (Archivage), JPEG (Léger)
- **Mise à l'échelle** : Haute qualité (`spline+accurate_rnd+full_chroma_int`)
- **Numérotation** : Séquentielle avec zéros (`00000001.png`, `00000002.png`, ...)

### 2️⃣ Mode Dataset (Détection de Scènes)
Extrait automatiquement uniquement les images aux changements de scène - idéal pour créer des datasets d'entraînement.
- **Filtre** : `select='gt(scene,0.15)'` détecte les changements visuels significatifs
- **Sortie** : Fréquence d'images variable (`-vsync vfr`) pour ignorer les images similaires

### 3️⃣ Suivi de Progression en Temps Réel
- Utilise `ffprobe` pour obtenir la durée de la vidéo
- Analyse la sortie FFmpeg pour afficher le pourcentage de progression
- Affiche l'image en cours d'extraction

### 4️⃣ Formats Supportés

| Format | Codec | Format Pixel | Cas d'Usage |
|--------|-------|--------------|-------------|
| PNG | png | rgb24 | Sans perte, édition |
| TIFF | tiff (deflate) | rgb24 | Archivage |
| JPEG | mjpeg | yuvj420p | Léger, web |

## 🖥️ Utilisation

1. **Sélectionner l'Entrée** - Parcourir ou coller le chemin vers un fichier vidéo (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`)
2. **Sélectionner la Sortie** - Choisir le dossier de destination pour les images extraites
3. **Choisir le Format** - Sélectionner PNG, TIFF ou JPEG
4. **Activer le Mode Dataset** (optionnel) - Cocher pour extraire uniquement les changements de scène
5. **Cliquer sur Extraire** - Suivre la progression dans la console de logs

## 🛠️ Détails Techniques

L'application construit des commandes FFmpeg comme :
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

Avec le Mode Dataset activé :
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "select='gt(scene,0.15)',showinfo" -vsync vfr \
  -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

## 📝 Licence

Ce projet est open source. Voir [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **FFmpeg** - Le cœur du traitement vidéo
- **CustomTkinter** - Framework UI Python moderne
