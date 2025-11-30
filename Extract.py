import customtkinter as ctk
from tkinter import filedialog
import os
import subprocess
import threading
import re
import json


class ExtractApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Extract 3.0.0")
        self.geometry("600x750")
        self.minsize(500, 600)
        
        # Variables
        self.input_path = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.format_var = ctk.StringVar(value='PNG')
        self.dataset_var = ctk.IntVar(value=0)
        self.is_extracting = False
        self.video_duration = 0
        
        # Configuration du grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        self._create_widgets()
    
    def _create_widgets(self):
        # ═══════════════════════════════════════════════════════════════
        # SECTION: Input/Output Files
        # ═══════════════════════════════════════════════════════════════
        files_frame = ctk.CTkFrame(self)
        files_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        files_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(files_frame, text="📁 Files", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=15, pady=(15, 10), sticky="w"
        )
        
        # Input
        ctk.CTkLabel(files_frame, text="Input:").grid(row=1, column=0, padx=(15, 10), pady=5, sticky="w")
        self.input_entry = ctk.CTkEntry(files_frame, textvariable=self.input_path, width=350)
        self.input_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(files_frame, text="Browse...", width=100, command=self.browse_input).grid(
            row=1, column=2, padx=(5, 15), pady=5
        )
        
        # Output
        ctk.CTkLabel(files_frame, text="Output:").grid(row=2, column=0, padx=(15, 10), pady=(5, 15), sticky="w")
        self.output_entry = ctk.CTkEntry(files_frame, textvariable=self.output_dir, width=350)
        self.output_entry.grid(row=2, column=1, padx=5, pady=(5, 15), sticky="ew")
        ctk.CTkButton(files_frame, text="Browse...", width=100, command=self.browse_output).grid(
            row=2, column=2, padx=(5, 15), pady=(5, 15)
        )
        
        # ═══════════════════════════════════════════════════════════════
        # SECTION: Settings
        # ═══════════════════════════════════════════════════════════════
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(settings_frame, text="⚙️ Settings", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w"
        )
        
        # Format
        ctk.CTkLabel(settings_frame, text="Format:").grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")
        format_options = ctk.CTkSegmentedButton(
            settings_frame, 
            values=['PNG', 'TIFF', 'JPEG'],
            variable=self.format_var
        )
        format_options.grid(row=1, column=1, padx=(5, 15), pady=10, sticky="w")
        
        # Dataset mode
        self.dataset_checkbox = ctk.CTkCheckBox(
            settings_frame, 
            text="Dataset Mode (Scene Detection)", 
            variable=self.dataset_var
        )
        self.dataset_checkbox.grid(row=2, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="w")
        
        # ═══════════════════════════════════════════════════════════════
        # SECTION: Progress
        # ═══════════════════════════════════════════════════════════════
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(progress_frame, text="📊 Progress", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w"
        )
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(progress_frame, text="Waiting...", text_color="gray")
        self.status_label.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="w")
        
        # ═══════════════════════════════════════════════════════════════
        # SECTION: Logs / Console
        # ═══════════════════════════════════════════════════════════════
        logs_frame = ctk.CTkFrame(self)
        logs_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(logs_frame, text="📋 Logs", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 10), sticky="w"
        )
        
        self.log_textbox = ctk.CTkTextbox(logs_frame, height=150, state="disabled")
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        
        # ═══════════════════════════════════════════════════════════════
        # SECTION: Action Buttons
        # ═══════════════════════════════════════════════════════════════
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Theme button
        self.theme_button = ctk.CTkButton(
            actions_frame, 
            text="🌙 Dark Mode", 
            width=140,
            fg_color="gray40",
            hover_color="gray30",
            command=self.toggle_theme
        )
        self.theme_button.grid(row=0, column=0, padx=5, pady=10)
        
        # Clear logs button
        ctk.CTkButton(
            actions_frame, 
            text="🗑️ Clear Logs", 
            width=140,
            fg_color="gray40",
            hover_color="gray30",
            command=self.clear_logs
        ).grid(row=0, column=1, padx=5, pady=10)
        
        # Extract button
        self.extract_button = ctk.CTkButton(
            actions_frame, 
            text="🚀 Extract", 
            width=140,
            fg_color="#28a745",
            hover_color="#218838",
            command=self.export
        )
        self.extract_button.grid(row=0, column=2, padx=5, pady=10)
    
    # ═══════════════════════════════════════════════════════════════════════
    # METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def log(self, message: str):
        """Adds a message to the log console."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
    
    def clear_logs(self):
        """Clears all logs."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
    
    def toggle_theme(self):
        """Toggles between light and dark mode."""
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_button.configure(text="🌙 Dark Mode")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_button.configure(text="☀️ Light Mode")
    
    def browse_input(self):
        """Opens a dialog to select the video file."""
        selected_file = filedialog.askopenfilename(
            filetypes=[('Video Files', '*.mkv *.mp4 *.webm *.mov *.avi *.wmv *.flv')]
        )
        if selected_file:
            self.input_path.set(selected_file.replace('/', '\\'))
            self.log(f"📥 File selected: {os.path.basename(selected_file)}")
    
    def browse_output(self):
        """Opens a dialog to select the output folder."""
        output_dir_value = filedialog.askdirectory()
        if output_dir_value:
            if not os.path.exists(output_dir_value):
                os.makedirs(output_dir_value)
            self.output_dir.set(output_dir_value.replace('/', '\\'))
            self.log(f"📤 Output folder: {output_dir_value}")
    
    def get_video_duration(self, input_path: str) -> float:
        """Gets the video duration in seconds via ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        except Exception as e:
            self.log(f"⚠️ Unable to read duration: {e}")
            return 0
    
    def parse_time(self, time_str: str) -> float:
        """Converts a HH:MM:SS.ms timestamp to seconds."""
        try:
            parts = time_str.split(':')
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
    
    def update_progress(self, current_time: float):
        """Updates the progress bar."""
        if self.video_duration > 0:
            progress = min(current_time / self.video_duration, 1.0)
            self.progress_bar.set(progress)
            percent = int(progress * 100)
            self.status_label.configure(text=f"Extracting... {percent}%")
    
    def set_extracting_state(self, extracting: bool):
        """Enables/disables the extraction state."""
        self.is_extracting = extracting
        if extracting:
            self.extract_button.configure(state="disabled", text="⏳ Extracting...")
            self.status_label.configure(text="Starting...", text_color="#FFA500")
        else:
            self.extract_button.configure(state="normal", text="🚀 Extract")
    
    def export(self):
        """Starts the image extraction."""
        if self.is_extracting:
            return
        
        input_path_value = self.input_path.get()
        output_dir_value = self.output_dir.get()

        if not input_path_value or not output_dir_value:
            self.log("❌ Please select an input file and output folder.")
            self.status_label.configure(text="Error: missing paths", text_color="#dc3545")
            return

        if not os.path.isfile(input_path_value):
            self.log("❌ Input file does not exist.")
            self.status_label.configure(text="Error: file not found", text_color="#dc3545")
            return

        output_filename = os.path.normpath(output_dir_value)
        format_choice = self.format_var.get()
        dataset_mode = self.dataset_var.get()

        # Get video duration
        self.log("🔍 Analyzing video...")
        self.video_duration = self.get_video_duration(input_path_value)
        if self.video_duration > 0:
            self.log(f"⏱️ Duration: {self.video_duration:.2f} seconds")
        
        # Build the command
        base_cmd = f'ffmpeg -hide_banner -progress pipe:1 -i "{input_path_value}" -sws_flags spline+accurate_rnd+full_chroma_int'

        if dataset_mode == 1:
            vf_opts = '-vf "select=\'gt(scene,0.15)\',showinfo" -vsync vfr'
            self.log("🎬 Dataset Mode enabled (scene detection)")
        else:
            vf_opts = '-map 0:v'

        if format_choice == 'PNG':
            ffmpeg_command = f'{base_cmd} -color_trc 2 -colorspace 2 -color_primaries 2 {vf_opts} -c:v png -pix_fmt rgb24 -start_number 0 "{output_filename}/%08d.png"'
        elif format_choice == 'TIFF':
            ffmpeg_command = f'{base_cmd} -color_trc 1 -colorspace 1 -color_primaries 1 {vf_opts} -c:v tiff -pix_fmt rgb24 -compression_algo deflate -start_number 0 "{output_filename}/%08d.tiff"'
        elif format_choice == 'JPEG':
            ffmpeg_command = f'{base_cmd} -color_trc 2 -colorspace 2 -color_primaries 2 {vf_opts} -c:v mjpeg -pix_fmt yuvj420p -q:v 1 -start_number 0 "{output_filename}/%08d.jpg"'

        self.log(f"🎯 Format: {format_choice}")
        self.log("🚀 Starting extraction...")
        
        self.set_extracting_state(True)
        self.progress_bar.set(0)

        def run_ffmpeg_command():
            try:
                process = subprocess.Popen(
                    ffmpeg_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                time_pattern = re.compile(r'out_time=(\d{2}:\d{2}:\d{2}\.\d+)')
                frame_pattern = re.compile(r'frame=(\d+)')
                
                for line in process.stdout:
                    line = line.strip()
                    
                    # Extraction du temps pour la progression
                    time_match = time_pattern.search(line)
                    if time_match:
                        current_time = self.parse_time(time_match.group(1))
                        self.after(0, lambda t=current_time: self.update_progress(t))
                    
                    # Log des frames
                    frame_match = frame_pattern.search(line)
                    if frame_match:
                        frame_num = frame_match.group(1)
                        self.after(0, lambda f=frame_num: self.status_label.configure(
                            text=f"Frame {f} extraite..."
                        ))
                
                process.wait()
                
                if process.returncode == 0:
                    self.after(0, lambda: self.on_extraction_complete(True))
                else:
                    self.after(0, lambda: self.on_extraction_complete(False))
                    
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error: {str(e)}"))
                self.after(0, lambda: self.on_extraction_complete(False))

        ffmpeg_thread = threading.Thread(target=run_ffmpeg_command, daemon=True)
        ffmpeg_thread.start()
    
    def on_extraction_complete(self, success: bool):
        """Called when extraction is complete."""
        self.set_extracting_state(False)
        if success:
            self.progress_bar.set(1)
            self.status_label.configure(text="✅ Extraction complete!", text_color="#28a745")
            self.log("✅ Extraction completed successfully!")
        else:
            self.status_label.configure(text="❌ Extraction failed", text_color="#dc3545")
            self.log("❌ Extraction failed.")


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ExtractApp()
    app.mainloop()
