# xteam-urbot 
# Copyright (C) 2024-2025 xteamdev
# This file is a part of < https://github.com/senpai80/Ayra/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/senpai80/Ayra/blob/main/LICENSE/>.

"""
✘ Help for YouTube

๏ Command: video
◉ Description: Download Videos from YouTube.

๏ Command: song
◉ Description: Download Songs from YouTube.
"""

import os
from asyncio import get_event_loop, sleep
from functools import partial

import wget
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL

from . import *


def run_sync(func, *args, **kwargs):
    return get_event_loop().run_in_executor(None, partial(func, *args, **kwargs))


@ultroid_cmd(pattern="video( (.*)|$)")
async def yt_video(e):
    infomsg = await e.eor("`Processing...`")
    
    raw_query = str(e.text.split(None, 1)[1])
    cleaned_query = raw_query.split('?')[0].strip()
    
    is_playlist_url = 'list=' in raw_query or 'playlist?' in raw_query
    is_youtube_url = 'youtu.be/' in raw_query or 'youtube.com/' in raw_query

    link = cleaned_query
    
    if not is_youtube_url and not is_playlist_url:
        try:
            search = (
                SearchVideos(cleaned_query, offset=1, mode="dict", max_results=1)
                .result()
                .get("search_result")
            )
            link = f"https://youtu.be/{search[0]['id']}"
        except Exception as error:
            return await infomsg.edit(f"**Pencarian...\n\n❌ Error: {error}**")
        
    ydl_params = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "outtmpl": "downloads/%(id)s_%(playlist_index)s.%(ext)s", 
        "nocheckcertificate": True,
        "geo_bypass": True,
        "cookiefile": "cookies.txt",
        "merge_output_format": "mp4", 
        "postprocessor_args": ['-movflags', 'faststart'], 
    }
    
    if is_playlist_url:
        ydl_params["playlist_items"] = '50'

    ydl = YoutubeDL(ydl_params)
    
    await infomsg.eor("Download ...")
    files_to_remove_after_upload = []

    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        
        entries = ytdl_data.get('entries', [ytdl_data]) 

        if ytdl_data.get('_type') == 'playlist':
            await infomsg.edit(f"`Playlist terdeteksi. Mengunggah {len(entries)} video...`")

        for entry in entries:
            if not entry: continue
            
            file_path = ydl.prepare_filename(entry) 
            
            if ydl_params.get('merge_output_format') == 'mp4':
                 if not file_path.endswith('.mp4'):
                     file_path = os.path.splitext(file_path)[0] + '.mp4'

            if not os.path.exists(file_path):
                 await e.respond(f"❌ Gagal menemukan file: {entry.get('title')}. Mungkin diblokir.")
                 continue

            videoid = entry.get("id")
            title = entry.get("title")
            duration = entry.get("duration")
            channel = entry.get("uploader")
            views = f"{entry.get('view_count', 0):,}".replace(",", ".")
            thumbs = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
            
            thumbnail = wget.download(thumbs)
            
            await e.client.send_file(
                e.chat.id,
                file=file_path,
                thumb=thumbnail,
                file_name=title,
                duration=duration,
                supports_streaming=True,
                caption=f'<blockquote>💡 Informasi {"video"}\n\n🏷 Nama: {title}\n🧭 Durasi: {duration}\n👀 Dilihat: {views}\n📢 Channel: {channel}\n🧑‍⚕️ Upload by: {ultroid_bot.full_name}</blockquote>',
                reply_to=e.reply_to_msg_id,
                parse_mode="html",
            )
            files_to_remove_after_upload.extend([thumbnail, file_path])
            
            await sleep(3) 
            
        
    except Exception as error:
        return await infomsg.eor(f"**Gagal...\n\n❌ Error: {error}**")
    
    await infomsg.delete()
    
    for files in files_to_remove_after_upload:
        if files and os.path.exists(files):
            os.remove(files)


@ultroid_cmd(pattern="song( (.*)|$)")
async def yt_audio(e):
    infomsg = await e.eor("`Processing...`")
    
    raw_query = str(e.text.split(None, 1)[1])
    cleaned_query = raw_query.split('?')[0].strip()
    
    is_playlist_url = 'list=' in raw_query or 'playlist?' in raw_query
    is_youtube_url = 'youtu.be/' in raw_query or 'youtube.com/' in raw_query

    link = cleaned_query
    
    if not is_youtube_url and not is_playlist_url:
        try:
            search = (
                SearchVideos(cleaned_query, offset=1, mode="dict", max_results=1)
                .result()
                .get("search_result")
            )
            link = f"https://youtu.be/{search[0]['id']}"
        except Exception as error:
            return await infomsg.eor(f"**Pencarian...\n\n❌ Error: {error}**")

    ydl_params = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
                "nopostoverwrites": True,
            }
        ],
        "postprocessor_args": ['-movflags', 'faststart'],
        "outtmpl": "downloads/%(id)s_%(playlist_index)s.%(ext)s",
        "nocheckcertificate": True,
        "geo_bypass": True,
        "cookiefile": "cookies.txt",
    }
    
    if is_playlist_url:
        ydl_params["playlist_items"] = '50'
        
    ydl = YoutubeDL(ydl_params)
    
    await infomsg.edit("Download ...")
    files_to_remove_after_upload = []

    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        
        entries = ytdl_data.get('entries', [ytdl_data])
        
        if ytdl_data.get('_type') == 'playlist':
            await infomsg.edit(f"`Playlist terdeteksi. Mengunggah {len(entries)} lagu...`")

        for entry in entries:
            if not entry: continue

            file_path = ydl.prepare_filename(entry) 
            base_path = os.path.splitext(file_path)[0]
            
            if not file_path.endswith('.mp3'):
                 file_path = base_path + '.mp3'
            
            if not os.path.exists(file_path):
                 await e.respond(f"❌ Gagal menemukan file: {entry.get('title')}. Mungkin diblokir.")
                 continue

            videoid = entry.get("id")
            title = entry.get("title")
            duration = entry.get("duration")
            channel = entry.get("uploader")
            views = f"{entry.get('view_count', 0):,}".replace(",", ".")
            thumbs = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

            thumbnail = wget.download(thumbs)
            
            await e.client.send_file(
                e.chat.id,
                file=file_path,
                thumb=thumbnail,
                file_name=f"{title}.mp3",
                duration=duration,
                supports_streaming=True,
                caption=f'<blockquote>💡 Informasi {"Audio"}\n\n🏷 Nama: {title}\n🧭 Durasi: {duration}\n👀 Dilihat: {views}\n📢 Channel: {channel}\n🧑‍⚕️ Upload by: {ultroid_bot.full_name}</blockquote>',
                reply_to=e.reply_to_msg_id,
                parse_mode="html",
            )
            files_to_remove_after_upload.extend([thumbnail, file_path, base_path + '.webm', base_path + '.m4a'])
            
            await sleep(3) 

        
    except Exception as error:
        return await infomsg.edit(f"**Downloader...\n\n❌ Error: {error}**")
    
    await infomsg.delete()

    for files in files_to_remove_after_upload:
        if files and os.path.exists(files):
            os.remove(files)
            
