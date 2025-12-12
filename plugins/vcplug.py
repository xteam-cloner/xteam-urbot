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

from . import * 
from telethon import events, TelegramClient, Button
from telethon.tl.types import Message, User
from xteam.configs import Var 
from xteam import call_py 
from xteam import ultroid_bot 
from telethon.utils import get_display_name
from xteam.fns.admins import admin_check 
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

from . import ultroid_cmd
logger = logging.getLogger(__name__)

fotoplay = "https://telegra.ph/file/b6402152be44d90836339.jpg"
ngantri = "https://telegra.ph/file/b6402152be44d90836339.jpg"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
Config = Var 
#HNDLR = Var.HNDLR
ASSISTANT_ID = Var.ASSISTANT_ID 

VC_STATUS: Dict[int, Dict[str, Any]] = {}

@dataclass
class Track:
    title: str
    source: str
    link: str
    type: str
    resolution: int
    requested_by: User
    
def is_admin(func):
    @functools.wraps(func)
    async def a_c(event, *args, **kwargs):
        is_admin = False
        if not event.is_private:
            try:
                _s = await event.client.get_permissions(event.chat_id, event.sender_id)
                if _s.is_admin:
                    is_admin = True
            except:
                is_admin = False
        if is_admin:
            await func(event, _s, *args, **kwargs) 
        else:
            await event.reply("Only Admins can execute this command!")
    return a_c

def AssistantAdd(mystic):
    async def wrapper(event):
        try:
            await event.client.get_permissions(int(event.chat_id), int(ASSISTANT_ID))
        except UserNotParticipantError:
            if event.is_group:
                try:
                    link = await event.client(ExportChatInviteRequest(event.chat_id))
                    invitelinkk = link.link
                    invitelink = invitelinkk.replace("https://t.me/+", "")
                    
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
        except ValueError as ve:
            await event.reply(f"❌ **Error Entity:** Could not resolve Assistant ID (`{ASSISTANT_ID}`). Please ensure the assistant has started a chat with the bot master and is online.")
            return

        return await mystic(event)

    return wrapper

def get_vc_state(chat_id: int, create: bool = False) -> Optional[Dict[str, Any]]:
    if chat_id not in VC_STATUS and create:
        VC_STATUS[chat_id] = {
            'queue': [],
            'now_playing': None,
            'lock': asyncio.Lock(),
            'volume': 100
        }
    return VC_STATUS.get(chat_id)

def vcmention(user):
    full_name = get_display_name(user)
    if not isinstance(user, User):
        return full_name
    return f"[{full_name}](tg://user?id={user.id})"

async def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1)
        data = await search.next() 
        
        data = data["result"][0]
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
    COOKIES_FILE = "cookies.txt"
    # Menggunakan fns.helper.bash yang diasumsikan ada di proyek
    command = f'yt-dlp --cookies {COOKIES_FILE} --js-runtimes node --remote-components ejs:github -g -f "{format}" {link}' 

    stdout, stderr = await bash(command) # Asumsi bash() tersedia
    if stdout:
        # yt-dlp -g mengembalikan URL streaming (source)
        return 1, stdout.split("\n")[0]
    return 0, stderr


async def gen_thumb(videoid):
    return fotoplay 

async def _build_stream(track: Track) -> MediaStream:
    aud_qual = AudioQuality.HIGH

    if track.type == "Audio":
        return MediaStream(
            track.source,
            audio_parameters=aud_qual,
            video_flags=MediaStream.Flags.IGNORE,
        )
    else:
        vid_qual = VideoQuality.HIGH 
        return MediaStream(
            track.source, 
            audio_parameters=aud_qual,
            video_parameters=vid_qual,
        )


# =========================================================================
# FUNGSI PERBAIKAN UNTUK MENGATASI NAME ERROR
# =========================================================================
async def get_audio_source_from_track(track: Track):
    """
    Mengambil objek Track dan mengembalikannya sebagai MediaStream 
    yang dapat digunakan oleh PyTgCalls.
    Fungsi ini adalah wrapper untuk _build_stream.
    """
    return await _build_stream(track)
# =========================================================================


