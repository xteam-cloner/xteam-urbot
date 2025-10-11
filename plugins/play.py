import asyncio
import os
import time
import datetime
from random import choice
import requests
from telethon import Button, events
from telethon.tl import functions, types
# Impor PyTgCalls dan Exception yang dibutuhkan
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import AlreadyJoinedError, NoActiveGroupCall

# Menggunakan impor yang sudah Anda definisikan di core file Ultroid
# Pastikan impor-impor ini berfungsi di lingkungan Ultroid Anda:
from xteam._misc._decorators import ultroid_cmd
from xteam._misc._wrappers import eod, eor
from xteam.dB import DEVLIST, ULTROID_IMAGES, ALIVE_TEXT, ALIVE_NAME, QUOTES
from xteam.fns.helper import *
from xteam.fns.misc import *
from xteam.fns.tools import *
from xteam.startup._database import _BaseDatabase as Database
from xteam.version import __version__, ultroid_version
from strings import get_help, get_string
from xteam._misc._supporter import CMD_HNDLR
from xteam.dB import stickers

# Variabel Global yang Anda definisikan (perlu dipertahankan)
udB: Database
# ... (variabel lain seperti Redis, con, quotly, OWNER_NAME, dll.)

# Objek klien Ultroid yang sudah berjalan
ultroid_bot: UltroidClient
asst: UltroidClient

xteam = ultroid_cmd # Alias untuk command handler

# --- INISIASI PYTGCALLS ---

# Inisiasi PyTgCalls menggunakan klien Telethon utama Ultroid (ultroid_bot)
try:
    call_py = PyTgCalls(ultroid_bot)
    call_py.start()
except Exception as e:
    # Ini mungkin terjadi jika PyTgCalls sudah berjalan atau ada masalah inisiasi
    print(f"Peringatan: Gagal memulai PyTgCalls, mungkin sudah berjalan atau ada error: {e}")
    # Jika gagal, buat objek tanpa mencoba start lagi (berasumsi sudah di-handle core)
    call_py = PyTgCalls(ultroid_bot) 

# --- FUNGSI COMMAND VOICE CALL ---

@xteam(pattern="playvc (.*)", usage="Untuk memutar media di Voice Chat.\nContoh: `.playvc [url_media]`")
@eor
async def play_vc_cmd(event):
    """Memutar media (audio/video) di Voice Chat."""
    if not event.is_group:
        return await event.edit("`Perintah ini hanya dapat digunakan di grup.`")

    # Ambil URL media dari argumen command
    media_url = event.pattern_match.group(1).strip()
    chat_id = event.chat_id
    
    await event.edit("`Memproses media dan mencoba terhubung ke Voice Chat...`")

    try:
        # Bergabung ke Voice Chat dan mulai memutar
        await call_py.join_group_call(
            chat_id,
            media_url,
        )
        
        await event.edit(f"🎶 **Berhasil Memutar** di Voice Chat:\n`{media_url}`")
        
    except NoActiveGroupCall:
        await event.edit("`Gagal: Tidak ada Voice Chat aktif di grup ini.`")
    except AlreadyJoinedError:
        try:
            # Jika userbot sudah bergabung, ganti stream media
            await call_py.change_stream(
                chat_id,
                media_url,
            )
            await event.edit(f"🔁 **Berhasil Mengganti media** di Voice Chat:\n`{media_url}`")
        except Exception as e:
            await event.edit(f"**Gagal mengganti stream:**\n`{e}`")
    except Exception as e:
        await event.edit(f"**Kesalahan saat bergabung/memutar:**\n`{e}`")


@xteam(pattern="stopvc", usage="Untuk menghentikan pemutaran dan keluar dari Voice Chat.")
@eor
async def stop_vc_cmd(event):
    """Menghentikan pemutaran dan keluar dari Voice Chat."""
    if not event.is_group:
        return await event.edit("`Perintah ini hanya dapat digunakan di grup.`")

    try:
        await call_py.leave_group_call(event.chat_id)
        await event.edit("🛑 **Berhasil meninggalkan Voice Chat.**")
    except Exception as e:
        await event.edit(f"**Gagal meninggalkan VC:**\n`{e}`")
        
# --- END OF VC PLAYER PLUGIN ---
