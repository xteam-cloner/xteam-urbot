import os
from asyncio import get_event_loop
from functools import partial
import asyncio
import shutil 

from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL
from telethon.tl.types import DocumentAttributeVideo
from telethon.errors import MediaEmptyError, WebpageCurlFailedError, InputUserDeactivatedError

from . import ultroid_cmd 

YDL_PARAMS = {
    "quiet": True,
    "no_warnings": True,
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "256", 
            "nopostoverwrites": True,
        }
    ],
    "postprocessor_args": ['-movflags', 'faststart'],
    "nocheckcertificate": True,
    "geo_bypass": True,
    "cookiefile": "cookies.txt",
}

def download_item_sync(url, output_dir, index):
    try:
        item_temp_dir = os.path.join(output_dir, str(index))
        os.makedirs(item_temp_dir, exist_ok=True)
        
        ydl_opts = YDL_PARAMS.copy()
        
        ydl_opts['outtmpl'] = os.path.join(item_temp_dir, '%(title)s.%(ext)s')
        
        ydl_opts['playlist_items'] = [index] 
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if 'entries' in info and info['entries']:
                downloaded_entry = info['entries'][0]
                
                filename = next((os.path.join(root, f) for root, _, files in os.walk(item_temp_dir) for f in files if f.endswith('.m4a')), None)

                if not filename:
                    filename = ydl.prepare_filename(downloaded_entry)
                
                title = downloaded_entry.get('title', os.path.basename(filename))
                duration = downloaded_entry.get('duration', 0)
                width = downloaded_entry.get('width', 0)
                height = downloaded_entry.get('height', 0)
                
                return filename, title, duration, width, height
            
            return 'Gagal mendapatkan info unduhan.', None, None, None, None
            
    except Exception as e:
        if 'item_temp_dir' in locals() and os.path.exists(item_temp_dir):
            shutil.rmtree(item_temp_dir)
        return str(e), None, None, None, None

async def download_item_async(url, output_dir, index):
    loop = get_event_loop()
    return await loop.run_in_executor(
        None, partial(download_item_sync, url, output_dir, index)
    )

@ultroid_cmd(pattern="playlist (.*)", group=1)
async def youtube_playlist_downloader(event):
    if not event.is_outgoing and not event.is_private:
        await event.reply("Hanya berfungsi di chat pribadi atau sebagai perintah outgoing.")
        return
        
    url = event.pattern_match.group(1).strip()
    
    if not url.startswith("http") or "list=" not in url:
        return await event.reply("❌ **URL Playlist Tidak Valid!** Harap berikan URL YouTube Playlist yang lengkap.")

    temp_dir = f"downloads/playlist_{event.id}/"
    status_msg = await event.reply("⏳ **Mendapatkan info playlist...**")

    try:
        await status_msg.edit("⏳ **Memproses daftar video...**")
        ydl_info_opts = {'quiet': True, 'extract_flat': True, 'force_generic_extractor': True, 'noplaylist': False}
        with YoutubeDL(ydl_info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if 'entries' not in info or not info['entries']:
            return await status_msg.edit("❌ **Playlist kosong atau tidak ditemukan!**")
            
        videos = info['entries']
        
        MAX_VIDEOS = 5 
        if len(videos) > MAX_VIDEOS:
            await status_msg.edit(f"⚠️ Playlist memiliki {len(videos)} video. **Hanya {MAX_VIDEOS} video pertama** yang akan diproses untuk menghindari *timeout*.")
            videos = videos[:MAX_VIDEOS]

        total_videos = len(videos)
        playlist_title = info.get('title', 'Playlist Tanpa Nama')
        downloaded_count = 0
        
        await status_msg.edit(f"▶️ **Memulai Download Playlist:** `{playlist_title}` ({total_videos} item)")

    except Exception as e:
        return await status_msg.edit(f"❌ Error saat mendapatkan info playlist: `{str(e)}`")

    for i, video in enumerate(videos):
        index = i + 1 
        current_title = video.get('title', f"Video ke-{index}")
        
        await status_msg.edit(f"📥 **[{index}/{total_videos}] Mengunduh M4A 256kbps:** `{current_title}`")
        filename, title, duration, width, height = await download_item_async(url, temp_dir, index)
        
        if not filename or not os.path.exists(filename) or filename.startswith('Error'):
            await event.reply(f"❌ **[{index}/{total_videos}] Gagal:** `{title if title else current_title}`. Error: `{filename}`")
            continue
            
        await status_msg.edit(f"⬆️ **[{index}/{total_videos}] Mengunggah:** `{title}`")
        
        try:
            await event.client.send_file(
                event.chat_id,
                filename,
                caption=f"🎧 **{playlist_title}** (M4A 256kbps)\n*Item {index}/{total_videos}:* `{title}`",
                supports_streaming=True,
            )
            downloaded_count += 1
            
        except Exception as e:
            await event.reply(f"❌ **[{index}/{total_videos}] Gagal Unggah:** `{title}`. Error: `{str(e)}`")
        
        try:
            os.remove(filename)
            item_temp_dir = os.path.dirname(filename)
            shutil.rmtree(item_temp_dir)
        except Exception:
            pass 
            
        await asyncio.sleep(2)

    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception:
        pass 

    await status_msg.edit(f"✅ **Selesai!** Playlist `{playlist_title}` selesai diunduh dan diunggah dalam format **M4A 256kbps**.\nTotal {downloaded_count} dari {total_videos} item berhasil.")
