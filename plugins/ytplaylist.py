import subprocess
import os
import asyncio
import re  # Diperlukan untuk regex
from . import ultroid_cmd
from . import *
# Tentukan folder download di root direktori Ultroid
DOWNLOAD_DIR = "ULTROID_YT_DOWNLOADS"

# --- Fungsi Download (Non-Blocking) ---
# Menggunakan regex untuk mengekstrak nama playlist dari output yt-dlp
PLAYLIST_NAME_REGEX = r"\[download\] Downloading playlist: (.+)"

async def run_download_process(playlist_url):
    """Fungsi yang menjalankan yt-dlp di thread terpisah."""
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    # Tambahkan --get-filename untuk mendapatkan nama folder yang DIBUAT yt-dlp
    command = [
        "yt-dlp",
        "--ignore-errors",
        "-x", # Ekstrak audio saja
        "--audio-format", "mp3", # Format output MP3
        "-o", os.path.join(DOWNLOAD_DIR, "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"),
        playlist_url
    ]
    
    try:
        # Jalankan subprocess.run dalam thread terpisah
        process = await asyncio.to_thread(
            subprocess.run, 
            command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Ekstrak nama playlist dari output
        match = re.search(PLAYLIST_NAME_REGEX, process.stdout)
        playlist_name = match.group(1).strip() if match else "Unknown_Playlist"

        return True, playlist_name, process.stdout
        
    except subprocess.CalledProcessError as e:
        return False, None, f"❌ Download Gagal. Kode Keluar: {e.returncode}\nError: {e.stderr}"
    except FileNotFoundError:
        return False, None, "❌ Error: yt-dlp tidak ditemukan. Pastikan sudah terinstal di lingkungan ini."

# --- COMMAND BOT ---

# Mengubah command untuk menangkap argumen (URL) sebagai grup regex
@ultroid_cmd(r"ytpl\s+(.*)$")
async def youtube_playlist_downloader(event):
    # Cek apakah command dipicu dengan argumen
    if event.pattern_match and event.pattern_match.group(1):
        url = event.pattern_match.group(1).strip()
    elif event.reply_to_msg_id:
        # Mengambil URL dari balasan pesan (reply)
        reply_msg = await event.get_reply_message()
        url = reply_msg.text.strip() if reply_msg and reply_msg.text else None
    else:
        await event.edit("⚠️ Harap berikan URL playlist YouTube setelah command, atau balas pesan yang berisi URL.")
        return
    
    # Validasi URL sederhana
    if not url.startswith(("http://", "https://", "www.")):
        await event.edit("❌ Input yang diberikan tampaknya bukan URL yang valid.")
        return

    await event.edit(f"⏳ **Memulai Download Playlist...**\n`{url}`\n\nProses ini mungkin memakan waktu lama tergantung ukuran playlist.")

    # Jalankan proses download
    success, playlist_name, output_message = await run_download_process(url)

    if success:
        final_path = os.path.join(DOWNLOAD_DIR, playlist_name)
        
        await event.edit(f"✅ **Download Playlist Selesai!**\n\n**Nama Playlist:** `{playlist_name}`\n**Jumlah File:** `{len(os.listdir(final_path))}`\n**Disimpan di:** `{final_path}`")
        
        # SINI Anda bisa menambahkan logic untuk mengunggah folder zip ke Telegram
        # await upload_files_to_telegram(event, final_path)
        
    else:
        await event.edit(f"❌ **Download Gagal**\n\nError: {output_message}")

