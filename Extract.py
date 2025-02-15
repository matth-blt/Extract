import customtkinter as ctk
from tkinter import filedialog
import os
import subprocess
import threading

def browse_input():
    selected_file = filedialog.askopenfilename(filetypes=[('Video Files', '*.mkv *.mp4 *.webm *.mov')])
    if selected_file:
        input_path.set(selected_file.replace('/', '\\'))

def browse_output():
    output_dir_value = filedialog.askdirectory()
    if not os.path.exists(output_dir_value):
        os.makedirs(output_dir_value)
    output_dir.set(output_dir_value)

def export():
    input_path_value = input_path.get()
    output_dir_value = output_dir.get()

    if not input_path_value or not output_dir_value:
        print("Please select an input and output path.")
        return

    output_filename = os.path.join(output_dir_value)
    output_filename = os.path.normpath(output_filename)

    format = format_var.get()

    if format == 'PNG':
        ffmpeg_command = f'ffmpeg -hide_banner -i "{input_path_value}" -sws_flags spline+accurate_rnd+full_chroma_int -color_trc 2 -colorspace 2 -color_primaries 2 -map 0:v -c:v png -pix_fmt rgb24 -start_number 0 "{output_filename}/%08d.png"'
    elif format == 'TIFF':
        ffmpeg_command = f'ffmpeg -hide_banner -i "{input_path_value}" -sws_flags spline+accurate_rnd+full_chroma_int -color_trc 1 -colorspace 1 -color_primaries 1 -map 0:v -c:v tiff -pix_fmt rgb24 -compression_algo deflate -start_number 0 -movflags frag_keyframe+empty_moov+delay_moov+use_metadata_tags+write_colr -bf 0 "{output_filename}/%08d.tiff"'
    elif format == 'JPEG':
        ffmpeg_command = f'ffmpeg -hide_banner -i "{input_path_value}" -sws_flags spline+accurate_rnd+full_chroma_int -color_trc 2 -colorspace 2 -color_primaries 2 -map 0:v -c:v mjpeg -pix_fmt yuvj420p -q:v 1 -start_number 0 "{output_filename}/%08d.jpg"'

    def run_ffmpeg_command():
        subprocess.run(ffmpeg_command, shell=True)

    ffmpeg_thread = threading.Thread(target=run_ffmpeg_command)
    ffmpeg_thread.start()

app = ctk.CTk()
app.title("Extract 2.0.0")
app.geometry("500x432")

input_path = ctk.StringVar()
output_dir = ctk.StringVar()

ctk.CTkLabel(app, text="Input Path:").pack(pady=10)
input_path_entry = ctk.CTkEntry(app, textvariable=input_path, width=400, state="disabled")
input_path_entry.pack(pady=5)
ctk.CTkButton(app, text="Browse...", command=browse_input).pack(pady=5)

ctk.CTkLabel(app, text="Output Path:").pack(pady=10)
output_dir_entry = ctk.CTkEntry(app, textvariable=output_dir, width=400, state="disabled")
output_dir_entry.pack(pady=5)
ctk.CTkButton(app, text="Browse...", command=browse_output).pack(pady=5)

format_var = ctk.StringVar(value='PNG')

ctk.CTkLabel(app, text="Format:").pack(pady=10)
format_combobox = ctk.CTkOptionMenu(app, variable=format_var, values=['PNG', 'TIFF', 'JPEG'])
format_combobox.pack(pady=5)

ctk.CTkButton(app, text="Extract", command=export).pack(pady=20)

app.mainloop()
