import asyncio
from telethon import TelegramClient, events
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream
from telethon.tl.types import User
from . import OWNER_ID
# ✅ Mengambil konfigurasi dan fungsi YouTube dari framework Ultroid
from xteam.configs import Var 
from xteam.fns.ytdl import download_yt, get_yt_link

# --- KONFIGURASI ---
# Catatan: Berdasarkan kode inti Ultroid yang Anda tunjukkan, 
# variabel sesi klien asisten adalah VC_SESSION.
OWNER_ID = OWNER_ID 
VC_SESSION = Var.VC_SESSION # Session string akun asisten (Wajib format Telethon)
API_ID = Var.API_ID 
API_HASH = Var.API_HASH 

DEFAULT_STREAM_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' 
voice_chat_status = {}
my_handler_id = None 

# --- KLIEN ASISTEN & PYTGCALLS ---

# Inisialisasi Klien Asisten (app)
app = TelegramClient(
    session=VC_SESSION,
    api_id=API_ID,
    api_hash=API_HASH
)

# Inisialisasi PyTgCalls (Call_py)
Call_py = PyTgCalls(app)

# --- FUNGSI STARTUP (SOLUSI RUNTIME ERROR) ---

async def start_assistant(event): 
    """Memastikan klien asisten dimulai dan PyTgCalls aktif."""
    global my_handler_id
    try:
        # 1. Menjalankan klien asisten ('app')
        if not await app.is_user_authorized():
            print("Memulai Klien Asisten...")
            await app.start()
        
        # 2. Menjalankan PyTgCalls
        if not Call_py.is_running:
            print("Memulai PyTgCalls...")
            await Call_py.start()
        
        print("Asisten Voice Chat siap.")

    except Exception as e:
        print(f"❌ ERROR: Gagal memulai klien asisten/PyTgCalls. Cek konfigurasi: {e}")
        
    # 3. Hapus handler setelah dijalankan agar tidak terpicu lagi (Penting!)
    client.remove_event_handler(start_assistant, events.NewMessage(pattern=None))

# --- FILTER PERINTAH ---

def is_user_command(event):
    """Memastikan pengirim adalah akun yang memiliki OWNER_ID."""
    return isinstance(event.sender, User) and event.sender.id == OWNER_ID

# --- HANDLER PERINTAH ULTROID (CLIENT UTAMA) ---

@client.on(events.NewMessage(pattern=r"[.!/](?:joinvc|join)"))
async def joinvc_handler(event):
    """Bergabung ke obrolan suara saat ini dan putar stream default."""
    
    if not is_user_command(event):
        return

    chat_id = event.chat_id
    await event.edit("`Mencoba bergabung ke obrolan suara...`")

    try:
        await Call_py.join(
            chat_id,
            MediaStream(DEFAULT_STREAM_URL)
        )
        voice_chat_status[chat_id] = True
        await event.edit(f"🎶 **Berhasil bergabung** ke obrolan suara dan mulai memutar URL default.")
    
    except NoActiveGroupCall:
        await event.edit("⚠️ **Gagal:** Tidak ada Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.edit(f"❌ **Terjadi Kesalahan** saat mencoba bergabung: `{e}`")


@client.on(events.NewMessage(pattern=r"[.!/](?:play|playurl) (.*)"))
async def play_url_handler(event):
    """Mulai memutar URL yang diberikan (langsung)."""
    
    if not is_user_command(event):
        return
        
    chat_id = event.chat_id
    url_to_play = event.pattern_match.group(1).strip()
    
    await event.edit(f"`Mencoba memutar: {url_to_play}`...")

    try:
        if voice_chat_status.get(chat_id):
            await Call_py.change_stream(
                chat_id,
                MediaStream(url_to_play)
            )
            await event.edit(f"🔄 **Stream diperbarui** ke: {url_to_play}")
        else:
            await Call_py.join(
                chat_id,
                MediaStream(url_to_play)
            )
            voice_chat_status[chat_id] = True
            await event.edit(f"🎶 **Berhasil bergabung** dan mulai memutar: {url_to_play}")
            
    except NoActiveGroupCall:
        await event.edit("⚠️ **Gagal:** Tidak ada Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.edit(f"❌ **Terjadi Kesalahan** saat mencoba memutar: `{e}`")


@client.on(events.NewMessage(pattern=r"[.!/]yplay (.*)"))
async def yplay_handler(event):
    """Mencari di YouTube (get_yt_link) dan memutar hasil pertama."""
    
    if not is_user_command(event):
        return
        
    chat_id = event.chat_id
    search_query = event.pattern_match.group(1).strip()
    
    if not search_query:
        await event.edit("⚠️ Harap berikan kata kunci pencarian. Format: `[.]yplay <judul lagu>`")
        return
        
    await event.edit(f"`Mencari {search_query} di YouTube...`")

    try:
        # Fungsi internal Ultroid
        url_to_play = await get_yt_link(search_query) 
        
        if not url_to_play:
            await event.edit("❌ **Gagal:** Video tidak ditemukan.")
            return
            
        if voice_chat_status.get(chat_id):
            await Call_py.change_stream(
                chat_id,
                MediaStream(url_to_play)
            )
            await event.edit(f"🔄 **Stream diperbarui** ke: [{search_query}]({url_to_play})")
        else:
            await Call_py.join(
                chat_id,
                MediaStream(url_to_play)
            )
            voice_chat_status[chat_id] = True
            await event.edit(f"🎶 **Berhasil bergabung** dan mulai memutar: [{search_query}]({url_to_play})")
            
    except NoActiveGroupCall:
        await event.edit("⚠️ **Gagal:** Tidak ada Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.edit(f"❌ **Terjadi Kesalahan** saat memutar/mencari: `{e}`")


@client.on(events.NewMessage(pattern=r"[.!/](?:leave|stop)"))
async def leave_handler(event):
    """Tinggalkan obrolan suara saat ini."""
    
    if not is_user_command(event):
        return
        
    chat_id = event.chat_id
    await event.edit("`Mencoba meninggalkan obrolan suara...`")
    
    try:
        await Call_py.leave(chat_id)
        voice_chat_status[chat_id] = False
        await event.edit("👋 **Berhasil meninggalkan** obrolan suara.")
        
    except NoActiveGroupCall:
        await event.edit("⚠️ **Gagal:** Bot tidak ada di Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.edit(f"❌ **Terjadi Kesalahan** saat mencoba meninggalkan: `{e}`")


# --- PANGGIL FUNGSI STARTUP PADA EVENT LOOP (SETELAH KLIEN SIAP) ---

# Handler ini berjalan segera setelah Ultroid dimulai (dan event loop berjalan), 
# memicu fungsi 'start_assistant' sekali saja.
client.add_event_handler(start_assistant, events.NewMessage(pattern=None)) 
            
