import os
import ssl
import shlex
import shutil
import subprocess
import threading
import re
import json
import flet as ft

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    if not os.environ.get("SSL_CERT_FILE"):
        ssl._create_default_https_context = ssl._create_unverified_context

APP_VERSION = "4.0.0"
APP_TITLE = f"Extract {APP_VERSION}"

HDR_TRANSFERS = {
    "smpte2084": "HDR10 (PQ)",
    "arib-std-b67": "HLG",
}

TONEMAP_OPTIONS = ["hable", "mobius", "reinhard", "clip"]

SCENE_THRESHOLD_DEFAULT = 0.15
NPL_DEFAULT = 100

_NO_WINDOW = (
    {"creationflags": subprocess.CREATE_NO_WINDOW}
    if hasattr(subprocess, "CREATE_NO_WINDOW") else {}
)

def get_video_info(input_path: str) -> dict:
    """Probe a video with ffprobe and return its duration and HDR status.

    Returns a dict with ``duration`` (seconds), ``is_hdr`` (bool) and
    ``hdr_type`` (label). On any failure, falls back to SDR / zero duration.
    """

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", "-select_streams", "v:0",
        input_path
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=30, **_NO_WINDOW
        )
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})

        duration = float(fmt.get("duration", 0))
        color_transfer = stream.get("color_transfer", "")

        return {
            "duration": duration,
            "is_hdr": color_transfer in HDR_TRANSFERS,
            "hdr_type": HDR_TRANSFERS.get(color_transfer, "SDR"),
        }
    except Exception:
        return {"duration": 0, "is_hdr": False, "hdr_type": "SDR"}


def check_zscale_available() -> bool:
    """Checks whether zscale (libzimg) is available in the current FFmpeg build."""

    try:
        result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True,
            timeout=15, **_NO_WINDOW
        )
        return "zscale" in result.stdout
    except Exception:
        return False


def build_vf_filter(
    hdr_mode: bool, hdr_active: bool, dataset_mode: bool,
    tonemap: str, npl: int, scene_threshold: float,
    output_format: str
) -> str:
    """
    Builds the -vf filter string based on selected options.
    Returns an empty string when no video filter is needed.
    """

    parts = []
    if hdr_mode and hdr_active:
        final_fmt = "rgb24" if output_format in ("PNG", "TIFF") else "yuv420p"
        parts += [
            f"zscale=t=linear:npl={npl}",
            "format=gbrpf32le",
            "zscale=p=bt709",
            f"tonemap=tonemap={tonemap}:desat=0",
            "zscale=t=bt709:m=bt709:r=tv",
            f"format={final_fmt}",
        ]

    if dataset_mode:
        parts.append(f"select='gt(scene,{scene_threshold})'")
        parts.append("showinfo")

    return ",".join(parts)


def build_ffmpeg_cmd(
    input_path: str, output_dir: str, output_format: str,
    hdr_mode: bool, hdr_active: bool, dataset_mode: bool,
    tonemap: str, npl: int, scene_threshold: float
) -> list[str]:
    """Assembles the FFmpeg command as an argv list (safe for shell=False)."""

    safe_out = os.path.normpath(output_dir)
    
    cmd = [
        "ffmpeg", "-hide_banner", "-progress", "pipe:1",
        "-i", input_path,
        "-sws_flags", "spline+accurate_rnd+full_chroma_int",
    ]

    vf = build_vf_filter(
        hdr_mode, hdr_active, dataset_mode,
        tonemap, npl, scene_threshold, output_format
    )
    if vf:
        cmd += ["-vf", vf]
    else:
        cmd += ["-map", "0:v"]

    if dataset_mode:
        cmd += ["-vsync", "vfr"]

    if output_format == "PNG":
        cmd += ["-color_trc", "2", "-colorspace", "2", "-color_primaries", "2",
                "-c:v", "png", "-pix_fmt", "rgb24"]
        ext = "png"
    elif output_format == "TIFF":
        cmd += ["-color_trc", "1", "-colorspace", "1", "-color_primaries", "1",
                "-c:v", "tiff", "-pix_fmt", "rgb24", "-compression_algo", "deflate"]
        ext = "tiff"
    else:  # JPEG
        cmd += ["-color_trc", "2", "-colorspace", "2", "-color_primaries", "2",
                "-c:v", "mjpeg", "-pix_fmt", "yuvj420p", "-q:v", "1"]
        ext = "jpg"

    cmd += ["-start_number", "0", os.path.join(safe_out, f"%08d.{ext}")]
    return cmd


