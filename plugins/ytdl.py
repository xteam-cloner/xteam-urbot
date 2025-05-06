from xteam.fns.ytdl import download_yt, get_yt_link
from telethon import events, Button

from . import get_string, requests, ultroid_cmd


async def download_callback(event):
    opt = event.data.decode().split("_")[1]
    url = event.data.decode().split("_")[2]
    xx = await event.edit(get_string("com_1"))
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    if opt == "ss":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
    elif opt == "vv":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
    elif opt == "s":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
    elif opt == "v":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
    await download_yt(xx, url, ytd)


@ultroid_cmd(
    pattern="isong(s|v|ss|vv) ?(.*)",
)
async def download_from_youtube_(event):
    opt = event.pattern_match.group(1).strip()
    xx = await event.eor(get_string("com_1"))
    if opt == "ss":
        url = event.pattern_match.group(2)
        if not url:
            return await xx.eor(get_string("youtube_1"))
        try:
            requests.get(url)
        except BaseException:
            return await xx.eor(get_string("youtube_2"))
        buttons = [
            [Button.inline(get_string("cb_audio"), data=f"dl_ss_{url}")],
        ]
        await xx.edit(get_string("youtube_9"), buttons=buttons)
    elif opt == "vv":
        url = event.pattern_match.group(2)
        if not url:
            return await xx.eor(get_string("youtube_3"))
        try:
            requests.get(url)
        except BaseException:
            return await xx.eor(get_string("youtube_4"))
        buttons = [
            [Button.inline(get_string("cb_video"), data=f"dl_vv_{url}")],
        ]
        await xx.edit(get_string("youtube_10"), buttons=buttons)
    elif opt == "s":
        try:
            query = event.text.split(" ", 1)[1]
        except IndexError:
            return await xx.eor(get_string("youtube_5"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        buttons = [
            [Button.inline(get_string("cb_audio"), data=f"dl_s_{url}")],
        ]
        await xx.edit(get_string("youtube_11"), buttons=buttons)
    elif opt == "v":
        try:
            query = event.text.split(" ", 1)[1]
        except IndexError:
            return await xx.eor(get_string("youtube_7"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        buttons = [
            [Button.inline(get_string("cb_video"), data=f"dl_v_{url}")],
        ]
        await xx.edit(get_string("youtube_12"), buttons=buttons)
    else:
        return


@ultroid_cmd(incoming=True, func=lambda e: e.is_private)
async def callback_handler(event):
    if event.data and event.data.decode().startswith("dl_"):
        await download_callback(event)
