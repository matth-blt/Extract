# Extract - Video Frame Extractor

[![Français](https://img.shields.io/badge/lang-Français-blue.svg)](README_FR.md)

A modern GUI application to extract frames from videos with optional HDR tonemapping and scene detection.

## Features

- ✅ **Frame Extraction** — Extract all frames from a video (PNG, TIFF, JPEG)
- ✅ **HDR Mode** — Automatic HDR detection (HDR10/PQ, HLG) with HDR→SDR tonemapping
- ✅ **Scene Detection** — Dataset mode with automatic scene change detection
- ✅ **Real-time Progress** — Live progress bar with percentage
- ✅ **Integrated Logs** — Built-in console to monitor extraction
- ✅ **Dark/Light Theme** — Toggle between dark and light Material Design modes
- ✅ **Modern UI** — Material Design 3 interface built with Flet

## Installation

### For Users
```bash
pip install flet
python Extract.py
```

### Prerequisites
- **Python 3.10+**
- **Flet** — `pip install flet`
- **FFmpeg** installed and available in PATH (with `libzimg` for HDR mode)
- **FFprobe** (included with FFmpeg)

#### Installing FFmpeg
- **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Essentials or Full build — includes libzimg)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

> **Verify HDR support:** `ffmpeg -filters | grep zscale` — should return a result.

## Project Structure

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## Detailed Features

### Frame Extraction
Extracts all frames from a video into individual images.
- **Formats**: PNG (Lossless), TIFF (Archive), JPEG (Lightweight)
- **Scaling**: High quality (`spline+accurate_rnd+full_chroma_int`)
- **Numbering**: Zero-padded sequential (`00000001.png`, `00000002.png`, ...)

### HDR Mode (Tonemapping)
Automatically detects HDR video and applies HDR→SDR tonemapping for SDR-compatible output.

**Automatic detection** via `ffprobe`:
| HDR Format | `color_transfer` value |
|---|---|
| HDR10 (PQ) | `smpte2084` |
| HLG | `arib-std-b67` |

**Available tonemap operators:**
| Operator | Description |
|---|---|
| `hable` | Filmic, good highlight rolloff (default) |
| `mobius` | Smooth, good for moderate HDR content |
| `reinhard` | Simple global operator |
| `clip` | Hard clip — fastest, lowest quality |

**FFmpeg filter chain used:**
```
zscale=t=linear:npl=<npl>
→ format=gbrpf32le
→ zscale=p=bt709
→ tonemap=tonemap=<operator>:desat=0
→ zscale=t=bt709:m=bt709:r=tv
→ format=rgb24   (PNG/TIFF) | yuv420p (JPEG)
```

> ⚠️ HDR mode requires FFmpeg compiled with `--enable-libzimg`. The app checks availability at startup.

### Dataset Mode (Scene Detection)
Automatically extracts only frames at scene changes — ideal for creating training datasets.
- **Threshold**: Adjustable slider (0.05–0.40, default 0.15)
- **Output**: Variable frame rate (`-vsync vfr`) to skip similar frames

HDR Mode and Dataset Mode are fully compatible and can be combined.

### Supported Formats

| Format | Codec | Pixel Format | Use Case |
|--------|-------|--------------|----------|
| PNG | png | rgb24 | Lossless, editing |
| TIFF | tiff (deflate) | rgb24 | Archival |
| JPEG | mjpeg | yuvj420p | Lightweight, web |

## Usage

1. **Select Input** — Browse to a video file (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`)
2. **Select Output** — Choose destination folder
3. **Choose Format** — PNG, TIFF, or JPEG
4. **Enable Dataset Mode** (optional) — Adjust scene threshold slider
5. **Enable HDR Mode** (optional) — Auto-detected; choose tonemap operator and peak luminance
6. **Click Extract** — Monitor progress and logs

## Technical Details

### Standard SDR extraction
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -map 0:v -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

### HDR tonemapping extraction
```bash
ffmpeg -hide_banner -progress pipe:1 -i "input_hdr.mkv" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,
       tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24" \
  -c:v png -pix_fmt rgb24 -start_number 0 "output/%08d.png"
```

### HDR + Scene Detection
```bash
ffmpeg ... -vf "zscale=t=linear:npl=100,...,format=rgb24,
                select='gt(scene,0.15)',showinfo" \
  -vsync vfr -c:v png ...
```

## License

This project is open source. See [LICENSE](LICENSE) for details.

## Acknowledgements

- **FFmpeg** — The backbone of video processing
- **Flet** — Modern Python UI framework (powered by Flutter)
- **libzimg / zscale** — HDR color space conversion