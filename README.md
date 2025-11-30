# 🎬 Extract - Video Frame Extractor

[![Français](https://img.shields.io/badge/lang-Français-blue.svg)](README_FR.md)

A lightweight GUI application to extract frames from videos with optional scene detection.

## 📋 Features

- ✅ **Frame Extraction** - Extract all frames from a video (PNG, TIFF, JPEG)
- ✅ **Scene Detection** - Dataset mode with automatic scene change detection
- ✅ **Real-time Progress** - Live progress bar with percentage and frame counter
- ✅ **Integrated Logs** - Built-in console to monitor extraction process
- ✅ **Dark/Light Theme** - Toggle between dark and light modes
- ✅ **Modern UI** - Clean interface built with CustomTkinter

## 🚀 Installation

### For Users
1. Download the latest release
2. Install dependencies: `pip install customtkinter`
3. Run `python Extract.py`

### Prerequisites
- **Python 3.10+**
- **FFmpeg** installed and available in PATH
- **FFprobe** (included with FFmpeg)

#### Installing FFmpeg
- **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `ffmpeg/bin` to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## 📦 Project Structure

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## 🎨 Detailed Features

### 1️⃣ Frame Extraction
Extracts all frames from a video into individual images.
- **Formats**: PNG (Lossless), TIFF (Archive), JPEG (Lightweight)
- **Scaling**: High quality (`spline+accurate_rnd+full_chroma_int`)
- **Numbering**: Zero-padded sequential (`00000001.png`, `00000002.png`, ...)

### 2️⃣ Dataset Mode (Scene Detection)
Automatically extracts only frames at scene changes - ideal for creating training datasets.
- **Filter**: `select='gt(scene,0.15)'` detects significant visual changes
- **Output**: Variable frame rate (`-vsync vfr`) to skip similar frames

### 3️⃣ Real-time Progress Tracking
- Uses `ffprobe` to get video duration
- Parses FFmpeg output to display live progress percentage
- Shows current frame being extracted

### 4️⃣ Supported Formats

| Format | Codec | Pixel Format | Use Case |
|--------|-------|--------------|----------|
| PNG | png | rgb24 | Lossless, editing |
| TIFF | tiff (deflate) | rgb24 | Archival |
| JPEG | mjpeg | yuvj420p | Lightweight, web |

## 🖥️ Usage

1. **Select Input** - Browse or paste path to video file (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`)
2. **Select Output** - Choose destination folder for extracted frames
3. **Choose Format** - Select PNG, TIFF, or JPEG
4. **Enable Dataset Mode** (optional) - Check to extract only scene changes
5. **Click Extract** - Monitor progress in the log console

## 🛠️ Technical Details

The application builds FFmpeg commands like:
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

With Dataset Mode enabled:
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "select='gt(scene,0.15)',showinfo" -vsync vfr \
  -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

## 📝 License

This project is open source. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- **FFmpeg** - The backbone of video processing
- **CustomTkinter** - Modern Python UI framework