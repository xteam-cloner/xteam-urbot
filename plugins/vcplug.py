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

logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
FFMPEG_ABSOLUTE_PATH = "/usr/bin/ffmpeg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

logger.info("Memeriksa folder unduhan...")
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


# Asumsi: DOWNLOAD_DIR, FFMPEG_ABSOLUTE_PATH, dan logger sudah didefinisikan

async def ytdl(url: str) -> Tuple[int, Union[str, Any]]:
    """
    Mengunduh audio dari URL dan mengonversinya menjadi format Opus (untuk Voice Chat/VC)
    menggunakan yt-dlp dan FFmpeg, dijalankan secara sinkron di executor.
    
    Args:
        url (str): URL video/musik yang akan diunduh.
        
    Returns:
        Tuple[int, Union[str, Any]]: (1, path_file_akhir) jika sukses, 
                                     (0, pesan_error) jika gagal.
    """
    loop = asyncio.get_running_loop()
    
    # 1. Pastikan direktori unduhan ada
    if not os.path.isdir(DOWNLOAD_DIR):
        try:
            os.makedirs(DOWNLOAD_DIR)
        except OSError as e:
            return 0, f"Gagal membuat direktori unduhan: {e}"

    def vc_audio_dl_sync():
        """
        Fungsi sinkron untuk menjalankan yt-dlp. 
        Menggunakan postprocessor untuk memastikan output Opus.
        """
        
        ydl_opts_vc = {
            # outtmpl tanpa ekstensi, agar postprocessor menentukan ekstensi akhir
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s"), 
            "format": "bestaudio/best", # Unduh audio terbaik yang tersedia
            "noplaylist": True,
            "quiet": True,
            "nocheckcertificate": True,
            "prefer_ffmpeg": True,
            "exec_path": FFMPEG_ABSOLUTE_PATH,
            "js_runtimes": {
                "node": {},
            },
            # *** Postprocessor untuk Konversi ke Opus (OGG) ***
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "opus", # Codec target (standar untuk VC/OGG)
                    "preferredquality": "128", # Kualitas bitrate (bisa disesuaikan)
                },
                # Hapus metadata file (opsional)
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": False,
                },
            ],
        }

        # video_id digunakan untuk penanganan error dan pembersihan
        video_id = 'unknown' 
        
        try:
            x = yt_dlp.YoutubeDL(ydl_opts_vc)
            info = x.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            
            # Cari file akhir yang memiliki ekstensi .opus (yang dihasilkan oleh postprocessor)
            final_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(video_id) and f.endswith('.opus')]
            
            if not final_files:
                # Ini terjadi jika konversi FFmpeg gagal (misalnya, libopus tidak ada)
                logger.error(f"FFmpeg gagal membuat file Opus setelah processing untuk ID: {video_id}.")
                raise FileNotFoundError("Konversi Opus gagal. Pastikan FFMPEG_ABSOLUTE_PATH benar dan mendukung libopus.")
                
            final_link = os.path.join(DOWNLOAD_DIR, final_files[0])
            return final_link
            
        except Exception as e:
            logger.error(f"YTDL VC Error during sync operation: {e}", exc_info=True)
            
            # Bersihkan file sementara atau parsial yang gagal diunduh
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(video_id):
                    try:
                        os.remove(os.path.join(DOWNLOAD_DIR, f))
                    except OSError:
                        # Abaikan jika ada masalah penghapusan
                        pass 
            
            # Ulangi error agar dapat ditangkap oleh blok 'await' di luar
            raise 

    # 2. Jalankan fungsi sinkron di executor
    try:
        downloaded_file = await loop.run_in_executor(None, vc_audio_dl_sync)
        return 1, downloaded_file
    except Exception as e:
        # Menangkap error dari vc_audio_dl_sync
        return 0, f"Error saat mengunduh atau konversi: {e}"


        
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
        for song_data in QUEUE.get(chat_id, []):
            file_path = song_data[1]
            
            if os.path.exists(file_path):
                if DOWNLOAD_DIR in file_path or os.path.dirname(file_path) == os.getcwd():
                    try:
                        os.remove(file_path)
                        logger.info(f"Dihapus file di /end: {file_path}")
                    except Exception as e:
                        logger.error(f"Gagal menghapus file {file_path} di /end: {e}")
                    
        try:
            await call_py.leave_call(chat_id) 
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
        if chat_id in QUEUE and QUEUE[chat_id]:
            file_to_delete = QUEUE[chat_id][0][1]
            if os.path.exists(file_to_delete):
                try:
                    os.remove(file_to_delete)
                except Exception:
                    pass
        
        op = await skip_current_song(chat_id)
        if op == 0:
            await edit_delete(event, "**Tidak Sedang Memutar Streaming**")
        elif op == 1:
            await edit_delete(event, "antrian kosong, meninggalkan obrolan suara", time=10)
            
            try:
                await call_py.leave_call(chat_id) 
            except Exception:
                pass
            
        else:
            await edit_or_reply(
                event,
                f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar** - [{op[0]}]({op[2]})",
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
                    if x < len(QUEUE[chat_id]):
                        file_path_to_delete = QUEUE[chat_id][x][1]
                        if os.path.exists(file_path_to_delete):
                            try:
                                os.remove(file_path_to_delete)
                            except Exception:
                                pass
                                
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
