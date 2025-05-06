from xteam.fns.ytdl import download_yt, get_yt_link
from telethon import events, Button

from . import get_string, requests, ultroid_cmd


@ultroid_cmd(
    pattern="isong(s|v|ss|vv) ?(.*)",
)
async def download_from_youtube_(event):
    buttons = [
        [
            Button.inline("Audio (Best)", data="song_s"),
            Button.inline("Video (Best)", data="song_v"),
        ],
        [
            Button.inline("Audio (URL)", data="song_ss"),
            Button.inline("Video (URL)", data="song_vv"),
        ],
    ]
    if not event.pattern_match.group(1).strip():
        return await event.reply(get_string("youtube_0"), buttons=buttons)

    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    opt = event.pattern_match.group(1).strip()
    xx = await event.eor(get_string("com_1"))
    url = event.pattern_match.group(2)

    if opt == "ss":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
        if not url:
            return await xx.eor(get_string("youtube_1"))
        try:
            requests.get(url)
        except BaseException:
            return await xx.eor(get_string("youtube_2"))
    elif opt == "vv":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
        if not url:
            return await xx.eor(get_string("youtube_3"))
        try:
            requests.get(url)
        except BaseException:
            return await xx.eor(get_string("youtube_4"))
    elif opt == "s":
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


@events.callbackquery.filter(data=re.compile(r"^song_(s|v|ss|vv)$"))
async def song_callback(event):
    opt = event.data.decode().split("_")[1]
    ytd = {
        "prefer_ffmpeg": True,
        "addmetadata": True,
        "geo-bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
    xx = await event.edit(get_string("com_1"))
    user_input = event.message.reply_to_msg_id if event.message.is_reply else None

    if opt == "ss":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
        await xx.edit(get_string("youtube_9"))
        try:
            response = await event.client.get_response(event.chat_id, timeout=30)
            url = response.text
            try:
                requests.get(url)
            except BaseException:
                return await xx.eor(get_string("youtube_2"))
        except asyncio.TimeoutError:
            return await xx.edit(get_string("time_out"))
    elif opt == "vv":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
        await xx.edit(get_string("youtube_10"))
        try:
            response = await event.client.get_response(event.chat_id, timeout=30)
            url = response.text
            try:
                requests.get(url)
            except BaseException:
                return await xx.eor(get_string("youtube_4"))
        except asyncio.TimeoutError:
            return await xx.edit(get_string("time_out"))
    elif opt == "s":
        ytd["format"] = "bestaudio"
        ytd["outtmpl"] = "%(id)s.m4a"
        if not user_input:
            return await xx.edit(get_string("youtube_5"))
        reply_msg = await event.get_reply_message()
        query = reply_msg.text if reply_msg else None
        if not query:
            return await xx.edit(get_string("youtube_5"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        await xx.eor(get_string("youtube_6"))
    elif opt == "v":
        ytd["format"] = "best"
        ytd["outtmpl"] = "%(id)s.mp4"
        ytd["postprocessors"] = [{"key": "FFmpegMetadata"}]
        if not user_input:
            return await xx.edit(get_string("youtube_7"))
        reply_msg = await event.get_reply_message()
        query = reply_msg.text if reply_msg else None
        if not query:
            return await xx.edit(get_string("youtube_7"))
        url = get_yt_link(query)
        if not url:
            return await xx.edit(get_string("unspl_1"))
        await xx.eor(get_string("youtube_8"))
    else:
        return
    await download_yt(xx, url, ytd)
