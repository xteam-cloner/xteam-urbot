# vctools.py - Plugin Musik VC Ultroid (Menggunakan Class Manager)

from __future__ import annotations

import asyncio
import os
import re
import contextlib 
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

import httpx

# 🚨 IMPOR UTAMA ULTROID
from . import * 
from telethon import events, TelegramClient, Button
from telethon.tl.types import Message, User
from xteam.configs import Var 
from xteam import call_py # PyTgCalls Client
from xteam import ultroid_bot 
from telethon.utils import get_display_name
from xteam.fns.admins import admin_check
# 🚨 IMPOR PYTGCALLS
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    ChatUpdate,
    MediaStream,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
    AudioQuality,
    VideoQuality,
)
# 🚨 IMPOR TELETHON LAINNYA (diasumsikan sudah diimpor oleh 'from . import *')
# Namun, untuk kejelasan, kita pertahankan:
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import LeaveChannelRequest

import yt_dlp
from youtubesearchpython.__future__ import VideosSearch

from . import ultroid_cmd
logger = logging.getLogger(__name__)

# --- KONSTANTA & KONFIGURASI ---
fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
# Asumsi utilitas Ultroid lainnya:
Config = Var # Asumsi konfigurasi ada di Var
#HNDLR = Var.HNDLR
# --------------------------------
# Di vcplug.py (Tambahkan ini di bagian atas, di bawah impor)

