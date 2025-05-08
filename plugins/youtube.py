# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
✘ Commands Available -

• `{i}songs <(youtube) search query>`
   Search and download audio from youtube.

• `{i}songv <(youtube) search query>`
   Search and download video from youtube.
"""

from xteam.fns.ytdl import download_yt, get_yt_link
from yt_dlp import YoutubeDL
from . import get_string, requests, ultroid_cmd
import logging

logging.basicConfig(level=logging.ERROR)


async def download_youtube(event, opt):
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    message = await event.eor(get_string("com_1"))  # Assuming com_1 is a relevant message
    try:
        query = event.text.split(" ", 1)[1]
    except IndexError:
        return await message.edit(
            get_string("youtube_5") if opt in ("s", "ss") else get_string("youtube_7")
        )

    url = get_yt_link(query)
    if not url:
        return await message.edit(get_string("unspl_1"))

    yt_info = get_yt_link(url)
    if yt_info:
        title = yt_info.get("title")
        duration = yt_info.get("duration")
        view_count = yt_info.get("view_count")
        channel_name = yt_info.get("uploader")
        info_text = f"**Judul:** {title}\n"
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            info_text += f"**Durasi:** {minutes}:{seconds:02d}\n"
        if channel_name:
            info_text += f"**Channel:** {channel_name}\n"
        if view_count is not None:
            info_text += f"**Views:** {view_count:,}\n"
        await message.edit(
            f"{get_string('youtube_6' if opt in ('s', 'ss') else 'youtube_8')}\n\n{info_text}"
        )
    else:
        await message.edit(
            get_string("youtube_6") if opt in ("s", "ss") else get_string("youtube_8")
        )

    if opt in ("s", "ss"):
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
    elif opt in ("v", "vv"):
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
    else:
        return

    try:
        await download_yt(message, url, ytd)
    except Exception as e:
         logging.error(f"Error during download: {e}")
         await message.edit(get_string("youtube_6")) # Replace "download_error" with a relevant string

@ultroid_cmd(pattern="song(s|v) ?(.*)")
async def download_song(event):
    await download_youtube(event, event.pattern_match.group(1).strip())

@ultroid_cmd(pattern="song(ss|vv) ?(.*)")
async def download_song_info(event):
    await download_youtube(event, event.pattern_match.group(1).strip())
