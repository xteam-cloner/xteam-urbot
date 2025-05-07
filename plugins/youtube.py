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

from . import get_string, requests, ultroid_cmd


@ultroid_cmd(
    pattern="song(s|v) ?(.*)",
)
async def download_from_youtube_(event):
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    opt = event.pattern_match.group(1).strip()
    xx = await event.eor(get_string("com_1"))
    if opt == "s":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
        try:
            query = event.text.split(" ", 1)[1]
        except IndexError:
            return await xx.eor(get_string("youtube_5"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        await xx.eor(get_string("youtube_6"))
    elif opt == "v":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
        try:
            query = event.text.split(" ", 1)[1]
        except IndexError:
            return await xx.eor(get_string("youtube_7"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        await xx.eor(get_string("youtube_8"))
    else:
        return
    await download_yt(xx, url, ytd)

from xteam.fns.ytdl import download_yt, get_yt_link, get_yt_info

from . import get_string, requests, ultroid_cmd


@ultroid_cmd(
    pattern="song(ss|vv) ?(.*)",
)
async def download_from_youtube_(event):
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    opt = event.pattern_match.group(1).strip()
    xx = await event.eor(get_string("com_1"))
    try:
        query = event.text.split(" ", 1)[1]
    except IndexError:
        return await xx.eor(
            get_string("youtube_5") if opt == "s" else get_string("youtube_7")
        )
    url = get_yt_link(query)
    if not url:
        return await xx.edit(get_string("unspl_1"))

    yt_info = get_yt_info(url)
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
        await xx.edit(f"{get_string('youtube_6' if opt == 's' else 'youtube_8')}\n\n{info_text}")
    else:
        await xx.edit(get_string("youtube_6" if opt == "s" else "youtube_8"))

    if opt == "s":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
    elif opt == "v":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
    else:
        return

    await download_yt(xx, url, ytd)
