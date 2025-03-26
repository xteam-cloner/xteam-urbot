import re
import requests
from datetime import timedelta
from yt_dlp import YoutubeDL
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetScheduledHistoryRequest
from telethon.tl.types import InputPeerChannel, InputPeerChat, InputPeerUser
from telethon.errors import PeerIdInvalidError
from telethon.types import Message
from telethon.utils import get_input_peer
from . import ultroid_cmd as client
from pyUltroid import *

PLAYLIST = {}

async def get_input_entity(client, peer_id):
    try:
        return await client.get_input_entity(peer_id)
    except PeerIdInvalidError:
        return None

async def start_next_song(client, chat_id):
    if chat_id in PLAYLIST and PLAYLIST[chat_id]:
        next_song = PLAYLIST[chat_id][0]
        audio_url, title, duration = next_song

        try:
            await client.send_message(
                chat_id,
                f"▶️ <b>Memutar:</b> {title}\n"
                f"⏳ <b>Durasi:</b> {timedelta(seconds=duration)}",
                parse_mode="html"
            )
        except Exception as e:
            print(f"❌ Gagal mengirim pesan: {e}")

        # Placeholder for your voice chat implementation. Telethon does not have built in Voice Chat functionality, you will need to use a third party library.
        print(f"Playing {title} from {audio_url}") # Replace this with your voice chat implementation

async def stop_vc(client, chat_id):
    if chat_id in PLAYLIST:
        PLAYLIST.pop(chat_id, None)

@client.on(events.NewMessage(pattern=r"(?i)\.play"))
async def play_vc(event):
    msg = await event.respond("<code>Mencari dan memutar musik...</code>", parse_mode="html")

    query = event.text.split(".play ", maxsplit=1)[1]

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "default_search": "ytsearch1",
        "cookiefile": "cookies.txt",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)

        if not info or "url" not in info:
            return await msg.edit("❌ Gagal mendapatkan data lagu. Coba lagi.", parse_mode="html")

        audio_url = info["url"]
        title = info.get("title", "Judul Tidak Diketahui")
        duration = info.get("duration", 0)
        views = info.get("view_count", 0)
        channel = info.get("uploader", "Tidak Diketahui")
        link = info.get("webpage_url", "#")

        song_data = (audio_url, title, duration)

        chat_id = event.chat_id
        if chat_id not in PLAYLIST:
            PLAYLIST[chat_id] = []

        PLAYLIST[chat_id].append(song_data)

        if len(PLAYLIST[chat_id]) == 1:
            await start_next_song(client, chat_id)

        await msg.edit(
            f"<b>💡 ɪɴꜰᴏʀᴍᴀsɪ {title}</b>\n\n"
            f"<b>🏷 ɴᴀᴍᴀ:</b> {title}\n"
            f"<b>🧭 ᴅᴜʀᴀsɪ:</b> {timedelta(seconds=duration)}\n"
            f"<b>👀 ᴅɪʟɪʜᴀᴛ:</b> {views:,}\n"
            f"<b>📢 ᴄʜᴀɴɴᴇʟ:</b> {channel}\n"
            f"<b>🔗 ᴛᴀᴜᴛᴀɴ:</b> <a href='{link}'>ʏᴏᴜᴛᴜʙᴇ</a>\n\n"
            f"<b>⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ:</b> {channel}",
            parse_mode="html"
        )

    except Exception as e:
        await msg.edit(f"❌ Terjadi kesalahan: {e}", parse_mode="html")

@client.on(events.NewMessage(pattern=r"(?i)\.skip"))
async def skip_vc(event):
    chat_id = event.chat_id
    if chat_id not in PLAYLIST or not PLAYLIST[chat_id]:
        return await event.respond("❌ Tidak ada lagu untuk dilewati.", parse_mode="html")

    PLAYLIST[chat_id].pop(0)
    if PLAYLIST[chat_id]:
        await start_next_song(client, chat_id)
    else:
        await stop_vc(client, chat_id)

@client.on(events.NewMessage(pattern=r"(?i)\.end"))
async def end_vc(event):
    await stop_vc(client, event.chat_id, event)

@client.on(events.NewMessage(pattern=r"(?i)\.playlist"))
async def show_playlist(event):
    chat_id = event.chat_id
    if chat_id not in PLAYLIST or not PLAYLIST[chat_id]:
        return await event.respond("📭 Playlist kosong.", parse_mode="html")

    playlist_text = "<b>🎶 Playlist Saat Ini:</b>\n"
    for i, song in enumerate(PLAYLIST[chat_id], 1):
        title = song[1]
        duration = timedelta(seconds=song[2])
        playlist_text += f"\n🎵 <b>{i}. {title}</b> - {duration}"

    await event.respond(playlist_text, parse_mode="html")
    
@client.on(events.NewMessage(pattern=r"(?i)\.skip"))
async def skip_vc(event):
    chat_id = event.chat_id
    if chat_id not in PLAYLIST or not PLAYLIST[chat_id]:
        return await event.respond("❌ Tidak ada lagu untuk dilewati.", parse_mode="html")

    PLAYLIST[chat_id].pop(0)
    if PLAYLIST[chat_id]:
        await start_next_song(client, chat_id)
    else:
        await stop_vc(client, chat_id, event)

async def auto_next(client, chat_id):
    """Dipanggil saat lagu selesai, otomatis memutar lagu berikutnya."""

    if chat_id in PLAYLIST and PLAYLIST[chat_id]:
        PLAYLIST[chat_id].pop(0)
        if PLAYLIST[chat_id]:
            await start_next_song(client, chat_id)
        else:
            await stop_vc(client, chat_id, None) # pass none for the event, as the stop was triggered by auto_next.
