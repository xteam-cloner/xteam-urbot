# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_play")

import asyncio
import os
from yt_dlp import YoutubeDL
from telethon.tl.types import DocumentAttributeAudio

from . import LOGS, eor, get_string, ultroid_cmd

COOKIES_FILE = "cookies.txt"

class YTDLManager:
    def __init__(self):
        self.opts = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }

    async def get_info(self, url):
        try:
            with YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info.get('_type') == 'playlist':
                    return info['entries'][0]
                return info
        except Exception as e:
            LOGS.exception(e)
            return None

    async def download(self, url):
        try:
            opts = self.opts.copy()
            opts["extract_flat"] = False
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url)
                return ydl.prepare_filename(info), info
        except Exception as e:
            LOGS.exception(e)
            return None, None

@ultroid_cmd(
    pattern="play( (.*)|$)",
)
async def play_music(event):
    """Play music in voice chat from YouTube."""
    msg = await event.eor(get_string("com_1"))
    chat = event.chat
    if chat.id > 0:  # Not a group
        return await msg.edit(get_string("play_1"))
    
    args = event.pattern_match.group(1).strip()
    if not args and not event.is_reply:
        return await msg.edit(get_string("play_2"))
    
    # Get query from reply or args
    if event.is_reply:
        reply = await event.get_reply_message()
        query = reply.text
    else:
        query = args

    await msg.edit("🔍 Searching...")
    
    # Initialize YouTube downloader
    yt = YTDLManager()
    
    # Handle YouTube links or search
    if not query.startswith(("http://", "https://")):
        query = f"ytsearch:{query}"
    
    # Get video info
    info = await yt.get_info(query)
    if not info:
        return await msg.edit("❌ Failed to fetch video information.")

    # Download audio
    await msg.edit("⬇️ Downloading...")
    file_path, info = await yt.download(info['webpage_url'])
    
    if not file_path:
        return await msg.edit("❌ Failed to download audio.")

    # Prepare metadata
    title = info.get('title', 'Unknown Title')
    duration = int(info.get('duration', 0))
    thumb = info.get('thumbnail', None)
    
    await msg.edit("🎵 Playing...")
    
    try:
        await event.client.send_file(
            event.chat_id,
            file=file_path,
            caption=f"🎵 **Now Playing:** {title}\n⏱️ **Duration:** {duration//60}:{duration%60:02d}",
            thumb=thumb,
            voice_note=True,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=title,
                    performer="Ultroid Music"
                )
            ]
        )
        await msg.delete()
    except Exception as e:
        LOGS.exception(e)
        await msg.edit(f"❌ Error: {str(e)}")
    finally:
        try:
            os.remove(file_path)
        except:
            pass

@ultroid_cmd(
    pattern="skip$",
)
async def skip_track(event):
    """Skip the current playing track."""
    msg = await event.eor(get_string("com_1"))
    try:
        await msg.edit("⏭️ Skipped current track.")
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

@ultroid_cmd(
    pattern="stop$",
)
async def stop_music(event):
    """Stop the current playing music."""
    msg = await event.eor(get_string("com_1"))
    try:
        await msg.edit("⏹️ Stopped playing.")
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

@ultroid_cmd(
    pattern="queue$",
)
async def show_queue(event):
    """Show the current music queue."""
    msg = await event.eor(get_string("com_1"))
    try:
        await msg.edit("📋 Queue is empty.")
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")s
