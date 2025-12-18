from __future__ import annotations
import asyncio
import os
import re
import contextlib 
import logging
import functools
import yt_dlp
from . import *
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import httpx
from telethon import events, TelegramClient, Button
from telethon.tl.types import Message, User, TypeUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import (
    UserPrivacyRestrictedError, 
    ChatAdminRequiredError, 
    UserAlreadyParticipantError
)
from xteam.configs import Var 
from xteam import call_py, bot as client
from telethon.utils import get_display_name
from xteam.fns.admins import admin_check 
from pytgcalls import PyTgCalls, filters as fl
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall, NoAudioSourceFound, NoVideoSourceFound
from pytgcalls.types import (
    Update,
    ChatUpdate,
    MediaStream,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
)
from pytgcalls.types.stream import VideoQuality, AudioQuality
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors.rpcerrorlist import (
    UserNotParticipantError,
    UserAlreadyParticipantError
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from youtubesearchpython.__future__ import VideosSearch
from . import ultroid_cmd as man_cmd, eor as edit_or_reply, eod as edit_delete, callback
from youtubesearchpython import VideosSearch
from xteam import LOGS
from xteam.vcbot import (
    CHAT_TITLE,
    gen_thumb,
    #skip_current_song,
    skip_item,
    ytdl,
    ytsearch,
    join_call
)
from xteam.vcbot.queues import QUEUE, add_to_queue, clear_queue, get_queue

logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
FFMPEG_ABSOLUTE_PATH = "/usr/bin/ffmpeg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
COOKIES_FILE_PATH = "cookies.txt"

def vcmention(user):
    full_name = get_display_name(user)
    if not isinstance(user, types.User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"

async def skip_current_song(chat_id: int):
    if chat_id not in QUEUE:
        return 0
    if len(QUEUE[chat_id]) > 1:
        QUEUE[chat_id].pop(0)
    else:
        QUEUE[chat_id] = []
        return 1

    next_song = QUEUE[chat_id][0]
    songname, url, link, type, RESOLUSI = next_song
    
    if type == "Audio":
        stream = MediaStream(media_path=url, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
    else:
        stream = MediaStream(media_path=url, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.HD_720p)

    try:
        await call_py.play(chat_id, stream)
        return [songname, link]
    except:
        return await skip_current_song(chat_id)

@man_cmd(pattern="play(?:\s|$)([\s\S]*)", group_only=True)
async def vc_play(event):
    title = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    
    if (replied and not replied.audio and not replied.voice and not title or not replied and not title):
        return await edit_or_reply(event, "**Silahkan Masukan Judul Lagu**")
    
    elif replied and not replied.audio and not replied.voice or not replied:
        botman = await edit_or_reply(event, "`Searching...`")
        query = event.text.split(maxsplit=1)[1] if not replied else title
        search = ytsearch(query)
        if search == 0:
            return await botman.edit("**Tidak Dapat Menemukan Lagu**")
        
        songname, url, duration, thumbnail, videoid = search
        ctitle = await CHAT_TITLE(chat.title)
        thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
        hm, ytlink = await ytdl(url)
        
        if hm == 0:
            return await botman.edit(f"`{ytlink}`")

        stream = MediaStream(media_path=ytlink, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)

        if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
            pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
            caption = f"💡 **Lagu Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n🎧 **Atas permintaan:** {from_user}"
            await botman.delete()
            return await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id)
        else:
            try:
                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                await call_py.join_call(chat_id, stream)
                caption = f"🏷 **Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar`\n🎧 **Atas permintaan:** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id)
            except AlreadyJoinedError:
                await call_py.play(chat_id, stream)
                caption = f"🏷 **Judul:** [{songname}]({url})\n💡 **Status:** `Memutar (Standby)`\n🎧 **Atas permintaan:** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id)
            except Exception as ep:
                clear_queue(chat_id)
                await botman.edit(f"`{ep}`")
    else:
        botman = await edit_or_reply(event, "📥 **Sedang Mendownload**")
        dl = await replied.download_media()
        link = f"https://t.me/c/{str(chat.id)[4:] if str(chat.id).startswith('-100') else chat.id}/{replied.id}"
        songname = "Telegram Music Player" if replied.audio else "Voice Note"
        
        stream = MediaStream(media_path=dl, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)

        if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
            pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
            caption = f"💡 **Lagu Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({link})\n🎧 **Atas permintaan:** {from_user}"
            await event.client.send_file(chat_id, QUEUE_PIC, caption=caption, reply_to=event.reply_to_msg_id)
            await botman.delete()
        else:
            try:
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await call_py.join_call(chat_id, stream)
                caption = f"🏷 **Judul:** [{songname}]({link})\n💡 **Status:** `Sedang Memutar Lagu`\n🎧 **Atas permintaan:** {from_user}"
                await event.client.send_file(chat_id, PLAY_PIC, caption=caption, reply_to=event.reply_to_msg_id)
                await botman.delete()
            except AlreadyJoinedError:
                await call_py.play(chat_id, stream)
                await botman.delete()
                await event.client.send_file(chat_id, PLAY_PIC, caption=caption)
            except Exception as ep:
                clear_queue(chat_id)
                await botman.edit(f"`{ep}`")

@man_cmd(pattern="vplay(?:\s|$)([\s\S]*)", group_only=True)
async def vc_vplay(event):
    title = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    
    xnxx = await edit_or_reply(event, "`Searching Video...`")
    query = event.text.split(maxsplit=1)[1] if not replied else title
    search = ytsearch(query)
    if search == 0:
        return await xnxx.edit("**Tidak Dapat Menemukan Video**")
    
    songname, url, duration, thumbnail, videoid = search
    ctitle = await CHAT_TITLE(chat.title)
    thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
    hm, ytlink = await ytdl(url)
    
    stream = MediaStream(media_path=ytlink, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.HD_720p)

    if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", 720)
        caption = f"💡 **Video Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n🎧 **Atas permintaan:** {from_user}"
        await xnxx.delete()
        await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id)
    else:
        try:
            add_to_queue(chat_id, songname, ytlink, url, "Video", 720)
            await call_py.join_call(chat_id, stream)
            caption = f"🏷 **Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}"
            await xnxx.delete()
            await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id)
        except AlreadyJoinedError:
            await call_py.play(chat_id, stream)
            await xnxx.delete()
            await event.client.send_file(chat_id, thumb, caption=caption)
        except Exception as ep:
            clear_queue(chat_id)
            await xnxx.edit(f"`{ep}`")

@man_cmd(pattern="end$", group_only=True)
async def vc_end(event):
    chat_id = event.chat_id
    try:
        await call_py.leave_call(chat_id)
        clear_queue(chat_id)
        await edit_or_reply(event, "**Streaming Berhenti.**")
    except Exception as e:
        await edit_delete(event, f"**ERROR:** `{e}`")

@man_cmd(pattern="skip(?:\s|$)([\s\S]*)", group_only=True)
async def vc_skip(event):
    chat_id = event.chat_id
    op = await skip_current_song(chat_id)
    if op == 0:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")
    elif op == 1:
        await edit_delete(event, "**Antrian habis, bot standby.**", 10)
    else:
        await edit_or_reply(event, f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar** - [{op[0]}]({op[1]})", link_preview=False)
