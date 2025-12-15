from __future__ import annotations
import asyncio
import os
import re
import contextlib 
import logging
import functools
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
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
from . import ultroid_cmd as man_cmd, eor as edit_or_reply, eod as edit_delete 
from youtubesearchpython import VideosSearch
from xteam import LOGS

from xteam.vcbot import QUEUE, add_to_queue, get_queue, pop_an_item, clear_queue 

logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
FFMPEG_ABSOLUTE_PATH = "/usr/bin/ffmpeg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

#logger.info("Memeriksa folder unduhan...")
if not os.path.isdir(DOWNLOAD_DIR):
    try:
        os.makedirs(DOWNLOAD_DIR)
        logger.info(f"Berhasil membuat folder unduhan: {DOWNLOAD_DIR}")
    except OSError as e:
        logger.error(f"Gagal membuat folder unduhan {DOWNLOAD_DIR}. Periksa izin: {e}")

def vcmention(user: TypeUser):
    full_name = get_display_name(user)
    if not isinstance(user, User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"

def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = data["thumbnails"][0]["url"]
        videoid = data["id"]
        return [songname, url, duration, thumbnail, videoid]
    except Exception as e:
        LOGS.info(str(e))
        return 0

async def ytdl(url: str, video_mode: bool = False) -> Tuple[int, Union[str, Any]]:
    loop = asyncio.get_running_loop()
    
    if not os.path.isdir(DOWNLOAD_DIR):
        try:
            os.makedirs(DOWNLOAD_DIR)
        except OSError as e:
            return 0, f"Gagal membuat direktori unduhan: {e}"

    def vc_audio_dl_sync():
        
        if video_mode:
            ydl_opts_vc = {
                "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": True,
                "nocheckcertificate": True,
                "prefer_ffmpeg": True,
                "exec_path": FFMPEG_ABSOLUTE_PATH,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4"
                    },
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": False,
                    },
                ],
            }
        else:
            ydl_opts_vc = {
                "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s"), 
                "format": "bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "nocheckcertificate": True,
                "prefer_ffmpeg": True,
                "exec_path": FFMPEG_ABSOLUTE_PATH,
                "js_runtimes": {
                    "node": {},
                },
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "opus",
                        "preferredquality": "128",
                    },
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": False,
                    },
                ],
            }
        
        video_id = 'unknown' 
        
        try:
            x = yt_dlp.YoutubeDL(ydl_opts_vc)
            info = x.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            
            if video_mode:
                target_ext = 'mp4'
            else:
                target_ext = 'opus'

            final_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(video_id) and f.endswith(f'.{target_ext}')]
            
            if not final_files:
                logger.error(f"FFmpeg gagal membuat file {target_ext.upper()} setelah processing untuk ID: {video_id}.")
                raise FileNotFoundError(f"Konversi {target_ext.upper()} gagal.")
                
            final_link = os.path.join(DOWNLOAD_DIR, final_files[0])
            return final_link
            
        except Exception as e:
            logger.error(f"YTDL VC Error during sync operation: {e}", exc_info=True)
            
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(video_id):
                    try:
                        os.remove(os.path.join(DOWNLOAD_DIR, f))
                    except OSError:
                        pass 
            
            raise 

    try:
        downloaded_file = await loop.run_in_executor(None, vc_audio_dl_sync)
        return 1, downloaded_file
    except Exception as e:
        return 0, f"Error saat mengunduh atau konversi: {e}"
                    
async def play_next_song(chat_id: int):
    finished_song_data = get_queue(chat_id)[0] if chat_id in QUEUE and QUEUE[chat_id] else None
    
    pop_an_item(chat_id)

    # Blok penghapusan file individual (os.remove) sudah dihapus di sini
    
    chat_queue = get_queue(chat_id)
    
    if chat_queue and len(chat_queue) > 0:
        next_song = chat_queue[0]
        songname, file_path, url_ref, media_type, resolution = next_song
        is_video = (media_type == "Video")
        
        try:
            video_quality = VideoQuality.HD_720p 

            stream = MediaStream(
                media_path=file_path,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=video_quality if is_video else VideoQuality.SD_480p,
                video_flags=MediaStream.Flags.REQUIRED if is_video else MediaStream.Flags.IGNORE,
            )
                
            await call_py.play(chat_id, stream)
            logger.info(f"Start the next song on {chat_id}: {songname}")
        
        except Exception as e:
            logger.error(
                f"Gagal memutar lagu berikutnya di {chat_id}: {e}. File: {file_path}", 
                exc_info=True
            )
            asyncio.create_task(play_next_song(chat_id)) 
            
    else:
        # PENTING: clear_queue bertanggung jawab membersihkan file disk sekarang.
        clear_queue(chat_id) 
        try:
            await call_py.leave_call(chat_id)
            logger.info(f"Antrian kosong, meninggalkan obrolan suara di {chat_id}")
        except Exception:
            pass
                                

