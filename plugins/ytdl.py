# xteam-urbot 
# Copyright (C) 2024-2025 xteamdev
#
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
from asyncio import get_event_loop
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
    try:
        raw_query = str(e.text.split(None, 1)[1])
        cleaned_query = raw_query.split('?')[0] 

        search = (
            SearchVideos(
                cleaned_query, offset=1, mode="dict", max_results=1
            )
            .result()
            .get("search_result")
        )
        link = f"https://youtu.be/{search[0]['id']}"
    except Exception as error:
        return await infomsg.edit(f"**Pencarian...\n\n❌ Error: {error}**")
        
    ydl = YoutubeDL(
        {
            "quiet": True,
            "no_warnings": True,
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
            "merge_output_format": "mp4", 
            # Perbaikan Streaming Video
            "postprocessor_args": ['-movflags', 'faststart'], 
        }
    )
    
    await infomsg.eor("Download ...")
    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        file_path = ydl.prepare_filename(ytdl_data)
        videoid = ytdl_data["id"]
        title = ytdl_data["title"]
        duration = ytdl_data["duration"]
        channel = ytdl_data["uploader"]
        views = f"{ytdl_data['view_count']:,}".replace(",", ".")
        thumbs = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    except Exception as error:
        return await infomsg.eor(f"**Gagal...\n\n❌ Error: {error}**")
        
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
    await infomsg.delete()
    for files in (thumbnail, file_path):
        if files and os.path.exists(files):
            os.remove(files)


@ultroid_cmd(pattern="song( (.*)|$)")
async def yt_audio(e):
    infomsg = await e.eor("`Processing...`")
    try:
        raw_query = str(e.text.split(None, 1)[1])
        cleaned_query = raw_query.split('?')[0] 

        search = (
            SearchVideos(
                cleaned_query, offset=1, mode="dict", max_results=1
            )
            .result()
            .get("search_result")
        )
        link = f"https://youtu.be/{search[0]['id']}"
    except Exception as error:
        return await infomsg.eor(f"**Pencarian...\n\n❌ Error: {error}**")

    ydl = YoutubeDL(
        {
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
            # Perbaikan Streaming Audio
            "postprocessor_args": ['-movflags', 'faststart'],
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
        }
    )
    
    await infomsg.edit("Download ...")
    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        file_path = ydl.prepare_filename(ytdl_data)
        
        base_path = os.path.splitext(file_path)[0]
        if not file_path.endswith('.mp3'):
             file_path = base_path + '.mp3'
        
        videoid = ytdl_data["id"]
        title = ytdl_data["title"]
        duration = ytdl_data["duration"]
        channel = ytdl_data["uploader"]
        views = f"{ytdl_data['view_count']:,}".replace(",", ".")
        thumbs = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    except Exception as error:
        return await infomsg.edit(f"**Downloader...\n\n❌ Error: {error}**")
        
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
    await infomsg.delete()
    
    files_to_remove = [thumbnail, file_path, base_path + '.webm', base_path + '.m4a'] 
    for files in files_to_remove:
        if files and os.path.exists(files):
            os.remove(files)
    
