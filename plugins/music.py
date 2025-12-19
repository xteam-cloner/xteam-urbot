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
from xteam import call_py, asst
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
from . import ultroid_bot, ultroid_cmd as man_cmd, eor as edit_or_reply, eod as edit_delete, callback
from youtubesearchpython import VideosSearch
from xteam import LOGS
from xteam.vcbot.markups import timer_task
from xteam.vcbot import (
    CHAT_TITLE,
    gen_thumb,
    telegram_markup_timer,
    skip_item,
    ytdl,
    ytsearch,
    get_play_text,
    join_call
)
from xteam.vcbot.queues import QUEUE, add_to_queue, clear_queue, get_queue, pop_an_item

logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
PLAY_PIC = "https://telegra.ph/file/6213d2673486beca02967.png"
QUEUE_PIC = "https://telegra.ph/file/d6f92c979ad96b2031cba.png"
FFMPEG_ABSOLUTE_PATH = "/usr/bin/ffmpeg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
COOKIES_FILE_PATH = "cookies.txt"

def vcmention(user):
    full_name = get_display_name(user)
    if not isinstance(user, types.User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"

async def skip_current_song(chat_id):
    if chat_id not in QUEUE:
        return 0
    pop_an_item(chat_id)
    if len(QUEUE[chat_id]) > 0:
        next_song = QUEUE[chat_id][0]
        songname, url, duration, thumb_url, videoid, artist, requester = next_song
        try:
            stream_link_info = await ytdl(url, video_mode=False) 
            hm, ytlink = stream_link_info if isinstance(stream_link_info, tuple) else (1, stream_link_info)
            await join_call(chat_id, link=ytlink)
            return [songname, url, duration, thumb_url, videoid, artist, requester]
        except Exception:
            return await skip_current_song(chat_id)
    else:
        return 1
        
@man_cmd(pattern="play(?:\s|$)([\s\S]*)", group_only=True)
async def vc_play(event):
    title = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    await event.delete()
    if (replied and not replied.audio and not replied.voice and not title or not replied and not title):
        return await edit_or_reply(event, "**Silakan masukkan judul lagu!**")
    if (replied and not replied.audio and not replied.voice) or (not replied and title):
        status_msg = await edit_or_reply(event, "`🔍 Mencari Audio...`")
        query = title if title else replied.message
        search = ytsearch(query)
        if search == 0:
            return await status_msg.edit("**❌ Lagu tidak ditemukan.**")
        songname, url, duration, thumbnail, videoid, artist = search
        thumb = await gen_thumb(videoid)
        caption_text = get_play_text(songname, artist, duration, from_user)
        stream_link_info = await ytdl(url, video_mode=False) 
        hm, ytlink = stream_link_info if isinstance(stream_link_info, tuple) else (1, stream_link_info)
        if hm == 0:
            return await status_msg.edit(f"**Error:** `{ytlink}`")
        if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
            pos = add_to_queue(chat_id, songname, url, duration, thumbnail, videoid, artist, from_user)
            final_caption = f"💡 **Ditambahkan ke Antrean »** `#{pos}`\n{caption_text}"
            await status_msg.delete()
            return await asst.send_file(chat_id, thumb, caption=final_caption, buttons=telegram_markup_timer("00:00", duration))
        else:
            try:
                add_to_queue(chat_id, songname, url, duration, thumbnail, videoid, artist, from_user)
                await join_call(chat_id, link=ytlink, video=False, resolution=0)
                await status_msg.delete()
                pesan_audio = await asst.send_file(chat_id, thumb, caption=caption_text, buttons=telegram_markup_timer("00:00", duration))
                asyncio.create_task(timer_task(event.client, chat_id, pesan_audio.id, duration))
            except Exception as e:
                clear_queue(chat_id)
                await status_msg.edit(f"**ERROR:** `{e}`")
                               
@man_cmd(pattern="vplay(?:\s|$)([\s\S]*)", group_only=True)
async def vc_vplay(event):
    title = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    status_msg = await edit_or_reply(event, "`🔍 Mencari Video...`")
    query = title if title else (replied.message if replied else None)
    if not query:
        return await status_msg.edit("**Berikan judul video!**")
    search = ytsearch(query)
    if search == 0:
        return await status_msg.edit("**❌ Video tidak ditemukan.**")
    songname, url, duration, thumbnail, videoid, artist = search
    thumb = await gen_thumb(videoid)
    stream_link_info = await ytdl(url, video_mode=True) 
    hm, ytlink = stream_link_info if isinstance(stream_link_info, tuple) else (1, stream_link_info)
    if hm == 0:
        return await status_msg.edit(f"**Error:** `{ytlink}`")
    if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
        pos = add_to_queue(chat_id, songname, url, duration, thumbnail, videoid, artist, from_user)
        caption = f"💡 **Ditambahkan ke Antrean »** `#{pos}`\n{get_play_text(songname, artist, duration, from_user)}"
        await status_msg.delete()
        return await asst.send_file(chat_id, thumb, caption=caption, buttons=telegram_markup_timer("00:00", duration))
    else:
        try:
            add_to_queue(chat_id, songname, url, duration, thumbnail, videoid, artist, from_user)
            await join_call(chat_id, link=ytlink, video=True, resolution=720)
            await status_msg.delete()
            pesan_video = await asst.send_file(chat_id, thumb, caption=f"🎥 **Memutar Video**\n{get_play_text(songname, artist, duration, from_user)}", buttons=telegram_markup_timer("00:00", duration))
            asyncio.create_task(timer_task(event.client, chat_id, pesan_video.id, duration))
        except Exception as e:
            clear_queue(chat_id)
            await status_msg.edit(f"**ERROR:** `{e}`")
            
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
        await edit_or_reply(event, f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar:** `{op[0]}`\n**Oleh:** {op[6]}")

@call_py.on_update()
async def unified_update_handler(client, update: Update):
    chat_id = getattr(update, "chat_id", None)
    if isinstance(update, StreamEnded):
        if chat_id in QUEUE and len(QUEUE[chat_id]) > 1:
            data = await skip_current_song(chat_id)
            if data and data != 1:
                try:
                    songname, url, duration, thumb_url, videoid, artist, requester = data
                    thumb = await gen_thumb(videoid)
                    caption = get_play_text(songname, artist, duration, requester)
                    await asst.send_file(chat_id, thumb, caption=f"**⏭ Memutar Berikutnya:**\n{caption}", buttons=telegram_markup_timer("00:00", duration))
                except Exception as e:
                    print(f"DEBUG ERROR: {e}")
    
