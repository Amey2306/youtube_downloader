import os
import threading
import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Antigravity YouTube Agent & Downloader")
        self.geometry("750x600")
        self.resizable(False, False)

        # Title
        self.title_label = ctk.CTkLabel(self, text="YouTube Agent & Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # Shared Download Directory Selection
        self.dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_frame.pack(pady=(0, 10))

        self.save_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.dir_label = ctk.CTkLabel(self.dir_frame, text=f"Save to: {self.save_dir}", width=400, anchor="w")
        self.dir_label.pack(side="left", padx=(0, 10))

        self.browse_button = ctk.CTkButton(self.dir_frame, text="Browse", width=80, command=self.browse_directory)
        self.browse_button.pack(side="left")

        # Tabview for Modes
        self.tabview = ctk.CTkTabview(self, width=700, height=350)
        self.tabview.pack(pady=5)

        self.tab_search = self.tabview.add("Search Agent")
        self.tab_direct = self.tabview.add("Direct Link")

        self.setup_search_tab()
        self.setup_direct_tab()

        # Shared Status & Progress (Moved to bottom)
        self.progress_bar = ctk.CTkProgressBar(self, width=700)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(15, 5))

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)
        
        self.is_downloading = False

    def setup_direct_tab(self):
        # URL Input
        self.url_var = ctk.StringVar()
        self.url_input = ctk.CTkEntry(self.tab_direct, width=500, placeholder_text="Enter exactly one YouTube URL...", textvariable=self.url_var)
        self.url_input.pack(pady=40)

        # Download Button
        self.download_button = ctk.CTkButton(self.tab_direct, text="Download Video", width=200, font=ctk.CTkFont(size=15, weight="bold"), command=self.start_direct_download)
        self.download_button.pack(pady=20)

    def setup_search_tab(self):
        # Search Input
        self.search_frame = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        self.search_frame.pack(pady=10)

        self.search_var = ctk.StringVar()
        self.search_input = ctk.CTkEntry(self.search_frame, width=450, placeholder_text="What do you want to learn/watch? Context goes here...", textvariable=self.search_var)
        self.search_input.pack(side="left", padx=(0, 10))

        self.search_btn = ctk.CTkButton(self.search_frame, text="Ask Agent", width=100, command=self.start_search)
        self.search_btn.pack(side="left")

        # Results Frame
        self.results_frame = ctk.CTkScrollableFrame(self.tab_search, width=650, height=200)
        self.results_frame.pack(pady=10)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.save_dir)
        if directory:
            self.save_dir = directory
            self.dir_label.configure(text=f"Save to: {self.save_dir}")

    # ================== SEARCH LOGIC ==================
    def start_search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter some context or keywords to search.")
            return

        self.search_btn.configure(state="disabled", text="Searching...")
        self.status_label.configure(text="Agent is searching YouTube...", text_color="cyan")
        
        # Clear existing results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        threading.Thread(target=self.execute_search, args=(query,), daemon=True).start()

    def execute_search(self, query):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'nocheckcertificate': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Use ytsearch5: to get top 5 results
                result = ydl.extract_info(f"ytsearch5:{query}", download=False)
                
                if 'entries' in result:
                    # Convert to list to avoid generator exhaustion outside of this thread/context
                    entries = list(result['entries'])
                    self.after(0, self.display_search_results, entries)
                else:
                    self.after(0, self.search_complete_ui, "No results found.")
        except Exception as e:
            self.after(0, self.search_complete_ui, f"Error: {e}")

    def search_complete_ui(self, msg=""):
        self.search_btn.configure(state="normal", text="Ask Agent")
        if msg:
            self.status_label.configure(text=msg, text_color="red")
        else:
            self.status_label.configure(text="Search Complete! Pick a video to download.", text_color="green")

    def display_search_results(self, entries):
        self.search_complete_ui()
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Unknown Title')
            channel = entry.get('uploader', 'Unknown Creator')
            duration = entry.get('duration') # in seconds
            url = entry.get('url', '')

            # Format duration
            if duration:
                try:
                    mins, secs = divmod(int(duration), 60)
                    dur_str = f"[{mins}:{secs:02d}]"
                except (ValueError, TypeError):
                    dur_str = "[Live/Unknown]"
            else:
                dur_str = "[Live/Unknown]"
            
            # Shorten title if too long
            if len(title) > 60:
                title = title[:57] + "..."

            display_text = f"{dur_str} {title} (by {channel})"

            row_frame = ctk.CTkFrame(self.results_frame, fg_color="gray20", corner_radius=5)
            row_frame.pack(fill="x", pady=5, padx=5)

            lbl = ctk.CTkLabel(row_frame, text=display_text, anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=10, pady=5)

            # Creating a lambda function that binds the specific url
            dl_btn = ctk.CTkButton(row_frame, text="Download", width=80, fg_color="#2b8a3e", hover_color="#1e6b2c", 
                                   command=lambda u=url: self.trigger_download(u))
            dl_btn.pack(side="right", padx=10, pady=5)

    # ================== DOWNLOAD LOGIC ==================
    def start_direct_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL.")
            return
        self.trigger_download(url)

    def trigger_download(self, url):
        if self.is_downloading:
            messagebox.showwarning("Busy", "A download is currently in progress.")
            return

        self.is_downloading = True
        self.download_button.configure(state="disabled")
        
        # Disable all download buttons inside the search results frame
        for child in self.results_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(state="disabled")

        self.status_label.configure(text="Starting Download...", text_color="white")
        self.progress_bar.set(0)

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                if '\x1b' in percent_str:
                    import re
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', percent_str)
                percent = float(percent_str) / 100.0
                percent = max(0.0, min(1.0, percent))
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

    def download_video(self, url):
        import shutil
        has_ffmpeg = shutil.which("ffmpeg") is not None
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
            self.after(0, self.download_complete, True)
        except Exception as e:
            self.after(0, self.download_complete, False, str(e))

    def download_complete(self, success, error_msg=""):
        self.is_downloading = False
        self.download_button.configure(state="normal")
        
        # Re-enable all download buttons in the search results
        for child in self.results_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(state="normal")

        if success:
            self.status_label.configure(text="Video Downloaded Successfully!", text_color="green")
            messagebox.showinfo("Success", "Video has been downloaded successfully.")
        else:
            self.status_label.configure(text="Download Failed", text_color="red")
            messagebox.showerror("Download Error", f"An error occurred: {error_msg}")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
