# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.


import os
import re

try:
    from PIL import Image
except ImportError:
    Image = None
from telethon import Button
from telethon.errors.rpcerrorlist import FilePartLengthInvalidError, MediaEmptyError
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from telethon.tl.types import InputWebDocument as wb

from xteam.fns.helper import (
    bash,
    fast_download,
    humanbytes,
    numerize,
    time_formatter,
)
from xteam.fns.ytdl import dler, get_buttons, get_formats

from . import LOGS, asst, callback, in_pattern, udB

try:
    from youtubesearchpython import VideosSearch
except ImportError:
    LOGS.info("'youtubesearchpython' not installed!")
    VideosSearch = None


ytt = "https://graph.org/file/afd04510c13914a06dd03.jpg"
_yt_base_url = "https://www.youtube.com/watch?v="
BACK_BUTTON = {}


@in_pattern("yt", owner=True)
async def _(event):
    try:
        string = event.text.split(" ", maxsplit=1)[1]
    except IndexError:
        fuk = event.builder.article(
            title="Search Something",
            thumb=wb(ytt, 0, "image/jpeg", []),
            text="**YᴏᴜTᴜʙᴇ Sᴇᴀʀᴄʜ**\n\nYou didn't search anything",
            buttons=Button.switch_inline(
                "Sᴇᴀʀᴄʜ Aɢᴀɪɴ",
                query="yt ",
                same_peer=True,
            ),
        )
        await event.answer([fuk])
        return
    results = []
    search = VideosSearch(string, limit=50)
    nub = search.result()
    nibba = nub["result"]
    for v in nibba:
        ids = v["id"]
        link = _yt_base_url + ids
        title = v["title"]
        duration = v["duration"]
        views = v["viewCount"]["short"]
        publisher = v["channel"]["name"]
        published_on = v["publishedTime"]
        description = (
            v["descriptionSnippet"][0]["text"]
            if v.get("descriptionSnippet")
            and len(v["descriptionSnippet"][0]["text"]) < 500
            else "None"
        )
        thumb = f"https://i.ytimg.com/vi/{ids}/hqdefault.jpg"
        text = f"**Title: [{title}]({link})**\n\n"
        text += f"`Description: {description}\n\n"
        text += f"「 Duration: {duration} 」\n"
        text += f"「 Views: {views} 」\n"
        text += f"「 Publisher: {publisher} 」\n"
        text += f"「 Published on: {published_on} 」`"
        desc = f"{title}\n{duration}"
        file = wb(thumb, 0, "image/jpeg", [])
        buttons = [
            [
                Button.inline("Audio", data=f"ytdl:audio:{ids}"),
                Button.inline("Video", data=f"ytdl:video:{ids}"),
            ],
            [
                Button.switch_inline(
                    "Sᴇᴀʀᴄʜ Aɢᴀɪɴ",
                    query="yt ",
                    same_peer=True,
                ),
                Button.switch_inline(
                    "Sʜᴀʀᴇ",
                    query=f"yt {string}",
                    same_peer=False,
                ),
            ],
        ]
        BACK_BUTTON.update({ids: {"text": text, "buttons": buttons}})
        results.append(
            await event.builder.article(
                type="photo",
                title=title,
                description=desc,
                thumb=file,
                content=file,
                text=text,
                include_media=True,
                buttons=buttons,
            ),
        )
    await event.answer(results[:50])


