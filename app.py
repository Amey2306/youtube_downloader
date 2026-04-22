import os
import threading
import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Antigravity YouTube Downloader")
        self.geometry("600x400")
        self.resizable(False, False)

        # Title
        self.title_label = ctk.CTkLabel(self, text="YouTube Video Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # URL Input
        self.url_var = ctk.StringVar()
        self.url_input = ctk.CTkEntry(self, width=450, placeholder_text="Enter YouTube Video URL here...", textvariable=self.url_var)
        self.url_input.pack(pady=10)

        # Download Directory Selection
        self.dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_frame.pack(pady=10)

        self.save_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.dir_label = ctk.CTkLabel(self.dir_frame, text=f"Save to: {self.save_dir}", width=350, anchor="w")
        self.dir_label.pack(side="left", padx=(0, 10))

        self.browse_button = ctk.CTkButton(self.dir_frame, text="Browse", width=80, command=self.browse_directory)
        self.browse_button.pack(side="left")

        # Download Button
        self.download_button = ctk.CTkButton(self, text="Download Video", width=200, font=ctk.CTkFont(size=15, weight="bold"), command=self.start_download)
        self.download_button.pack(pady=20)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=450)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 5))

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)
        
        self.is_downloading = False

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.save_dir)
        if directory:
            self.save_dir = directory
            self.dir_label.configure(text=f"Save to: {self.save_dir}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Handle percentage parsing
                percent_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                # Some versions of yt-dlp might use ANSI escape sequences in this string
                if '\x1b' in percent_str:
                    import re
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', percent_str)
                percent = float(percent_str) / 100.0
                # Ensure percent doesn't exceed 1.0 or go below 0.0
                percent = max(0.0, min(1.0, percent))
                
                # Update UI via after() for thread safety
                self.after(0, self.update_progress, percent, f"Downloading: {percent_str}% - {d.get('_speed_str', '')} ETA: {d.get('_eta_str', '')}")
            except Exception as e:
                pass
        elif d['status'] == 'finished':
            self.after(0, self.update_progress, 1.0, "Download Finished! Processing...")

    def update_progress(self, percent, status_text):
        self.progress_bar.set(percent)
        if "Processing..." in status_text:
            self.status_label.configure(text=status_text, text_color="green")
        else:
            self.status_label.configure(text=status_text)

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL.")
            return

        if self.is_downloading:
            return

        self.is_downloading = True
        self.download_button.configure(state="disabled")
        self.status_label.configure(text="Starting Download...", text_color="white")
        self.progress_bar.set(0)

        # Run yt-dlp in a separate thread so it doesn't freeze the GUI
        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        import shutil
        has_ffmpeg = shutil.which("ffmpeg") is not None
        
        # If ffmpeg is present, download best video and best audio and merge (enables 1080p+)
        # If not, fallback to 'best', which gets highest quality pre-merged file (usually 720p max)
        format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if has_ffmpeg else 'best[ext=mp4]/best'

        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Use after to update GUI safely from another thread
            self.after(0, self.download_complete, True)
        except Exception as e:
            self.after(0, self.download_complete, False, str(e))

    def download_complete(self, success, error_msg=""):
        self.is_downloading = False
        self.download_button.configure(state="normal")
        if success:
            self.status_label.configure(text="Video Downloaded Successfully!", text_color="green")
            messagebox.showinfo("Success", "Video has been downloaded successfully.")
        else:
            self.status_label.configure(text="Download Failed", text_color="red")
            messagebox.showerror("Download Error", f"An error occurred: {error_msg}")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