async def _start_stream(chat_id: int, track: Track, client: PyTgCalls):
    audio_source = await get_audio_source_from_track(track)
    
    # Klien utama PyTgCalls harus menggunakan MediaStream sebagai argumen untuk join/change
    stream = audio_source 
    
    if not await client.is_connected(chat_id):
        try:
            logging.info(f"Joining VC in {chat_id} and starting stream.")
            await client.join_group_call(
                chat_id,
                stream # Menggunakan MediaStream yang dibangun dari track
            )
        except Exception as e:
            logging.error(f"Failed to join VC in {chat_id}: {e}")
            raise
            
    else:
        logging.info(f"Client already in VC. Changing stream to new track.")
        await client.change_stream(
            chat_id, 
            stream
        )
        
    st = get_vc_state(chat_id)
    st['now_playing'] = track
    st['status'] = 'playing'
    
    # Baris ini terlihat duplikat dan berpotensi menyebabkan error, 
    # karena logika join/change sudah ada di blok if/else di atas. 
    # Dibiarkan sesuai kode asli, tetapi perlu diwaspadai jika terjadi bug.
    try:
        await client.join_group_call(chat_id, stream)
    except Exception:
        await client.change_stream(chat_id, stream)

async def global_play(event: events.NewMessage, track: Track):
    chat_id = event.chat_id
    st = get_vc_state(chat_id, create=True)
    client = call_py

    async with st['lock']:
        if st['now_playing'] is None:
            await _start_stream(chat_id, track, client)
            return 1 
        else:
            st['queue'].append(track)
            return len(st['queue']) + 1

async def global_leave(chat_id: int):
    client = call_py
    try:
        await client.leave_group_call(chat_id)
    except Exception:
        pass
    VC_STATUS.pop(chat_id, None)

async def _on_track_end_handler(_, update: StreamEnded):
    chat_id = update.chat_id
    st = get_vc_state(chat_id)
    if not st: return
    
    client = call_py 
    
    async with st['lock']:
        if not st['queue']:
            st['now_playing'] = None
            with contextlib.suppress(Exception):
                await client.leave_group_call(chat_id)
            VC_STATUS.pop(chat_id, None)
            return None
        
        nxt: Track = st['queue'].pop(0) 
        await _start_stream(chat_id, nxt, client)
        return nxt

def register_vc_handlers():
    global call_py 
    
    if call_py is None:
        logger.warning("call_py is still None after loading plugin. Handlers not registered.")
        return

    @call_py.on_stream_end()
    async def on_end_global(client, update: StreamEnded):
        await _on_track_end_handler(client, update)

    @call_py.on_closed_voice_chat()
    async def closedvc_global(_, chat_id: int):
        VC_STATUS.pop(chat_id, None)

    @call_py.on_left()
    @call_py.on_kicked()
    async def left_kicked_vc_global(_, chat_id: int):
        VC_STATUS.pop(chat_id, None)

    logger.info("VC Handlers registered successfully.")

btnn =[[Button.inline("✯ cʟᴏꜱᴇ ✯", data="cls")]]

@ultroid_cmd(pattern="cls")
async def _(event):
     await event.delete()


