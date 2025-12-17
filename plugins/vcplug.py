from __future__ import annotations
import asyncio
import os
import re
import contextlib 
import logging
import functools
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
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors.rpcerrorlist import (
    UserNotParticipantError,
    UserAlreadyParticipantError
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
import yt_dlp
from youtubesearchpython.__future__ import VideosSearch
from . import ultroid_cmd as man_cmd, eor as edit_or_reply, eod as edit_delete, callback
from youtubesearchpython import VideosSearch
from xteam import LOGS
from xteam.vcbot import CHAT_TITLE, skip_current_song, skip_item, play_next_stream, add_to_queue, gen_thumb, ytsearch, join_call 
from xteam.vcbot.queues import pop_an_item, QUEUE, clear_queue, get_queue


logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
FFMPEG_ABSOLUTE_PATH = "/usr/bin/ffmpeg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
COOKIES_FILE_PATH = "cookies.txt"



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
                "cookiefile": COOKIES_FILE_PATH,
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
                "cookiefile": COOKIES_FILE_PATH,
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
    from xteam import call_py
    
    if chat_id not in QUEUE or not QUEUE[chat_id]:
        LOGS.info(f"Queue is empty, leaving voice chat {chat_id}")
        if call_py:
            try:
                await call_py.leave_call(chat_id)
            except Exception:
                pass
        clear_queue(chat_id)
        return None
    
    QUEUE[chat_id].pop(0)

    if not QUEUE[chat_id]:
        LOGS.info(f"No more songs in queue for {chat_id}, leaving...")
        if call_py:
            try:
                await call_py.leave_call(chat_id)
            except Exception:
                pass
        clear_queue(chat_id)
        return None

    try:
        next_song = QUEUE[chat_id][0] 
        songname, url, link, type, RESOLUSI = next_song
    except IndexError:
        return None

    LOGS.info(f"Start the next song on {chat_id}: {songname}")

    if type == "Audio":
        stream = MediaStream(
            media_path=url,
            audio_parameters=AudioQuality.HIGH, 
            audio_flags=MediaStream.Flags.REQUIRED, 
            video_flags=MediaStream.Flags.IGNORE,
        )
    elif type == "Video":
        video_quality = (
            VideoQuality.HD_720p if RESOLUSI == 720 else
            VideoQuality.SD_480p if RESOLUSI == 480 else
            VideoQuality.SD_360p if RESOLUSI == 360 else
            VideoQuality.SD_480p
        )
        stream = MediaStream(
            media_path=url,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=video_quality,
            audio_flags=MediaStream.Flags.REQUIRED, 
            video_flags=MediaStream.Flags.REQUIRED,
        )

    if not call_py:
        LOGS.error("call_py is None! Cannot play next song.")
        return None

    try:
        await call_py.play(chat_id, stream)
        try:
            await call_py.mute(chat_id, is_muted=False)
        except Exception:
            pass
        return [songname, link, type]
    except Exception as e:
        LOGS.error(f"Error playing next stream in {chat_id}: {e}")
        return None
        
    

@man_cmd(pattern=r"(play|vplay)\b", group_only=True)
async def vc_stream(event):
    command_type = event.pattern_match.group(1) 
    is_video = (command_type == 'vplay')
    RESOLUSI = 720 if is_video else 0
    MODE_TYPE = "Video" if is_video else "Audio"
    try:
        title_match = event.text.split(maxsplit=1)[1]
    except IndexError:
        title_match = "" 
    replied = await event.get_reply_message()
    chat = await event.get_chat()
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    asstUserName = asst.me.username
    try:
        await event.client(InviteToChannelRequest(chat_id, [asstUserName]))
    except (UserAlreadyParticipantError, UserPrivacyRestrictedError, ChatAdminRequiredError):
        pass
    except Exception as e:
        logger.error(f"Gagal mengundang bot asisten: {e}") 
        sender_client = asst if event.is_group else event.client
    if not replied or (replied and not valid_replies):

        xteambot = await edit_or_reply(event, f"`Searching {MODE_TYPE}...`")
        query = title_match
        search = ytsearch(query)
        
        if search == 0:
            return await xteambot.edit(f"**Tidak Dapat Menemukan {MODE_TYPE}** Coba cari dengan Judul yang Lebih Spesifik")
        
        songname, url, duration, thumbnail, videoid = search
        ctitle = await CHAT_TITLE(chat.title)
        thumb = await gen_thumb(thumbnail, songname, videoid, ctitle)
        
        stream_link_info = await ytdl(url, video_mode=is_video) 
        hm, stream_link = stream_link_info if isinstance(stream_link_info, tuple) else (0, stream_link_info)
        
        if hm == 0:
            return await xteambot.edit(f"`{stream_link}`")

        # Antrian Sudah Ada
        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, stream_link, url, MODE_TYPE, RESOLUSI) 
            caption = f"💡 **{MODE_TYPE} Added to queue »** `#{pos}`\n\n**🏷 Title:** [{songname}]({url})\n**⏱ Duration :** `{duration}`\n🎧 **Request By:** {from_user}"
            await xteambot.delete()
            return await asst.send_file(
                chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id
            )
        else:
            try:
                await join_call(
                    chat_id,
                    link=stream_link,
                    video=is_video,
                    resolution=RESOLUSI if is_video else 0,
                )
                add_to_queue(chat_id, songname, stream_link, url, MODE_TYPE, RESOLUSI)
                caption = f"🎧 Now Playing!\n\n🏷 **Title :** [{songname}]({url})\n**⏱ Duration :** `{duration}`\n🎧 **Request By:** {from_user}"
                await xteambot.delete()
                return await event.client.send_file(
                    chat_id, thumb, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS
                )
            except UserAlreadyParticipantError:
                if os.path.exists(stream_link):
                    with contextlib.suppress(Exception):
                        os.remove(stream_link)
                        
                await call_py.leave_call(chat_id)
                clear_queue(chat_id)
                return await xteambot.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                if os.path.exists(stream_link):
                    with contextlib.suppress(Exception):
                        os.remove(stream_link)
                        
                clear_queue(chat_id)
                return await xteambot.edit(f"**ERROR:** `{ep}`")
    else:
        xteambot = await edit_or_reply(event, f"📥 **Sedang Mendownload {MODE_TYPE}**")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
        link = f"https://t.me/c/{chat_id}/{event.reply_to_msg_id}"
        songname = f"Telegram {MODE_TYPE} Player"
        
        if is_video and title_match:
            res_match = re.search(r'\b(\d{3,4})\b', title_match)
            if res_match:
                try:
                    RESOLUSI = int(res_match.group(1))
                except ValueError:
                    pass

        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl, link, MODE_TYPE, RESOLUSI)
            caption = f"💡 **{MODE_TYPE} Ditambahkan Ke antrian »** `#{pos}`\n\n**🏷 Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n🎧 **Atas permintaan:** {from_user}"
            
            thumbnail_file = ngantri if not is_video else fotoplay 
            
            await event.client.send_file(
                chat_id, thumbnail_file, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS
            )
            await xteambot.delete()
            
        # Memutar Sekarang
        else:
            try:
                await join_call(
                    chat_id,
                    link=dl,
                    video=is_video,
                    resolution=RESOLUSI if is_video else 0,
                )
                add_to_queue(chat_id, songname, dl, link, MODE_TYPE, RESOLUSI)
                caption = f"🏷 **Judul:** [{songname}]({link})\n**👥 Chat ID:** `{chat_id}`\n💡 **Status:** `Sedang Memutar {MODE_TYPE}`\n🎧 **Atas permintaan:** {from_user}"
                
                thumbnail_file = fotoplay 
                
                await xteambot.delete()
                return await event.client.send_file(
                    chat_id, thumbnail_file, caption=caption, reply_to=event.reply_to_msg_id, buttons=MUSIC_BUTTONS
                )
            except UserAlreadyParticipantError: 
                if os.path.exists(dl):
                    with contextlib.suppress(Exception):
                        os.remove(dl)
                        
                await call_py.leave_call(chat_id)
                clear_queue(chat_id)
                return await xteambot.edit("**ERROR:** `Karena akun sedang berada di obrolan suara`\n\n• Silahkan Coba Play lagi")
            except Exception as ep:
                if os.path.exists(dl):
                    with contextlib.suppress(Exception):
                        os.remove(dl)
                        
                clear_queue(chat_id)
                return await xteambot.edit(f"**ERROR:** `{ep}`")

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


