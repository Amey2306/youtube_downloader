import yt_dlp
import json

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'nocheckcertificate': True
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info("ytsearch5:Ai learning videos", download=False)
        entries = list(result.get('entries', []))
        print("Number of entries:", len(entries))
        if len(entries) > 0:
            print("Keys in first entry:", entries[0].keys())
        else:
            print("Entries is empty!")
            print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