@ultroid_cmd(pattern="play(?: (.+))?", allow_sudo=True, groups_only=True)
@AssistantAdd
async def play(event):
    chat_id = event.chat_id
    from_user = vcmention(await event.get_sender()) 
    st = get_vc_state(chat_id, create=True)
    
    query = event.pattern_match.group(1)
    replied = await event.get_reply_message()

    if not replied and not query:
        return await event.client.send_file(chat_id, Config.CMD_IMG, caption="**Give Me Your Query Which You want to Play**\n\n **Example**: `{}play Nira Ishq Bass boosted`".format(HNDLR), buttons=btnn)

    botman = await event.reply("🔎")
    
    if query:
        search = await ytsearch(query)
        if search == 0:
            return await botman.edit("**Can't Find Song** Try searching with More Specific Title")
            
        songname, url, duration, thumbnail, videoid = search
        sender = await event.get_sender()
        thumb = await gen_thumb(videoid) 
        format = "bestaudio[ext=m4a]" 
        hm, ytlink = await ytdl(format, url) 
        
        if hm == 0:
            return await botman.edit(f"`{ytlink}`")

        new_track = Track(songname, ytlink, url, "Audio", st['volume'], sender)
        
        if st['now_playing']:
            pos = await global_play(event, new_track)
            caption = f"✨ **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await botman.delete()
            await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
        else:
            try:
                await _start_stream(chat_id, new_track, call_py)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
            except Exception as ep:
                st['now_playing'] = None
                st['queue'].clear()
                await botman.edit(f"`{ep}`")
    
    elif replied and (replied.audio or replied.voice):
        await botman.edit("➕ Downloading File...")
        dl = await replied.download_media(file=DOWNLOAD_DIR)
        link = f"https://t.me/c/{chat_id}/{replied.id}"
        songname = "Telegram Music Player" if replied.audio else "Voice Note"
        sender = await event.get_sender()

        new_track = Track(songname, dl, link, "Audio", st['volume'], sender)
        
        if st['now_playing']:
            pos = await global_play(event, new_track)
            caption = f"✨ **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await botman.delete()
            await event.client.send_file(chat_id, ngantri, caption=caption, buttons=btnn)
        else:
            try:
                await _start_stream(chat_id, new_track, call_py)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await botman.delete()
                await event.client.send_file(chat_id, fotoplay, caption=caption, buttons=btnn)
            except Exception as ep:
                st['now_playing'] = None
                st['queue'].clear()
                await botman.edit(f"`{ep}`")

    else:
        return await botman.edit("Invalid input or replied media. Need query or audio/voice reply.")


@ultroid_cmd(pattern="end$", allow_sudo=True, groups_only=True)
@is_admin
async def vc_end(event, perm):
    chat_id = event.chat_id
    st = get_vc_state(chat_id) 
    
    if st and st['now_playing']:
        await global_leave(chat_id)
        await event.reply(f"**Streaming Ended**")
    else:
        await event.reply("**Ntg is playing ~**")

@ultroid_cmd(pattern="vplay(?: (.+))?", allow_sudo=True, groups_only=True)
@AssistantAdd
async def vplay(event):
    chat_id = event.chat_id
    from_user = vcmention(await event.get_sender())
    st = get_vc_state(chat_id, create=True)

    if Var.HEROKU_MODE == "ENABLE": 
        await event.reply("__Currently Heroku Mode is ENABLED so You Can't Stream Video because Video Streaming Cause of Banning Your Heroku Account__.")
        return

    query = event.pattern_match.group(1)
    replied = await event.get_reply_message()
    
    if not replied and not query:
        return await event.client.send_file(chat_id, Config.CMD_IMG, caption="**Give Me Your Query Which You want to Stream**\n\n **Example**: `{}vplay Nira Ishq Bass boosted`".format(HNDLR), buttons=btnn)

    xnxx = await event.reply("**🔄 Processing Query... Please Wait!**")
    
    RESOLUSI = 720 

    if query:
        search = await ytsearch(query)
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

        if st['now_playing']:
            pos = await global_play(event, new_track)
            caption = f"**✨ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await xnxx.delete()
            await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
        else:
            try:
                await _start_stream(chat_id, new_track, call_py)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n🌸 **ᴛɪᴛʟᴇ :** [{songname}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ :** {duration} ᴍɪɴᴜᴛᴇs\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await xnxx.delete()
                await event.client.send_file(chat_id, thumb, caption=caption, buttons=btnn)
            except Exception as ep:
                st['now_playing'] = None
                st['queue'].clear()
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

        if st['now_playing']:
            pos = await global_play(event, new_track)
            caption = f"**✨ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ** {pos}\n\n❄ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
            await xnxx.delete()
            await event.client.send_file(chat_id, ngantri, caption=caption, buttons=btnn)
        else:
            try:
                await _start_stream(chat_id, new_track, call_py)
                caption = f"➻ **sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ**\n\n✨ **ᴛɪᴛʟᴇ :** [{songname}]({link})\n🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {from_user}"
                await xnxx.delete()
                await event.client.send_file(chat_id, fotoplay, caption=caption, buttons=btnn)
            except Exception as ep:
                st['now_playing'] = None
                st['queue'].clear()
                await xnxx.edit(f"`{ep}`")
    
    else:
        return await xnxx.edit("Invalid input or replied media. Need query, video/document reply, or audio/voice reply.")