def parse_time(time_str: str) -> float:
    """Converts HH:MM:SS.ms to seconds."""
    
    try:
        h, m, s = time_str.split(":")
        return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        return 0.0


def main(page: ft.Page):
    """Build the Flet UI and wire up the extraction workflow."""

    page.title = APP_TITLE
    page.window.width = 680
    page.window.height = 820
    page.window.min_width = 520
    page.window.min_height = 640
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="#6200EE")
    page.dark_theme = ft.Theme(color_scheme_seed="#BB86FC")
    page.padding = 0

    state = {
        "input_path": "",
        "output_dir": "",
        "video_duration": 0.0,
        "is_hdr": False,
        "hdr_type": "SDR",
        "is_extracting": False,
        "zscale_ok": False,
    }

    def toggle_theme(_):
        """Switch between dark and light theme and flip the toggle icon."""

        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon_btn.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon_btn.icon = ft.Icons.LIGHT_MODE
        page.update()

    theme_icon_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        tooltip="Toggle theme",
        on_click=toggle_theme,
    )

    header = ft.Container(
        content=ft.Row(
            [
                ft.Row([
                    ft.Icon(ft.Icons.MOVIE_FILTER_ROUNDED, size=28, color="#BB86FC"),
                    ft.Text(APP_TITLE, size=20, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                theme_icon_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
    )

    hdr_badge = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.HIGH_QUALITY_ROUNDED, size=14, color="#121212"),
            ft.Text("", size=12, weight=ft.FontWeight.BOLD, color="#121212"),
        ], spacing=4, tight=True),
        bgcolor="#FFD700",
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        visible=False,
    )

    def update_hdr_badge(info: dict):
        """Show the HDR badge with the detected transfer label, or hide it."""

        if info["is_hdr"]:
            hdr_badge.content.controls[1].value = info["hdr_type"]
            hdr_badge.visible = True
        else:
            hdr_badge.visible = False
        hdr_badge.update()

    input_field = ft.TextField(
        label="Input video",
        read_only=True,
        expand=True,
        border_radius=10,
        hint_text="No file selected",
        prefix_icon=ft.Icons.VIDEO_FILE_ROUNDED,
    )
    output_field = ft.TextField(
        label="Output folder",
        read_only=True,
        expand=True,
        border_radius=10,
        hint_text="No folder selected",
        prefix_icon=ft.Icons.FOLDER_ROUNDED,
    )

    def handle_input(path: str):
        """Store the chosen input file and probe it for duration/HDR off-thread."""

        if not path:
            return
        
        state["input_path"] = path
        input_field.value = path
        input_field.update()
        log(f"File selected: {os.path.basename(path)}")

        def probe():
            info = get_video_info(path)
            state["video_duration"] = info["duration"]
            state["is_hdr"] = info["is_hdr"]
            state["hdr_type"] = info["hdr_type"]

            if info["duration"] > 0:
                log(f"Duration: {info['duration']:.2f}s")
            if info["is_hdr"]:
                log(f"{info['hdr_type']} detected — HDR Mode recommended")
                hdr_checkbox.value = True
                hdr_checkbox.update()
            else:
                log("SDR video — standard extraction")

            update_hdr_badge(info)
        threading.Thread(target=probe, daemon=True).start()

    def handle_output(path: str):
        """Store the chosen output directory."""

        if not path:
            return
        
        state["output_dir"] = path
        output_field.value = path
        output_field.update()
        log(f"Output folder: {path}")

    input_picker = ft.FilePicker()
    output_picker = ft.FilePicker()
    page.services.extend([input_picker, output_picker])

    async def pick_input(e):
        """Open the native file dialog and load the selected video."""

        files = await input_picker.pick_files(
            dialog_title="Select video file",
            allow_multiple=False,
            allowed_extensions=["mkv", "mp4", "webm", "mov", "avi", "wmv", "flv"],
        )

        if files:
            handle_input(files[0].path)

    async def pick_output(e):
        """Open the native directory dialog and store the output folder."""

        path = await output_picker.get_directory_path(
            dialog_title="Select output folder"
        )
        handle_output(path)

    files_section = _card(
        title="Files",
        content=ft.Column([
            ft.Row([
                input_field,
                ft.IconButton(
                    icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                    tooltip="Browse input",
                    on_click=pick_input,
                ),
            ], spacing=8),
            ft.Row([
                output_field,
                ft.IconButton(
                    icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                    tooltip="Browse output",
                    on_click=pick_output,
                ),
            ], spacing=8),
            ft.Row([hdr_badge], alignment=ft.MainAxisAlignment.START),
        ], spacing=12),
    )

    format_seg = ft.SegmentedButton(
        selected=["PNG"],
        segments=[
            ft.Segment(value="PNG",  label=ft.Text("PNG")),
            ft.Segment(value="TIFF", label=ft.Text("TIFF")),
            ft.Segment(value="JPEG", label=ft.Text("JPEG")),
        ],
        allow_multiple_selection=False,
        allow_empty_selection=False,
    )

    dataset_checkbox = ft.Checkbox(
        label="Dataset Mode (scene detection)",
        value=False,
    )
    scene_slider = ft.Slider(
        min=0.05, max=0.40, value=SCENE_THRESHOLD_DEFAULT,
        divisions=35, label="{value:.2f}",
        expand=True,
        visible=False,
    )
    scene_row = ft.Row([
        ft.Text("Scene threshold:", size=13),
        scene_slider,
    ], visible=False, spacing=8)

    def on_dataset_change(e):
        """Toggle the scene-threshold slider with the Dataset Mode checkbox."""

        scene_row.visible = dataset_checkbox.value
        scene_row.update()

    dataset_checkbox.on_change = on_dataset_change

    hdr_checkbox = ft.Checkbox(
        label="HDR Mode (tonemapping HDR→SDR)",
        value=False,
    )
    tonemap_dropdown = ft.Dropdown(
        label="Tonemap operator",
        value="hable",
        options=[ft.dropdown.Option(t) for t in TONEMAP_OPTIONS],
        width=180,
        border_radius=10,
        visible=False,
    )
    npl_field = ft.TextField(
        label="Peak luminance (npl)",
        value=str(NPL_DEFAULT),
        width=160,
        border_radius=10,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False,
    )
    hdr_options_row = ft.Row(
        [tonemap_dropdown, npl_field],
        spacing=12,
        visible=False,
    )

    zscale_warning = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="#FFA726", size=16),
            ft.Text(
                "zscale not found in your FFmpeg build — HDR mode disabled",
                size=12, color="#FFA726",
            ),
        ], spacing=6),
        visible=False,
    )

    def on_hdr_change(e):
        """Reveal HDR tonemap options, warning if zscale is unavailable."""

        enabled = hdr_checkbox.value
        hdr_options_row.visible = enabled
        tonemap_dropdown.visible = enabled
        npl_field.visible = enabled
        zscale_warning.visible = enabled and not state["zscale_ok"]
        hdr_options_row.update()
        zscale_warning.update()

    hdr_checkbox.on_change = on_hdr_change

    settings_section = _card(
        title="Settings",
        content=ft.Column([
            ft.Row([ft.Text("Format:", size=14), format_seg], spacing=16),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            dataset_checkbox,
            scene_row,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            hdr_checkbox,
            hdr_options_row,
            zscale_warning,
        ], spacing=10),
    )

    progress_bar = ft.ProgressBar(value=0, expand=True, border_radius=8, height=10)
    progress_pct = ft.Text("0%", size=13, weight=ft.FontWeight.W_600)
    status_text = ft.Text("Waiting...", size=13, color="#888888")

    progress_section = _card(
        title="Progress",
        content=ft.Column([
            ft.Row([progress_bar, progress_pct], spacing=12),
            status_text,
        ], spacing=8),
    )

    log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    logs_section = ft.Container(
        content=ft.Column([
            ft.Text("Logs", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=log_list,
                expand=True,
                border=ft.Border.all(1, "#33ffffff"),
                border_radius=10,
                padding=10,
                bgcolor="#0affffff",
            ),
        ], spacing=12, expand=True),
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        expand=True,
    )

    def log(message: str):
        """Append a line to the log view, capping history at 500 entries."""

        log_list.controls.append(
            ft.Text(message, size=12, selectable=True,
                    font_family="Courier New")
        )
        if len(log_list.controls) > 500:
            log_list.controls.pop(0)
        try:
            log_list.update()
        except Exception:
            pass

    def clear_logs(_):
        """Empty the log view."""

        log_list.controls.clear()
        log_list.update()

    extract_btn = ft.FilledButton(
        "Extract",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        bgcolor="#6200EE",
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: start_extraction(),
    )

    actions_row = ft.Container(
        content=ft.Row([
            ft.OutlinedButton(
                " Clear Logs",
                icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=clear_logs,
            ),
            extract_btn,
        ], alignment=ft.MainAxisAlignment.END, spacing=12),
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
    )

    def set_extracting(extracting: bool):
        """Toggle the busy state: disable the button and update its label."""

        state["is_extracting"] = extracting

        if extracting:
            extract_btn.disabled = True
            extract_btn.content = "Extracting..."
            status_text.value = "Starting..."
            status_text.color = "#FFA726"
        else:
            extract_btn.disabled = False
            extract_btn.content = "Extract"
            status_text.color = ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)

        extract_btn.update()
        status_text.update()

    def update_progress(current_time: float):
        """Update the progress bar from the current ffmpeg timestamp."""

        dur = state["video_duration"]

        if dur > 0:
            pct = min(current_time / dur, 1.0)
            progress_bar.value = pct
            progress_pct.value = f"{int(pct * 100)}%"
            progress_bar.update()
            progress_pct.update()

    def start_extraction():
        """Validate inputs, build the ffmpeg command and run it off-thread."""

        if state["is_extracting"]:
            return

        inp = state["input_path"]
        out = state["output_dir"]

        if not inp or not out:
            log("Please select an input file and output folder.")
            return
        if not os.path.isfile(inp):
            log("Input file does not exist.")
            return

        fmt = list(format_seg.selected)[0]
        dataset = dataset_checkbox.value
        hdr = hdr_checkbox.value and state["zscale_ok"]
        hdr_active = state["is_hdr"]
        tonemap = tonemap_dropdown.value

        try:
            npl = int(npl_field.value)
        except (ValueError, TypeError):
            npl = NPL_DEFAULT
        try:
            threshold = float(f"{scene_slider.value:.2f}")
        except Exception:
            threshold = SCENE_THRESHOLD_DEFAULT

        cmd = build_ffmpeg_cmd(
            inp, out, fmt, hdr, hdr_active, dataset,
            tonemap, npl, threshold
        )

        log(f"Format: {fmt} | HDR: {'ON (' + tonemap + ')' if hdr and hdr_active else 'OFF'} | Dataset: {'ON' if dataset else 'OFF'}")
        log("Starting extraction...")
        log(f"CMD: {shlex.join(cmd)}")

        set_extracting(True)
        progress_bar.value = 0
        progress_pct.value = "0%"
        progress_bar.update()
        progress_pct.update()

        def run():
            """Stream ffmpeg output, throttling progress updates to the UI."""

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                    **_NO_WINDOW,
                )

                time_pattern = re.compile(r"out_time=(\d{2}:\d{2}:\d{2}\.\d+)")
                frame_pattern = re.compile(r"frame=\s*(\d+)")
                dur = state["video_duration"]
                last_pct = -1
                last_frame = 0

                for line in process.stdout:
                    line = line.strip()
                    tm = time_pattern.search(line)
                    if tm:
                        t = parse_time(tm.group(1))
                        pct = int(min(t / dur, 1.0) * 100) if dur > 0 else 0
                        if pct != last_pct:
                            last_pct = pct
                            page.run_task(async_update_progress, t)
                    fm = frame_pattern.search(line)
                    if fm:
                        frame_n = int(fm.group(1))
                        # Throttle: refresh status at most every 24 frames
                        if frame_n - last_frame >= 24:
                            last_frame = frame_n
                            page.run_task(async_set_status, f"Frame {frame_n} extracted...")

                process.wait()
                success = process.returncode == 0
                page.run_task(async_finish, success)

            except Exception as e:
                log(f"❌ Error: {e}")
                page.run_task(async_finish, False)

        threading.Thread(target=run, daemon=True).start()

    async def async_update_progress(t: float):
        """UI-thread bridge to refresh the progress bar."""

        update_progress(t)
        page.update()

    async def async_set_status(text: str):
        """UI-thread bridge to update the status line."""

        status_text.value = text
        status_text.update()

    async def async_finish(success: bool):
        """UI-thread bridge to finalise the run with a snackbar and status."""

        set_extracting(False)

        if success:
            progress_bar.value = 1
            progress_pct.value = "100%"
            progress_bar.update()
            progress_pct.update()
            status_text.value = "Extraction complete!"
            status_text.color = "#4CAF50"
            status_text.update()
            log("Extraction completed successfully!")
            page.show_dialog(ft.SnackBar(
                ft.Text("Extraction complete!"), bgcolor="#4CAF50"
            ))
        else:
            status_text.value = "Extraction failed"
            status_text.color = "#F44336"
            status_text.update()
            log("Extraction failed.")
            page.show_dialog(ft.SnackBar(
                ft.Text("Extraction failed — check logs"), bgcolor="#F44336"
            ))

        page.update()

    page.add(
        ft.Column([
            header,
            ft.Container(
                content=ft.Column([
                    files_section,
                    settings_section,
                    progress_section,
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
                expand=False,
            ),
            logs_section,
            actions_row,
        ], expand=True, spacing=0),
    )

    def startup_checks():
        """Verify ffmpeg/ffprobe are installed and detect zscale support."""

        missing = [b for b in ("ffmpeg", "ffprobe") if shutil.which(b) is None]

        if missing:
            log(f"⚠ {', '.join(missing)} not found in PATH — install FFmpeg first.")
            log("→ macOS: brew install ffmpeg  |  Windows: gyan.dev build")
            extract_btn.disabled = True
            extract_btn.update()
            return

        ok = check_zscale_available()
        state["zscale_ok"] = ok

        if ok:
            log("zscale (libzimg) is available — HDR mode ready")
        else:
            log("zscale not found in FFmpeg — HDR mode disabled")
            log("→ Install a full FFmpeg build (macOS: evermeet.cx | Windows: gyan.dev)")
            zscale_warning.visible = hdr_checkbox.value
            zscale_warning.update()

    threading.Thread(target=startup_checks, daemon=True).start()


def _card(title: str, content: ft.Control) -> ft.Container:
    """Returns a Material-style card container."""

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
            content,
        ], spacing=14),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        margin=ft.Margin.symmetric(horizontal=20, vertical=6),
        border_radius=16,
        border=ft.Border.all(1, "#1fffffff"),
        bgcolor="#0affffff",
    )

if __name__ == "__main__":
    ft.run(main)
