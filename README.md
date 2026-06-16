# Extract — Video Frame Extractor

[![Français](https://img.shields.io/badge/lang-Français-blue.svg)](README_FR.md)

A cross-platform desktop application for extracting frames from video files, with
optional HDR-to-SDR tonemapping and scene-change detection. Built with
[Flet](https://flet.dev) and powered by FFmpeg.

<img width="341" height="420" alt="img" src="https://github.com/user-attachments/assets/d89e487d-325a-41b7-bb9a-0fc0707d2a52" />

## Features

- **Frame extraction** to PNG, TIFF, or JPEG.
- **HDR tonemapping** with automatic HDR10 (PQ) and HLG detection.
- **Scene detection** (Dataset mode) for extracting only frames at scene changes.
- **Real-time progress** with a live progress bar and percentage.
- **Integrated log console** to monitor each extraction.
- **Dark and light themes** following Material Design 3.

## Requirements

- Python 3.10 or newer (developed and tested on 3.13).
- [Flet](https://pypi.org/project/flet/) — `pip install flet`.
- FFmpeg and FFprobe available on the `PATH`.
- For HDR mode, an FFmpeg build compiled with `libzimg` (provides the `zscale` filter).

### Installing FFmpeg

| Platform | Command / Source |
|----------|------------------|
| macOS    | `brew install ffmpeg` |
| Linux    | `sudo apt install ffmpeg` |
| Windows  | [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Essentials or Full build) |

Verify HDR support:

```bash
ffmpeg -filters | grep zscale
```

If this returns nothing, the current FFmpeg build lacks `libzimg` and HDR mode
will remain disabled. Install a full build that includes it
(macOS: [evermeet.cx](https://evermeet.cx/ffmpeg/); Windows: gyan.dev Full).

## Installation

```bash
pip install flet
python Extract.py
```

## Usage

1. **Select input** — choose a video file (`.mkv`, `.mp4`, `.webm`, `.mov`, `.avi`, `.wmv`, `.flv`).
2. **Select output** — choose the destination folder.
3. **Choose a format** — PNG, TIFF, or JPEG.
4. **Enable Dataset mode** (optional) — adjust the scene-detection threshold.
5. **Enable HDR mode** (optional) — auto-detected; pick a tonemap operator and peak luminance.
6. **Click Extract** — follow progress and logs in the application.

## How it works

### Frame extraction

Every frame is written as an individual, zero-padded image
(`00000000.png`, `00000001.png`, ...). High-quality scaling is applied
(`spline+accurate_rnd+full_chroma_int`).

| Format | Codec          | Pixel format | Use case            |
|--------|----------------|--------------|---------------------|
| PNG    | png            | rgb24        | Lossless, editing   |
| TIFF   | tiff (deflate) | rgb24        | Archival            |
| JPEG   | mjpeg          | yuvj420p     | Lightweight, web    |

### HDR mode (tonemapping)

The application probes the source with `ffprobe` and detects HDR from the
`color_transfer` metadata:

| HDR format | `color_transfer` |
|------------|------------------|
| HDR10 (PQ) | `smpte2084`      |
| HLG        | `arib-std-b67`   |

When HDR is detected and enabled, an HDR-to-SDR tonemapping chain is applied.
Available operators:

| Operator   | Description                                   |
|------------|-----------------------------------------------|
| `hable`    | Filmic, good highlight rolloff (default)      |
| `mobius`   | Smooth, suited to moderate HDR content        |
| `reinhard` | Simple global operator                        |
| `clip`     | Hard clip — fastest, lowest quality           |

FFmpeg filter chain:

```
zscale=t=linear:npl=<npl>
  -> format=gbrpf32le
  -> zscale=p=bt709
  -> tonemap=tonemap=<operator>:desat=0
  -> zscale=t=bt709:m=bt709:r=tv
  -> format=rgb24   (PNG/TIFF) | yuv420p (JPEG)
```

HDR mode requires FFmpeg compiled with `--enable-libzimg`; availability is
checked at startup.

### Dataset mode (scene detection)

Extracts only frames at scene changes, which is useful for building training
datasets. The threshold is adjustable (0.05–0.40, default 0.15) and a variable
frame rate (`-vsync vfr`) skips near-duplicate frames. Dataset mode and HDR mode
can be combined.

## Command reference

Standard SDR extraction:

```bash
ffmpeg -hide_banner -progress pipe:1 -i "input.mp4" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -map 0:v -c:v png -pix_fmt rgb24 -start_number 0 \
  "output/%08d.png"
```

HDR tonemapping extraction:

```bash
ffmpeg -hide_banner -progress pipe:1 -i "input_hdr.mkv" \
  -sws_flags spline+accurate_rnd+full_chroma_int \
  -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,\
tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24" \
  -c:v png -pix_fmt rgb24 -start_number 0 "output/%08d.png"
```

HDR with scene detection:

```bash
ffmpeg ... -vf "zscale=t=linear:npl=100,...,format=rgb24,\
select='gt(scene,0.15)',showinfo" \
  -vsync vfr -c:v png ...
```

## Troubleshooting

**`CERTIFICATE_VERIFY_FAILED` on first run (macOS)**
Python.org builds ship without CA certificates, so Flet cannot download its
desktop client. Run the bundled certificate installer once:

```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

**HDR mode stays disabled**
The installed FFmpeg lacks the `zscale` filter. Install a build compiled with
`libzimg` (see [Installing FFmpeg](#installing-ffmpeg)).

**`ffmpeg`/`ffprobe` not found**
Ensure both are installed and on the `PATH`. The application disables extraction
at startup if either is missing.

## Project structure

```
Extract/
├── Extract.py
├── README.md
├── README_FR.md
└── LICENSE
```

## License

This project is open source. See [LICENSE](LICENSE) for details.

## Acknowledgements

- **FFmpeg** — video decoding, filtering, and encoding.
- **Flet** — Python UI framework built on Flutter.
- **libzimg / zscale** — HDR colorspace conversion.
