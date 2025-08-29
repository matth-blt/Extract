# Extract

Lightweight GUI application (Python + CustomTkinter) to extract frames (images) from a video, with optional automatic scene change detection (*Dataset mode*).  
Currently supports formats: **PNG**, **JPEG**, and (planned) **TIFF** via `ffmpeg`.

---

## ✨ Features

- Select a video file (supported extensions filtered: `.mkv .mp4 .webm .mov`)
- Choose / create an output directory
- Frame export modes:
  - Standard mode: extract all frames from the video stream (`-map 0:v`)
  - Dataset mode (checkbox): scene change detection (`select='gt(scene,0.15)'`) to export only representative frames
- Supported output formats:
  - PNG (24‑bit RGB)
  - JPEG (high quality `-q:v 1`)
  - TIFF (command incomplete – see Improvements)
- Zero‑padded sequential numbering: `%08d.ext`
- Asynchronous `ffmpeg` execution (thread) so the UI stays responsive

---

## 🖥 Technical Overview

The script builds a base `ffmpeg` command:
```
ffmpeg -hide_banner -i "INPUT" -sws_flags spline+accurate_rnd+full_chroma_int [OPTIONS] ...
```
Then appends either:
- `-vf "select='gt(scene,0.15)',showinfo" -vsync vfr` (Dataset mode)
- or `-map 0:v` (all frames)

---

## 📁 Repository Structure

```
.
└── Extract.py  # Main script (GUI + ffmpeg command construction)
```

---

## 🔧 Prerequisites

1. Python 3.10+ (recommended)
2. ffmpeg installed and available in PATH:
   - Windows: https://www.gyan.dev/ffmpeg/builds/ then add `ffmpeg/bin` to PATH
   - macOS: `brew install ffmpeg`
   - Linux (Debian/Ubuntu): `sudo apt-get install ffmpeg`
3. Python dependencies:
   - `customtkinter` (modern UI)
   - (Optional future: `tqdm` for progress bar, `pytest` for tests)

---

## 📦 Installation

```bash
git clone https://github.com/matth-blt/Extract.git
cd Extract
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install customtkinter
```

Verify `ffmpeg`:
```bash
ffmpeg -version
```

---

## ▶️ Usage

Launch the interface:

```bash
python Extract.py
```

UI steps:
1. Click “Browse...” (Input Path) and choose a video.
2. Click “Browse...” (Output Path) and pick / create a folder.
3. Select export format (PNG / JPEG / TIFF).
4. (Optional) Enable “Dataset Mode (Scene Detection)” to export only scene change frames.
5. Click “Extract”.

Output example:
```
OUTPUT_DIR/
├── 00000000.png (or .jpg / .tiff)
├── 00000001.png
└── ...
```

---

## 🧪 Example Generated `ffmpeg` Command (PNG + scene mode)

```bash
ffmpeg -hide_banner -i "C:\Videos\film.mp4" -sws_flags spline+accurate_rnd+full_chroma_int \
-vf "select='gt(scene,0.15)',showinfo" -vsync vfr \
-color_trc 2 -colorspace 2 -color_primaries 2 \
-c:v png -pix_fmt rgb24 -start_number 0 "C:\Output\%08d.png"
```

---

## ❗ Current Limitations

- No progress bar (thread starts `ffmpeg` without capturing output)
- No disk space validation
- No cancellation (cannot terminate process via UI)
- TIFF block is incomplete / truncated in current code (line 43):
  - Needs completion / correction (e.g. remove `-movflags` if not using a container, or adjust codec)
- No external configuration (scene threshold `0.15` hard‑coded)
- No structured logging or unit tests

---

## 🛠 Potential Improvements

- Add progress parsing (parse `ffmpeg` stderr)
- Make scene threshold configurable (`--scene-threshold`)
- Additional formats: WebP, AVIF, HEIF
- Time range extraction option
- Drag & drop support
- Executable packaging (PyInstaller / Briefcase)
- Internationalization (EN/FR)
- Frame hashing / deduplication

---

## 🧹 Code Quality & Style

Suggested (not implemented):
```bash
pip install ruff mypy
ruff check .
ruff format .
mypy Extract.py
```

---

## 🔐 Security

- No data collection
- Validate paths (avoid overwriting critical data)
- Avoid running on untrusted media without sandboxing

---

## 🧾 License

Specify a license (e.g. MIT). Example:

```
MIT License © 2025 matth-blt
```

---

## 🤝 Contributing

Pull requests welcome:
1. Fork
2. Create a branch: `feat/add-tiff`
3. Conventional commit: `feat: add proper tiff support`
4. Open PR with description (ffmpeg command, tests)

---

## ❓ Quick FAQ

Q: No images exported?  
A: Check output path, permissions, or whether the video has a video stream.

Q: Dataset mode produces very few images?  
A: Threshold `0.15` may be high – make it configurable.

Q: Colors look off?  
A: Inspect/remove color flags (`-color_trc`, etc.) for debugging.

---

## 🗺 Suggested Roadmap

- [ ] Fix / complete TIFF command
- [ ] UI control for scene threshold
- [ ] Show progress + ETA
- [ ] Status bar / log panel
- [ ] Internationalization
- [ ] Cross‑platform executable

---

## 🙏 Acknowledgments

- `ffmpeg` (essential open source project)
- `customtkinter` for modern UI

---

If you want, I can also:
- Propose a correct TIFF command
- Add ffmpeg output parsing for progress
- Prepare a packaging script

Let me know and I’ll adapt. Happy extracting! 🎬