@callback(
    re.compile(
        "ytdownload:(.*)",
    ),
    owner=True,
)
async def _(event):
    # Parsing URL dan Data
    url_data = event.pattern_match.group(1).strip()
    if isinstance(url_data, bytes):
        url_data = url_data.decode("UTF-8")
    
    lets_split = url_data.split(":")
    tipe_konten = lets_split[0]  # audio / video
    format_val = lets_split[1]   # kualitas (misal: 128 / 720)
    vid_id = lets_split[2]
    link = _yt_base_url + vid_id
    
    try:
        ext = lets_split[3]
    except IndexError:
        ext = "mp3" if tipe_konten == "audio" else "mkv"

    # Konfigurasi Cookies
    cookie_path = "cookies.txt"
    if not os.path.exists(cookie_path):
        cookie_path = None

    # Pengaturan Opsi yt-dlp
    if tipe_konten == "audio":
        opts = {
            "format": "bestaudio",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
            "outtmpl": f"%(id)s.{ext}",
            "logtostderr": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": ext,
                    "preferredquality": format_val,
                },
                {"key": "FFmpegMetadata"},
            ],
        }
    else: # video
        opts = {
            "format": str(format_val),
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "cookiefile": "cookies.txt",
            "outtmpl": f"%(id)s.{ext}",
            "logtostderr": False,
            "postprocessors": [{"key": "FFmpegMetadata"}],
        }

    # Proses Download Metadata & File
    ytdl_data = await dler(event, link, opts, True)
    title = ytdl_data.get("title", "Unknown Title")
    
    # Mencari nama Artist/Channel
    artist = (
        ytdl_data.get("artist") or 
        ytdl_data.get("creator") or 
        ytdl_data.get("channel") or 
        "Unknown"
    )
    
    views = numerize(ytdl_data.get("view_count")) or 0
    likes = numerize(ytdl_data.get("like_count")) or 0
    duration = ytdl_data.get("duration") or 0
    
    # Download Thumbnail
    thumb, _ = await fast_download(ytdl_data["thumbnail"], filename=f"{vid_id}.jpg")
    try:
        Image.open(thumb).convert("RGB").save(thumb, "JPEG")
    except Exception as er:
        LOGS.exception(er)
        thumb = None

    # Deskripsi Singkat
    description = ytdl_data.get("description") or "None"
    if len(description) > 100:
        description = description[:100] + "..."

    # Menentukan Filepath untuk Upload
    if tipe_konten == "audio":
        filepath = f"{vid_id}.{ext}"
        if not os.path.exists(filepath):
            filepath = f"{filepath}.{ext}"
        
        attributes = [
            DocumentAttributeAudio(
                duration=int(duration),
                title=title,
                performer=artist,
            ),
        ]
        filename_upload = f"{title}.{ext}"
    else: # video
        # yt-dlp kadang merubah ekstensi secara otomatis, kita cek manual
        filepath = f"{vid_id}.{ext}"
        if not os.path.exists(filepath):
            for e in ["mkv", "mp4", "webm"]:
                if os.path.exists(f"{vid_id}.{e}"):
                    filepath = f"{vid_id}.{e}"
                    break
        
        attributes = [
            DocumentAttributeVideo(
                duration=int(duration),
                w=ytdl_data.get("width") or 1280,
                h=ytdl_data.get("height") or 720,
                supports_streaming=True,
            ),
        ]
        filename_upload = f"{title}.mkv"

    size = os.path.getsize(filepath)

    # Proses Upload
    file, _ = await event.client.fast_uploader(
        filepath,
        filename=filename_upload,
        show_progress=True,
        event=event,
        to_delete=True,
    )

    # Menyusun Teks Pesan
    text = (
        f"**Title: [{title}]({_yt_base_url}{vid_id})**\n\n"
        f"`📝 Description: {description}\n\n"
        f"「 Duration: {time_formatter(int(duration)*1000)} 」\n"
        f"「 Artist: {artist} 」\n"
        f"「 Views: {views} 」\n"
        f"「 Likes: {likes} 」\n"
        f"「 Size: {humanbytes(size)} 」`"
    )
    
    button = Button.switch_inline("Search More", query="yt ", same_peer=True)

    # Mengirim Hasil
    try:
        await event.edit(
            text,
            file=file,
            buttons=button,
            attributes=attributes,
            thumb=thumb,
        )
    except (FilePartLengthInvalidError, MediaEmptyError):
        file_msg = await asst.send_message(
            udB.get_key("LOG_CHANNEL"),
            text,
            file=file,
            buttons=button,
            attributes=attributes,
            thumb=thumb,
        )
        await event.edit(text, file=file_msg.media, buttons=button)
    
    # Cleanup thumbnail
    if thumb and os.path.exists(thumb):
        os.remove(thumb)
        

@callback(re.compile("ytdl_back:(.*)"), owner=True)
async def ytdl_back(event):
    id_ = event.data_match.group(1).decode("utf-8")
    if not BACK_BUTTON.get(id_):
        return await event.answer("Query Expired! Search again 🔍")
    await event.edit(**BACK_BUTTON[id_])
