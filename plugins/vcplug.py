from __future__ import annotations
import asyncio
import os
import re
import contextlib 
import logging
import functools
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

import httpx
from xteam.vcbot import *
from . import * 
from telethon import events, TelegramClient, Button
from telethon.tl.types import Message, User, TypeUser
from xteam.configs import Var 
from xteam import call_py, bot as client
from xteam import ultroid_bot 
from telethon.utils import get_display_name
from xteam.fns.admins import admin_check 
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError
from pytgcalls.types import (
    Update,
    ChatUpdate,
    MediaStream,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
    AudioQuality,
    VideoQuality,
    # StreamType, # TELAH DIHAPUS
)
# Perhatikan bahwa jika StreamType tidak ada, ia harus dihapus dari daftar impor di atas juga.
# Karena Anda tidak mengirimkan kembali daftar impor yang diperbarui, saya asumsikan sudah dihapus.
# Saya HAPUS JUGA IMPOR YANG SAYA TAMBAHKAN DARI BAWAH
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors.rpcerrorlist import (
    UserNotParticipantError,
    UserAlreadyParticipantError
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.messages import ImportChatInviteRequest


import yt_dlp
from youtubesearchpython.__future__ import VideosSearch

from . import ultroid_cmd as man_cmd, eor as edit_or_reply, edit_delete 
logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")


def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=ffmpeg_params,
        )
    else:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=ffmpeg_params,
        )

def vcmention(user: TypeUser):
    full_name = get_display_name(user)
    if not isinstance(user, User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"


@man_cmd(pattern="play(?:\s|$)([\s\S]*)", group_only=True)
async def vc_play(event):
    title_match = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    
    if not title_match and not (replied and (replied.audio or replied.voice)):
        return await edit_or_reply(event, "**Silahkan Masukan Judul Lagu**")

    if not replied or (replied and not replied.audio and not replied.voice):
        botman = await edit_or_reply(event, "`Searching...`")
        query = event.text.split(maxsplit=1)[1]
        search = ytsearch(query)
        
        if search == 0:
            return await botman.edit("**Tidak Dapat Menemukan Lagu** Coba cari dengan Judul yang Lebih Spesifik")
        
        songname, url, duration, thumbnail, videoid = search
        ctitle = await CHAT_TITLE(chat.title)
        thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
        hm, ytlink = await ytdl(url)

        if hm == 0:
            return await botman.edit(f"`{ytlink}`")

        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
            caption = f"💡 **Lagu Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n🎧 **Atas permintaan:** {from_user}"
            await botman.delete()
            return await event.client.send_file(
                chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id
            )
        else:
            try:
                await call_py.join_group_call(
                    chat_id,
                    dynamic_media_stream(ytlink, video=False),
                    # stream_type=StreamType().pulse_stream, # DIHAPUS
                )
                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                caption = f"🏷 **Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar`\n🎧 **Atas permintaan:** {from_user}"
                await botman.delete()
                return await event.client.send_file(
                    chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id
                )
            except AlreadyJoinedError:
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await botman.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await botman.edit(f"**ERROR:** `{ep}`")

    else:
        botman = await edit_or_reply(event, "📥 **Sedang Mendownload**")
        dl = await replied.download_media()
        link = f"https://t.me/c/{chat_id}/{event.reply_to_msg_id}"
        songname = "Telegram Music Player" if replied.audio else "Voice Note"
        
        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
            caption = f"💡 **Lagu Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n🎧 **Atas permintaan:** {from_user}"
            await event.client.send_file(
                chat_id, ngantri, caption=caption, reply_to=event.reply_to_msg_id
            )
            await botman.delete()
        else:
            try:
                await call_py.join_group_call(
                    chat_id,
                    dynamic_media_stream(dl, video=False),
                    # stream_type=StreamType().pulse_stream, # DIHAPUS
                )
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                caption = f"🏷 **Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n💡 **Status:** `Sedang Memutar Lagu`\n🎧 **Atas permintaan:** {from_user}"
                await event.client.send_file(
                    chat_id, fotoplay, caption=caption, reply_to=event.reply_to_msg_id
                )
                await botman.delete()
            except AlreadyJoinedError:
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await botman.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await botman.edit(f"**ERROR:** `{ep}`")


@man_cmd(pattern="vplay(?:\s|$)([\s\S]*)", group_only=True)
async def vc_vplay(event):
    title_match = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    RESOLUSI = 720
    
    if not title_match and not (replied and (replied.video or replied.document)):
        return await edit_or_reply(event, "**Silahkan Masukan Judul Video**")

    if not replied or (replied and not replied.video and not replied.document):
        xnxx = await edit_or_reply(event, "`Searching...`")
        query = event.text.split(maxsplit=1)[1]
        search = ytsearch(query)
        
        if search == 0:
            return await xnxx.edit("**Tidak Dapat Menemukan Video** Coba cari dengan Judul yang Lebih Spesifik")
        
        songname, url, duration, thumbnail, videoid = search
        ctitle = await CHAT_TITLE(chat.title)
        thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
        hm, ytlink = await ytdl(url)

        if hm == 0:
            return await xnxx.edit(f"`{ytlink}`")

        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, ytlink, url, "Video", RESOLUSI)
            caption = f"💡 **Video Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n🎧 **Atas permintaan:** {from_user}"
            await xnxx.delete()
            return await event.client.send_file(
                chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id
            )
        else:
            try:
                await call_py.join_group_call(
                    chat_id,
                    dynamic_media_stream(ytlink, video=True),
                    # stream_type=StreamType().pulse_stream, # DIHAPUS
                )
                add_to_queue(chat_id, songname, ytlink, url, "Video", RESOLUSI)
                return await xnxx.edit(
                    f"**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}",
                    link_preview=False,
                )
            except AlreadyJoinedError:
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await xnxx.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await xnxx.edit(f"**ERROR:** `{ep}`")

    else:
        xnxx = await edit_or_reply(event, "📥 **Sedang Mendownload**")
        dl = await replied.download_media()
        link = f"https://t.me/c/{chat_id}/{event.reply_to_msg_id}"
        songname = "Telegram Video Player"
        
        if len(event.text.split()) > 1:
            try:
                RESOLUSI = int(event.text.split(maxsplit=1)[1])
            except ValueError:
                pass

        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl, link, "Video", RESOLUSI)
            caption = f"💡 **Video Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n🎧 **Atas permintaan:** {from_user}"
            await event.client.send_file(
                chat_id, ngantri, caption=caption, reply_to=event.reply_to_msg_id
            )
            await xnxx.delete()
        else:
            try:
                await call_py.join_group_call(
                    chat_id,
                    dynamic_media_stream(dl, video=True),
                    # stream_type=StreamType().pulse_stream, # DIHAPUS
                )
                add_to_queue(chat_id, songname, dl, link, "Video", RESOLUSI)
                caption = f"🏷 **Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}"
                await xnxx.delete()
                return await event.client.send_file(
                    chat_id, fotoplay, caption=caption, reply_to=event.reply_to_msg_id
                )
            except AlreadyJoinedError:
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await xnxx.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await xnxx.edit(f"**ERROR:** `{ep}`")