from telethon.errors.rpcerrorlist import (
    UserNotParticipantError,
    UserAlreadyParticipantError
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from xteam.configs import Var # Asumsi ASSISTANT_ID ada di Var


import functools

def is_admin(func):
    @functools.wraps(func)
    async def a_c(event):
        is_admin = False
        if not event.is_private:
            try:
                _s = await event.client.get_permissions(event.chat_id, event.sender_id)
                if _s.is_admin:
                    is_admin = True
            except:
                is_admin = False
        if is_admin:
            await func(event, _s)
        else:
            await event.reply("Only Admins can execute this command!")
    return a_c
# Dapatkan ID asisten dari konfigurasi
ASSISTANT_ID = Var.ASSISTANT_ID # Ganti Var dengan sumber config yang benar!

def AssistantAdd(mystic):
    async def wrapper(event):
        try:
            # Gunakan event.client untuk mengambil izin
            permissions = await event.client.get_permissions(int(event.chat_id), int(ASSISTANT_ID))
        except UserNotParticipantError:
            if event.is_group:
                try:
                    # Gunakan event.client untuk mengambil dan mengimpor link
                    link = await event.client(ExportChatInviteRequest(event.chat_id))
                    invitelinkk = link.link
                    invitelink = invitelinkk.replace("https://t.me/+", "")
                    
                    # Gunakan event.client untuk bergabung sebagai bot
                    await event.client(ImportChatInviteRequest(invitelink)) 
                    await event.reply(
                        f"Joined Successfully",
                    )
                except UserAlreadyParticipantError:
                    pass
                except Exception as e:
                    await event.reply(
                        f"__Assistant Failed To Join__\n\n**Reason**: {e}"
                    )
                    return
        return await mystic(event)

    return wrapper

# ... Lanjutkan dengan @ultroid_cmd(pattern="play")

# ─────────────────────────────────────────────────────────────
# Queue/State Models (DIINTEGRASIKAN KEMBALI)
# ─────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    source: str  # URL atau Local Path
    link: str    # URL asli (YouTube) atau link T.me untuk file
    type: str    # Audio / Video
    resolution: int # Resolusi untuk video
    requested_by: User
    
class Queue:
    # Diganti dengan list yang lebih sederhana untuk mendukung pop(index)
    def __init__(self):
        self._q: list[Track] = []
    def push(self, t: Track):
        self._q.append(t)
    def pop(self) -> Optional[Track]:
        return self._q.pop(0) if self._q else None
    def pop_at(self, index: int) -> Optional[Track]:
        try:
            return self._q.pop(index)
        except IndexError:
            return None
    def as_list(self):
        return list(self._q)
    def clear(self):
        self._q.clear()
    def __len__(self):
        return len(self._q)

class VCState:
    def __init__(self):
        self.queue = Queue()
        self.now_playing: Optional[Track] = None
        self.lock = asyncio.Lock()
        self.volume = 100

# ─────────────────────────────────────────────────────────────
# VC Manager (DIINTEGRASIKAN KEMBALI)
# ─────────────────────────────────────────────────────────────

class VCManager:
    def __init__(self, tgcalls_client: PyTgCalls):
        self.tgcalls = tgcalls_client 
        self.states: Dict[int, VCState] = {}
        # self.resolver = YouTubeResolver() # Resolver bisa di luar manager
        
        # 🌟 Setup Event Handlers PyTgCalls
        @self.tgcalls.on_stream_end()
        async def on_end(_, update):
            await self._on_track_end(update.chat_id)

        @self.tgcalls.on_closed_voice_chat()
        async def closedvc(_, chat_id: int):
            self.states.pop(chat_id, None)

        @self.tgcalls.on_left()
        @self.tgcalls.on_kicked()
        async def left_kicked_vc(_, chat_id: int):
            self.states.pop(chat_id, None)


    def state(self, chat_id: int) -> Optional[VCState]:
        return self.states.get(chat_id)

    def get_or_create_state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

    async def leave(self, chat_id: int):
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        self.states.pop(chat_id, None)

    async def play(self, chat_id: int, track: Track):
        st = self.get_or_create_state(chat_id)
        async with st.lock:
            if st.now_playing is None:
                await self._start_stream(chat_id, track)
            else:
                st.queue.push(track)
                # Return posisi queue (index terakhir + 1, karena 0 adalah now_playing)
                return len(st.queue.as_list()) 
        return 1 # Jika langsung dimainkan (posisi 1 di queue virtual)


    def _build_stream(self, track: Track) -> MediaStream:
        gain_db = 6.0 * (track.resolution / 100.0 - 1.0) # Menggunakan resolution sebagai volume
        
        is_local = os.path.exists(track.source)
        
        if track.type == "Audio":
            # Audio Piped
            return AudioPiped(
                track.source,
                stream_type=StreamType().pulse_stream,
                additional_ffmpeg_parameters=["-af", f"volume={gain_db}dB"],
            )
        else: # Video
            # Video Piped
            if track.resolution == 720:
                vid_qual = HighQualityVideo()
            elif track.resolution == 480:
                vid_qual = MediumQualityVideo()
            elif track.resolution == 360:
                vid_qual = LowQualityVideo()
            else:
                vid_qual = HighQualityVideo() # Default
            
            return AudioVideoPiped(
                track.source, 
                HighQualityAudio(), 
                vid_qual,
                stream_type=StreamType().pulse_stream,
                additional_ffmpeg_parameters=["-af", f"volume={gain_db}dB"],
            )

    async def _start_stream(self, chat_id: int, track: Track):
        st = self.get_or_create_state(chat_id)
        st.now_playing = track
        stream = self._build_stream(track)
        
        try:
            await self.tgcalls.join_group_call(chat_id, stream)
        except Exception:
            await self.tgcalls.change_stream(chat_id, stream)

    async def _on_track_end(self, chat_id: int):
        st = self.state(chat_id)
        if not st: return
        
        async with st.lock:
            nxt = st.queue.pop()
            if nxt:
                await self._start_stream(chat_id, nxt)
                return nxt
            else:
                st.now_playing = None
                with contextlib.suppress(Exception):
                    await self.tgcalls.leave_group_call(chat_id)
                self.states.pop(chat_id, None) # Hapus state jika queue kosong
                return None

    async def pause(self, chat_id: int):
        await self.tgcalls.pause_stream(chat_id)

    async def resume(self, chat_id: int):
        await self.tgcalls.resume_stream(chat_id)

    async def skip_item(self, chat_id: int, index: int) -> Optional[str]:
        st = self.state(chat_id)
        if not st: return None
        
        removed_track = st.queue.pop_at(index - 1) # index 1 di command = index 0 di list
        return removed_track.title if removed_track else None


# Singleton manager
_vc: Optional[VCManager] = None

def _manager(e) -> VCManager:
    global _vc, call_py
    
    if not isinstance(call_py, PyTgCalls):
        raise RuntimeError("VC Client (PyTgCalls) belum siap atau VCBOT dinonaktifkan.")
        
    if _vc is None:
        _vc = VCManager(call_py)
    return _vc

# ─────────────────────────────────────────────────────────────
# Utils (DIIMPOR/DIPERBAIKI)
# ─────────────────────────────────────────────────────────────

def vcmention(user):
    full_name = get_display_name(user)
    if not isinstance(user, User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"


def ytsearch(query: str):
    try:
        # Menggunakan async VideosSearch dari yt_dlp
        search = ultroid_bot.loop.run_until_complete(VideosSearch(query, limit=1).next())
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
        videoid = data["id"]
        return [songname, url, duration, thumbnail, videoid]
    except Exception as e:
        logger.error(f"YouTube Search Error: {e}")
        return 0


async def ytdl(format: str, link: str):
    # Menggunakan fungsi bash Ultroid
    stdout, stderr = await bash(f'yt-dlp -g -f "{format}" {link}')
    if stdout:
        return 1, stdout.split("\n")[0]
    return 0, stderr


# Skip diubah menjadi metode di VCManager
# async def skip_item(chat_id: int, x: int): ... (Dihapus/Diganti)


async def skip_current_song(chat_id: int):
    # Logika skip diubah ke manager
    manager = _manager(None) # None karena tidak pakai event
    st = manager.state(chat_id)
    if not st: return 0
    
    # Ambil lagu berikutnya (indeks 0 di queue)
    next_track = st.queue.as_list()[0] if st.queue.as_list() else None
    
    if st.now_playing and not next_track:
        # Hanya 1 lagu, tinggalkan VC
        await manager.leave(chat_id)
        return 1
    elif next_track:
        # Ada lagu berikutnya
        await manager._start_stream(chat_id, next_track)
        st.queue.pop() # Hapus dari queue karena sudah dimainkan
        return [next_track.title, next_track.link, next_track.type]
    
    return 0


# ─────────────────────────────────────────────────────────────
# Commands (MENGGANTI @Zaid.on DENGAN @ultroid_cmd)
# ─────────────────────────────────────────────────────────────

btnn =[[Button.inline("✯ cʟᴏꜱᴇ ✯", data="cls")]]

@ultroid_cmd(pattern="cls")
async def _(event):
     await event.delete()


@ultroid_cmd(pattern="play(?: (.+))?", allow_sudo=True, groups_only=True)
@AssistantAdd
async def play(event):
    chat_id = event.chat_id
    from_user = vcmention(event.sender) 
    manager = _manager(event)
    st = manager.get_or_create_state(chat_id)
    
    query = event.pattern_match.group(1)
    replied = await event.get_reply_message()

    if not replied and not query:
        return await event.client.send_file(chat_id, Config.CMD_IMG, caption="**Give Me Your Query Which You want to Play**\n\n **Example**: `{}play Nira Ishq Bass boosted`".format(HNDLR), buttons=btnn)

    botman = await event.reply("🔎")
    
    if query:
        search = ytsearch(query)
        if search == 0:
            return await botman.edit("**Can't Find Song** Try searching with More Specific Title")     
        
        songname, url, duration, thumbnail, videoid = search
        sender = await event.get_sender()
        thumb = await gen_thumb(videoid)
        format = "bestaudio[ext=m4a]" # Format audio terbaik
        hm, ytlink = await ytdl(format, url)
        
        if hm == 0:
            return await botman.edit(f"`{ytlink}`")

        new_track = Track(songname, ytlink, url, "Audio", st.volume, sender)
        
        if st.now_playing:
            pos = await manager.play(chat_id, new_track)
            caption = f"✨ **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await botman.delete()
            await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
        else:
            try:
                await manager._start_stream(chat_id, new_track)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
            except Exception as ep:
                st.now_playing = None
                st.queue.clear()
                await botman.edit(f"`{ep}`")
    
    elif replied and (replied.audio or replied.voice):
        await botman.edit("➕ Downloading File...")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
        link = f"https://t.me/c/{chat_id}/{replied.id}"
        songname = "Telegram Music Player" if replied.audio else "Voice Note"
        sender = await event.get_sender()

        new_track = Track(songname, dl, link, "Audio", st.volume, sender)
        
        if st.now_playing:
            pos = await manager.play(chat_id, new_track)
            caption = f"✨ **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await botman.delete()
            await event.client.send_file(chat_id, ngantri, caption=caption, buttons=btnn)
        else:
            try:
                await manager._start_stream(chat_id, new_track)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, fotoplay, caption=caption, buttons=btnn)
            except Exception as ep:
                st.now_playing = None
                st.queue.clear()
                await botman.edit(f"`{ep}`")

    else:
        return await botman.edit("Invalid input or replied media. Need query or audio/voice reply.")


@ultroid_cmd(pattern="end$", allow_sudo=True, groups_only=True)
@is_admin
async def vc_end(event, perm):
    chat_id = event.chat_id
    manager = _manager(event)
    st = manager.state(chat_id)
    
    if st and st.now_playing:
        await manager.leave(chat_id)
        await event.reply(f"**Streaming Ended**")
    else:
        await event.reply("**Ntg is playing ~**")


@ultroid_cmd(pattern="vplay(?: (.+))?", allow_sudo=True, groups_only=True)
@AssistantAdd
async def vplay(event):
    chat_id = event.chat_id
    from_user = vcmention(event.sender)
    manager = _manager(event)
    st = manager.get_or_create_state(chat_id)

    if Var.HEROKU_MODE == "ENABLE":
        await event.reply("__Currently Heroku Mode is ENABLED so You Can't Stream Video because Video Streaming Cause of Banning Your Heroku Account__.")
        return

    query = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    
    if not replied and not query:
        return await event.client.send_file(chat_id, Config.CMD_IMG, caption="**Give Me Your Query Which You want to Stream**\n\n **Example**: `{}vplay Nira Ishq Bass boosted`".format(HNDLR), buttons=btnn)

    xnxx = await event.reply("**🔄 Processing Query... Please Wait!**")
    
    RESOLUSI = 720 # Default

    if query:
        search = ytsearch(query)
        if search == 0:
            return await xnxx.edit("**Can't Find Song** Try searching with More Specific Title")
        
        songname, url, duration, thumbnail, videoid = search
        thumb = await gen_thumb(videoid)
        format = "best[height<=?720][width<=?1280]"
        hm, ytlink = await ytdl(format, url)
        
        if hm == 0:
            return await xnxx.edit(f"`{ytlink}`")
            
        sender = await event.get_sender()
        new_track = Track(songname, ytlink, url, "Video", RESOLUSI, sender)

        if st.now_playing:
            pos = await manager.play(chat_id, new_track)
            caption = f"**✨ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await xnxx.delete()
            await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
        else:
            try:
                await manager._start_stream(chat_id, new_track)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await xnxx.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
            except Exception as ep:
                st.now_playing = None
                st.queue.clear()
                await xnxx.edit(f"`{ep}`")
    
    elif replied and (replied.video or replied.document):
        if len(event.text.split()) > 1 and event.text.split()[1].isdigit():
             RESOLUSI = int(event.text.split()[1])
        
        await xnxx.edit("➕ **Downloading Replied File**")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
        link = f"https://t.me/c/{chat_id}/{replied.id}"
        songname = "Telegram Video Player"
        sender = await event.get_sender()
        
        new_track = Track(songname, dl, link, "Video", RESOLUSI, sender)

        if st.now_playing:
            pos = await manager.play(chat_id, new_track)
            caption = f"**✨ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await xnxx.delete()
            await event.client.send_file(chat_id, ngantri, caption=caption, buttons=btnn)
        else:
            try:
                await manager._start_stream(chat_id, new_track)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n✨ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await xnxx.delete()
                await event.client.send_file(chat_id, fotoplay, caption=caption, buttons=btnn)
            except Exception as ep:
                st.now_playing = None
                st.queue.clear()
                await xnxx.edit(f"`{ep}`")
    
    else:
        return await xnxx.edit("Invalid input or replied media. Need query or video/document reply.")


@ultroid_cmd(pattern="playlist$", allow_sudo=True, groups_only=True)
@is_admin
async def vc_playlist(event, perm):
    chat_id = event.chat_id
    st = _manager(event).state(chat_id)
    
    if not st or not st.now_playing:
        return await event.reply("**Ntg is Streaming**")
        
    np = st.now_playing
    queue_list = st.queue.as_list()
    
    PLAYLIST = f"**🎧 PLAYLIST:**\n**• [{np.title}]({np.link})** | `{np.type}` \n\n**• Upcoming Streaming ({len(queue_list)}):**"
    
    for x, track in enumerate(queue_list):
        PLAYLIST += f"\n**#{x+1}** - [{track.title}]({track.link}) | `{track.type}`"
        
    await event.reply(PLAYLIST, link_preview=False)


@ultroid_cmd(pattern="leavevc$", allow_sudo=True, groups_only=True)
@is_admin
async def leavevc(event, perm):
    xnxx = await event.reply("Processing")
    chat_id = event.chat_id
    
    manager = _manager(event)
    st = manager.state(chat_id)
    
    if st:
        await manager.leave(chat_id)
        await xnxx.edit(f"**Left the voice chat** `{chat_id}`")
    else:
        await xnxx.edit(f"**I am not on Voice Chat**")


@ultroid_cmd(pattern="skip(?: (.+))?", allow_sudo=True, groups_only=True)
@is_admin
async def vc_skip(event, perm):
    chat_id = event.chat_id
    manager = _manager(event)
    st = manager.state(chat_id)
    
    if not st or not st.now_playing:
        return await event.reply("**Nothing Is Streaming**")

    arg = event.pattern_match.group(1)
    
    if not arg:
        # Skip current song (0)
        next_track = await manager._on_track_end(chat_id)
        if next_track is None:
            await event.reply("empty queue, leaving voice chat")
        else:
            await event.reply(
                f"**⏭ Skipped**\n**🎧 Now Playing** - [{next_track.title}]({next_track.link})",
                link_preview=False,
            )
    else:
        skip_indices = [int(x) for x in arg.split(" ") if x.isdigit()]
        skip_indices.sort(reverse=True) # Hapus dari belakang untuk menghindari perubahan indeks
        DELQUE = "**Removing Following Songs From Queue:**"
        removed = False

        for x in skip_indices:
            if x > 0:
                hm = await manager.skip_item(chat_id, x)
                if hm:
                    DELQUE += "\n" + f"**#{x}** - {hm}"
                    removed = True
        
        if removed:
            await event.reply(DELQUE)
        else:
            await event.reply("**No valid songs skipped from queue.**")


@ultroid_cmd(pattern="pause$", allow_sudo=True, groups_only=True)
@is_admin
async def vc_pause(event, perm):
    chat_id = event.chat_id
    manager = _manager(event)

    if manager.state(chat_id):
        try:
            await manager.pause(chat_id)
            await event.reply("**Streaming Paused**")
        except Exception as e:
            await event.reply(f"**ERROR:** `{e}`")
    else:
        await event.reply("**Nothing Is Playing**")


@ultroid_cmd(pattern="resume$", allow_sudo=True, groups_only=True)
@is_admin
async def vc_resume(event, perm):
    chat_id = event.chat_id
    manager = _manager(event)

    if manager.state(chat_id):
        try:
            await manager.resume(chat_id)
            await event.reply("**Streaming Started Back 🔙**")
        except Exception as e:
            await event.reply(f"**ERROR:** `{e}`")
    else:
        await event.reply("**Nothing Is Streaming**")

               