@man_cmd(pattern="skip", group_only=True)
async def vc_skip(event):
    chat_id = event.chat_id
    
    full_command = event.text.split(maxsplit=1)
    
    if len(full_command) > 1:
        skip = full_command[1]
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
        
        return
            
    else:
        if chat_id not in QUEUE or not QUEUE[chat_id]:
            return await edit_delete(event, "**Tidak Sedang Memutar Streaming**")
        
        result = await play_next_song(chat_id) 

        if result is None:
            return await edit_delete(event, "Antrian kosong, meninggalkan obrolan suara", time=10)
        
        songname, link, type = result
        
        await edit_or_reply(
            event,
            f"**⏭ Melewati Lagu**\n**🎧 Sekarang Memutar** - [{songname}]({link})",
            link_preview=False,
                            )
        

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


@man_cmd(pattern="clean$", group_only=True)
async def clean_disk(event):
    if not os.path.isdir(DOWNLOAD_DIR):
        return await edit_or_reply(event, "Folder unduhan tidak ditemukan.")
    
    files = os.listdir(DOWNLOAD_DIR)
    
    if not files:
        return await edit_or_reply(event, "Folder unduhan sudah kosong.")

    deleted_count = 0
    for file_name in files:
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        # HINDARI MENGHAPUS DIREKTORI, HANYA FILE
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception:
                pass # Abaikan error jika gagal menghapus
    
    return await edit_or_reply(event, 
        f"✅ **Pembersihan Selesai:** Berhasil menghapus **{deleted_count}** file media dari folder unduhan (`{DOWNLOAD_DIR}`)."
    )



MUSIC_BUTTONS = [
    [
        Button.inline("⏸ PAUSE", data="pauseit"),
        Button.inline("▶️ RESUME", data="resumeit")
    ],
    [
        Button.inline("⏭ SKIP", data="skipit"),
        Button.inline("⏹ STOP", data="stopit")
    ],
    [
        Button.inline("🗑 CLOSE", data="closeit")
    ]
]


@callback(data=re.compile(b"(pauseit|resumeit|stopit|skipit|closeit)"), owner=True)
async def music_manager(e):
    query = e.data.decode("utf-8")
    chat_id = e.chat_id
    try:
        if query == "pauseit":
            await call_py.pause_stream(chat_id)
            await e.answer("⏸ Paused", alert=False)
        elif query == "resumeit":
            await call_py.resume_stream(chat_id)
            await e.answer("▶️ Resumed", alert=False)
        elif query == "stopit":
            await call_py.leave_group_call(chat_id)
            await e.delete()
        elif query == "skipit":
            await call_py.drop_user(chat_id)
            await e.answer("⏭ Skipped", alert=False)
        elif query == "closeit":
            await e.delete()
    except Exception as err:
        await e.answer(f"⚠️ Error: {str(err)}", alert=True)
