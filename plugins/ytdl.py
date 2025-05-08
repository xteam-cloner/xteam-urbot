# Ayra - UserBot
# Copyright (C) 2021-2022 senpai80
#
# This file is a part of < https://github.com/senpai80/Ayra/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/senpai80/Ayra/blob/main/LICENSE/>.
"""
✘ **Bantuan Untuk Youtube**

๏ **Perintah:** video
◉ **Keterangan:** Unduh Video Dari Youtube.

๏ **Perintah:** song
◉ **Keterangan:** Unduh Lagu Dari Youtube.
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


@ultroid_cmd(pattern="Video( (.*)|$)")
async def yt_video(e):
    infomsg = await e.eor("`Processing...`")
    try:
        search = (
            SearchVideos(
                str(e.text.split(None, 1)[1]), offset=1, mode="dict", max_results=1
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
            "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
        }
    )
    await infomsg.eor("Mulai Mendownload...")
    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        file_path = ydl.prepare_filename(ytdl_data)
        videoid = ytdl_data["id"]
        title = ytdl_data["title"]
        url = f"https://youtu.be/{videoid}"
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
        caption=f'<blockquote>💡 Informasi {"video"}\n\n🏷 Nama: {title}\n🧭 Durasi: {duration}\n👀 Dilihat: {views}\n📢 Channel: {channel}\nUpload By: {ultroid_bot.full_name}</blockquote>',
        reply_to=e.reply_to_msg_id,
        parse_mode="html",
    )
    await infomsg.delete()
    for files in (thumbnail, file_path):
        if files and os.path.exists(files):
            os.remove(files)


@ultroid_cmd(pattern="Song( (.*)|$)")
async def yt_audio(e):
    infomsg = await e.eor("`Processing...`")
    try:
        search = (
            SearchVideos(
                str(e.text.split(None, 1)[1]), offset=1, mode="dict", max_results=1
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
            "format": "bestaudio[ext=m4a]",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
        }
    )
    await infomsg.edit("Mulai Mendownload...")
    try:
        ytdl_data = await run_sync(ydl.extract_info, link, download=True)
        file_path = ydl.prepare_filename(ytdl_data)
        videoid = ytdl_data["id"]
        title = ytdl_data["title"]
        url = f"https://youtu.be/{videoid}"
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
        file_name=title,
        duration=duration,
        supports_streaming=False,
        caption=f'<blockquote>💡 Informasi {"Audio"}\n\n🏷 Nama: {title}\n🧭 Durasi: {duration}\n👀 Dilihat: {views}\n**📢 Channel: {channel}\nUpload By: {ultroid_bot.full_name}</blockquote>',
        reply_to=e.reply_to_msg_id,
        parse_mode="html",
    )
    await infomsg.delete()
    for files in (thumbnail, file_path):
        if files and os.path.exists(files):
            os.remove(files)