@call_py.on_update()
async def stream_end_handler(client, update: Update):
    if isinstance(update, StreamEnded):
        chat_id = update.chat_id
        logger.info(f"Stream berakhir di {chat_id}. Memeriksa antrian...")
        asyncio.create_task(play_next_song(chat_id))


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
                await join_call(
                    chat_id,
                    link=ytlink,
                    video=False,
                )
                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                caption = f"🏷 **Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar`\n🎧 **Atas permintaan:** {from_user}"
                await botman.delete()
                return await event.client.send_file(
                    chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id
                )
            except UserAlreadyParticipantError:
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await botman.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await botman.edit(f"**ERROR:** `{ep}`")

    else:
        botman = await edit_or_reply(event, "📥 **Sedang Mendownload**")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
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
                await join_call(
                    chat_id,
                    link=dl,
                    video=False,
                )
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                caption = f"🏷 **Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n💡 **Status:** `Sedang Memutar Lagu`\n🎧 **Atas permintaan:** {from_user}"
                await event.client.send_file(
                    chat_id, fotoplay, caption=caption, reply_to=event.reply_to_msg_id
                )
                await botman.delete()
            except UserAlreadyParticipantError: 
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
        hm, ytlink = await ytdl(url, video_mode=True)

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
                await join_call(
                    chat_id,
                    link=ytlink,
                    video=True,
                    resolution=RESOLUSI,
                )
                add_to_queue(chat_id, songname, ytlink, url, "Video", RESOLUSI)
                return await xnxx.edit(
                    f"**🏷 Judul:** [{songname}]({url})\n**⏱ Durasi:** `{duration}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}",
                    link_preview=False,
                )
            except UserAlreadyParticipantError: 
                await call_py.leave_group_call(chat_id)
                clear_queue(chat_id)
                return await xnxx.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                clear_queue(chat_id)
                return await xnxx.edit(f"**ERROR:** `{ep}`")

    else:
        xnxx = await edit_or_reply(event, "📥 **Sedang Mendownload**")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
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
                await join_call(
                    chat_id,
                    link=dl,
                    video=True,
                    resolution=RESOLUSI,
                )
                add_to_queue(chat_id, songname, dl, link, "Video", RESOLUSI)
                caption = f"🏷 **Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n💡 **Status:** `Sedang Memutar Video`\n🎧 **Atas permintaan:** {from_user}"
                await xnxx.delete()
                return await event.client.send_file(
                    chat_id, fotoplay, caption=caption, reply_to=event.reply_to_msg_id
                )
            except UserAlreadyParticipantError: 
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
        clear_queue(chat_id) 
        try:
            await call_py.leave_call(chat_id) 
            await edit_or_reply(event, "**Menghentikan Streaming**")
        except Exception as e:
            await edit_delete(event, f"**ERROR:** `{e}`")
    else:
        await edit_delete(event, "**Tidak Sedang Memutar Streaming**")


@man_cmd(pattern="skip(?:\s|$)([\s\S]*)", group_only=True)
async def vc_skip(event):
    chat_id = event.chat_id
    
    if len(event.text.split()) < 2:
        
        if chat_id not in QUEUE or not QUEUE[chat_id]:
            return await edit_delete(event, "**Tidak Sedang Memutar Streaming**")
        
        await play_next_song(chat_id) 

        chat_queue = get_queue(chat_id)
        if chat_queue and len(chat_queue) > 0:
            op = chat_queue[0]
            await edit_or_reply(
                event,
                f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar** - [{op[0]}]({op[2]})",
                link_preview=False,
            )
        else:
            await edit_delete(event, "Antrian kosong, meninggalkan obrolan suara", time=10)
            
    else:
        skip = event.text.split(maxsplit=1)[1]
        DELQUE = "**Menghapus Lagu Berikut Dari Antrian:**"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            
            cleaned_list = []
            
            for x in items:
                if x > 0 and x < len(QUEUE[chat_id]):
                    file_path_to_delete = QUEUE[chat_id][x][1]
                    song_name = QUEUE[chat_id][x][0]
                    
                    QUEUE[chat_id].pop(x) 
                    
                    if os.path.exists(file_path_to_delete):
                        with contextlib.suppress(Exception):
                            os.remove(file_path_to_delete)
                            logger.info(f"Dihapus file di /skip #{x}: {file_path_to_delete}")
                    
                    cleaned_list.append(f"**#{x}** - {song_name}")
            
            if cleaned_list:
                await event.edit(DELQUE + "\n" + "\n".join(cleaned_list))
            else:
                await edit_delete(event, "**Nomor antrian tidak valid.**", time=10)


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
