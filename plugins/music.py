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

async def skip_current_song(chat_id: int):
    if chat_id not in QUEUE:
        return 0
    if len(QUEUE[chat_id]) > 1:
        QUEUE[chat_id].pop(0)
    else:
        QUEUE[chat_id] = []
        return 1
    next_song = QUEUE[chat_id][0]
    songname, url, link, type_mode, RESOLUSI = next_song
    is_video = (type_mode == "Video")
    try:
        await join_call(chat_id, link=url, video=is_video, resolution=RESOLUSI)
        return [songname, link]
    except Exception as e:
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
    
    # KONDISI 1: JIKA TIDAK ADA REPLY (CARI DI YOUTUBE)
    elif replied and not replied.audio and not replied.voice or not replied:
        botman = await edit_or_reply(event, "`Searching Audio...`")
        query = event.text.split(maxsplit=1)[1] if not replied else title
        search = ytsearch(query)
        if search == 0:
            return await botman.edit("**Tidak Dapat Menemukan Lagu**")
        
        songname, url, duration, thumbnail, videoid = search
        ctitle = await CHAT_TITLE(chat.title)
        thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
        
        # Mengambil link stream dari ytdl
        stream_link_info = await ytdl(url, video_mode=False) 
        hm, ytlink = stream_link_info if isinstance(stream_link_info, tuple) else (1, stream_link_info)
        
        if hm == 0:
            return await botman.edit(f"`{ytlink}`")

        if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
            pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
            caption = f"💡 **Audio Added to queue »** `#{pos}`\n\n**🏷 Title:** [{songname}]({url})\n**⏱ Duration:** `{duration}`\n🎧 **Request By:** {from_user}"
            await botman.delete()
            return await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
        else:
            try:
                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                # MENGGUNAKAN JOIN_CALL SEPERTI NOMOR 1
                await join_call(chat_id, link=ytlink, video=False, resolution=0)
                caption = f"🏷 **Title:** [{songname}]({url})\n**⏱ Duration:** `{duration}`\n💡 **Status:** `Now Playing`\n🎧 **Request By:** {from_user}"
                await botman.delete()
                return await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
            except Exception as ep:
                clear_queue(chat_id)
                await botman.edit(f"**ERROR:** `{ep}`")

    # KONDISI 2: JIKA REPLY FILE TELEGRAM
    else:
        botman = await edit_or_reply(event, "📥 **Sedang Mendownload Audio...**")
        dl = await replied.download_media()
        link = f"https://t.me/c/{str(chat.id)[4:] if str(chat.id).startswith('-100') else chat.id}/{replied.id}"
        songname = "Telegram Music Player" if replied.audio else "Voice Note"

        if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
            pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
            caption = f"💡 **Audio Added to queue »** `#{pos}`\n\n**🏷 Title:** [{songname}]({link})\n🎧 **Request By:** {from_user}"
            await event.client.send_file(chat_id, QUEUE_PIC, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
            await botman.delete()
        else:
            try:
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                # MENGGUNAKAN JOIN_CALL SEPERTI NOMOR 1
                await join_call(chat_id, link=dl, video=False, resolution=0)
                caption = f"🏷 **Title:** [{songname}]({link})\n💡 **Status:** `Now Playing`\n🎧 **Request By:** {from_user}"
                await botman.delete()
                return await event.client.send_file(chat_id, PLAY_PIC, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
            except Exception as ep:
                clear_queue(chat_id)
                await botman.edit(f"**ERROR:** `{ep}`")
    
@man_cmd(pattern="vplay(?:\s|$)([\s\S]*)", group_only=True)
async def vc_vplay(event):
    title = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    
    # Variabel pesan didefinisikan sebagai 'xnxx'
    xnxx = await edit_or_reply(event, "`Searching Video...`")
    
    query = event.text.split(maxsplit=1)[1] if not replied else title
    search = ytsearch(query)
    if search == 0:
        return await xnxx.edit("**Tidak Dapat Menemukan Video**")
    
    songname, url, duration, thumbnail, videoid = search
    ctitle = await CHAT_TITLE(chat.title)
    thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
    
    stream_link_info = await ytdl(url, video_mode=True) 
    hm, ytlink = stream_link_info if isinstance(stream_link_info, tuple) else (1, stream_link_info)
    
    if hm == 0:
        return await xnxx.edit(f"`{ytlink}`")

    # LOGIKA ANTREAN
    if chat_id in QUEUE and len(QUEUE[chat_id]) > 0:
        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", 720)
        caption = f"💡 **Video Ditambahkan Ke Antrean »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n🎧 **Atas permintaan:** {from_user}"
        
        # PERBAIKAN: Gunakan xnxx.delete(), bukan xteambot
        await xnxx.delete()
        return await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
    
    else:
        try:
            add_to_queue(chat_id, songname, ytlink, url, "Video", 720)
            await join_call(chat_id, link=ytlink, video=True, resolution=720)
            
            caption = f"🏷 **Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}"
            
            # PERBAIKAN: Gunakan xnxx.delete(), bukan xteambot
            await xnxx.delete()
            return await event.client.send_file(chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS)
        except Exception as ep:
            clear_queue(chat_id)
            await xnxx.edit(f"**ERROR:** `{ep}`")
            

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

@man_cmd(pattern="pause$", group_only=True)
async def vc_pause(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        try:
            await call_py.pause(chat_id)
            await edit_or_reply(event, "**Streaming Dijeda**")
        except Exception as e:
            await edit_delete(event, f"**ERROR:** `{e}`")
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern="resume$", group_only=True)
async def vc_resume(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        try:
            await call_py.resume(chat_id)
            await edit_or_reply(event, "**Streaming Dilanjutkan**")
        except Exception as e:
            await edit_or_reply(event, f"**ERROR:** `{e}`")
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern=r"volume(?: |$)(.*)", group_only=True)
async def vc_volume(event):
    query = event.pattern_match.group(1)
    me = await event.client.get_me()
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    chat_id = event.chat_id
    
    if not admin and not creator:
        if not await admin_check(event):
             return await edit_delete(event, f"**Maaf {me.first_name} Bukan Admin 👮**", 30)

    if chat_id in QUEUE:
        try:
            volume_level = int(query)
            if not 0 <= volume_level <= 100:
                return await edit_delete(event, "**Volume harus antara 0 dan 100.**", 10)
            await call_py.change_volume_call(chat_id, volume=volume_level)
            await edit_or_reply(
                event, f"**Berhasil Mengubah Volume Menjadi** `{volume_level}%`"
            )
        except ValueError:
             await edit_delete(event, "**Mohon masukkan angka yang valid untuk volume.**", 10)
        except Exception as e:
            await edit_delete(event, f"**ERROR:** `{e}`", 30)
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern="playlist$", group_only=True)
async def vc_playlist(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if not chat_queue:
            return await edit_delete(event, "**Tidak Ada Lagu Dalam Antrian**", time=10)

        PLAYLIST = f"**🎧 Sedang Memutar:**\n**• [{chat_queue[0][0]}]({chat_queue[0][2]})** | `{chat_queue[0][3]}` \n\n**• Daftar Putar:**"
        
        l = len(chat_queue)
        for x in range(1, l): 
            hmm = chat_queue[x][0]
            hmmm = chat_queue[x][2]
            hmmmm = chat_queue[x][3]
            PLAYLIST = PLAYLIST + "\n" + f"**#{x}** - [{hmm}]({hmmm}) | `{hmmmm}`"
            
        await edit_or_reply(event, PLAYLIST, link_preview=False)
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@call_py.on_update()
async def unified_update_handler(client, update: Update) -> None:
    try:
        chat_id = update.chat_id
    except:
        return

    if isinstance(update, StreamEnded):
        if chat_id in QUEUE:
            op = await skip_current_song(chat_id) 
            if isinstance(op, list):
                await client.send_message(
                    chat_id,
                    f"**🎧 Sekarang Memutar:** [{op[0]}]({op[1]})",
                    link_preview=False,
                )
            elif op == 1:
                await client.send_message(chat_id, "**💡 Antrean habis. Bot Standby.**")

    elif isinstance(update, ChatUpdate):
        status = update.status
        CRITICAL = (ChatUpdate.Status.KICKED | ChatUpdate.Status.LEFT_GROUP | ChatUpdate.Status.CLOSED_VOICE_CHAT)
        if (status & ChatUpdate.Status.LEFT_CALL) or (status & CRITICAL):
            clear_queue(chat_id)

MUSIC_BUTTONS = [
    [
        Button.inline("⏸", data="pauseit"),
        Button.inline("▶️", data="resumeit")
    ],
    [
        Button.inline("⏭", data="skipit"),
        Button.inline("⏹", data="stopit")
    ],
    [
        Button.inline("🗑", data="closeit")
    ]
]


@callback(data=re.compile(b"(pauseit|resumeit|stopit|skipit|closeit)"), owner=True)
async def music_manager(e):
    query = e.data.decode("utf-8")
    chat_id = e.chat_id
    try:
        if query == "pauseit":
            await call_py.pause(chat_id)
            await e.answer("Pause", alert=False)
        elif query == "resumeit":
            await call_py.resume(chat_id)
            await e.answer("Resume", alert=False)
        elif query == "stopit":
            await call_py.leave_call(chat_id)
            await e.delete()
        elif query == "skipit":
            await call_py.drop_user(chat_id)
            await e.answer("⏭", alert=False)
        elif query == "closeit":
            await e.delete()
    except Exception as err:
        await e.answer(f"⚠️ Error: {str(err)}", alert=True)