@man_cmd(pattern="end$", group_only=True)
async def vc_end(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        try:
            await call_py.leave_group_call(chat_id)
            clear_queue(chat_id)
            await edit_or_reply(event, "**Menghentikan Streaming**")
        except Exception as e:
            await edit_delete(event, f"**ERROR:** `{e}`")
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern="skip(?:\s|$)([\s\S]*)", group_only=True)
async def vc_skip(event):
    chat_id = event.chat_id
    if len(event.text.split()) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await edit_delete(event, "**Tidak Sedang Memutar Streaming**")
        elif op == 1:
            await edit_delete(event, "antrian kosong, meninggalkan obrolan suara", 10)
        else:
            await edit_or_reply(
                event,
                f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar** - [{op[0]}]({op[1]})",
                link_preview=False,
            )
    else:
        skip = event.text.split(maxsplit=1)[1]
        DELQUE = "**Menghapus Lagu Berikut Dari Antrian:**"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x != 0:
                    hm = await skip_item(chat_id, x)
                    if hm != 0:
                        DELQUE = DELQUE + "\n" + f"**#{x}** - {hm}"
            await event.edit(DELQUE)


@man_cmd(pattern="pause$", group_only=True)
async def vc_pause(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        try:
            await call_py.pause_stream(chat_id)
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
            await call_py.resume_stream(chat_id)
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
        return await edit_delete(event, f"**Maaf {me.first_name} Bukan Admin 👮**", 30)

    if chat_id in QUEUE:
        try:
            await call_py.change_volume_call(chat_id, volume=int(query))
            await edit_or_reply(
                event, f"**Berhasil Mengubah Volume Menjadi** `{query}%`"
            )
        except Exception as e:
            await edit_delete(event, f"**ERROR:** `{e}`", 30)
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern="playlist$", group_only=True)
async def vc_playlist(event):
    chat_id = event.chat_id
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await edit_or_reply(
                event,
                f"**🎧 Sedang Memutar:**\n• [{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][3]}`",
                link_preview=False,
            )
        else:
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


@call_py.on_stream_end()
async def stream_end_handler(_, u: Update):
    chat_id = u.chat_id
    await skip_current_song(chat_id)


@call_py.on_closed_voice_chat()
async def closedvc(_, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)


@call_py.on_left()
async def leftvc(_, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)


@call_py.on_kicked()
async def kickedvc(_, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)
    
