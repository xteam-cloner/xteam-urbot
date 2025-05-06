from xteam.fns.ytdl import download_yt, get_yt_link
from . import get_string, requests, ultroid_cmd
from telethon import Button

@ultroid_cmd(
    pattern="down ?(.*)",
)
async def download_from_youtube_(event):
    # Create buttons for user selection
    buttons = [
        [Button.inline("Download Song", data="download_song")],
        [Button.inline("Download Video", data="download_video")]
    ]
    
    await event.eor("Please choose an option:", buttons=buttons)

@ultroid_cmd(
    pattern="button_callback",
)
async def button_callback(event):
    data = event.data.decode("utf-8")
    if data == "download_song":
        await handle_download(event, "s")
    elif data == "download_video":
        await handle_download(event, "v")

async def handle_download(event, opt):
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    
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
