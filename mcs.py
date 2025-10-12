# Import os (dibiarkan sesuai permintaan)
import asyncio
from telethon import TelegramClient, events
from pytgcalls import PyTgCalls, idle
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream
from xteam.configs import Var 

# --- KONFIGURASI ---
API_ID = Var.API_ID 
API_HASH = Var.API_HASH 

# Menggunakan STRING_SESSION sebagai nama sesi
STRING_SESSION = Var.SESSION 

# URL Audio/Video untuk diputar (Diubah menjadi URL YouTube)
# PyTgCalls akan menggunakan yt-dlp untuk mendapatkan stream audio dari URL ini.
DEFAULT_STREAM_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' 
# ------------------------------------

# Inisialisasi Klien Telethon menggunakan STRING_SESSION
client = TelegramClient(SESSION, API_ID, API_HASH)

# Inisialisasi PyTgCalls dengan Klien Telethon
pytgcalls_app = PyTgCalls(client)

# Dictionary untuk melacak status obrolan suara
voice_chat_status = {}

# --- FUNGSI UTAMA ---

async def main():
    print("Memulai klien Telethon dengan STRING_SESSION...")
    await client.start()
    
    print("Memulai PyTgCalls...")
    await pytgcalls_app.start()

    print("Bot siap! Kirim /join atau /playurl di grup dengan Obrolan Suara aktif.")

    # Tetap jalankan bot sampai terputus
    await idle()
    
    print("Menghentikan bot.")
    await client.run_until_disconnected()

# --- HANDLER PERINTAH ---

@client.on(events.NewMessage(pattern="join"))
async def join_handler(event):
    """Bergabung ke obrolan suara saat ini dan putar stream default."""
    chat_id = event.chat_id
    await event.reply("Mencoba bergabung ke obrolan suara...")

    try:
        # Bergabung ke obrolan suara
        await pytgcalls_app.join(
            chat_id,
            MediaStream(DEFAULT_STREAM_URL)
        )
        voice_chat_status[chat_id] = True
        await event.reply(f"🎶 **Berhasil bergabung** ke obrolan suara dan mulai memutar URL default (YouTube).")
    
    except NoActiveGroupCall:
        await event.reply("⚠️ **Gagal:** Tidak ada Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.reply(f"❌ **Terjadi Kesalahan** saat mencoba bergabung: {e}")


@client.on(events.NewMessage(pattern="playurl (.*)"))
async def play_url_handler(event):
    """Mulai memutar URL yang diberikan. Bergabung jika belum ada di obrolan suara."""
    chat_id = event.chat_id
    url_to_play = event.pattern_match.group(1).strip()
    
    if not url_to_play:
        await event.reply("⚠️ Harap berikan URL audio atau video. Format: `/playurl <url>` (Mendukung tautan YouTube).")
        return

    await event.reply(f"Mencoba memutar: `{url_to_play}`...")

    try:
        if chat_id in voice_chat_status and voice_chat_status[chat_id]:
            # Jika sudah di obrolan suara, ganti stream yang sedang diputar
            await pytgcalls_app.change_stream(
                chat_id,
                MediaStream(url_to_play)
            )
            await event.reply(f"🔄 **Stream diperbarui** ke: {url_to_play}")
        else:
            # Jika belum di obrolan suara, bergabung dan mulai memutar
            await pytgcalls_app.join(
                chat_id,
                MediaStream(url_to_play)
            )
            voice_chat_status[chat_id] = True
            await event.reply(f"🎶 **Berhasil bergabung** dan mulai memutar: {url_to_play}")
            
    except NoActiveGroupCall:
        await event.reply("⚠️ **Gagal:** Tidak ada Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.reply(f"❌ **Terjadi Kesalahan** saat mencoba memutar: {e}")


@client.on(events.NewMessage(pattern="leave"))
async def leave_handler(event):
    """Tinggalkan obrolan suara saat ini."""
    chat_id = event.chat_id
    await event.reply("Mencoba meninggalkan obrolan suara...")
    
    try:
        await pytgcalls_app.leave(chat_id)
        voice_chat_status[chat_id] = False
        await event.reply("👋 **Berhasil meninggalkan** obrolan suara.")
        
    except NoActiveGroupCall:
        await event.reply("⚠️ **Gagal:** Bot tidak ada di Obrolan Suara aktif di grup ini.")
    except Exception as e:
        await event.reply(f"❌ **Terjadi Kesalahan** saat mencoba meninggalkan: {e}")

# --- TITIK MASUK ---

if __name__ == '__main__':
    # Telethon dan pytgcalls keduanya bersifat asynchronous, jadi kita jalankan di loop event
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot dihentikan oleh pengguna.")
    except Exception as e:
        print(f"Kesalahan Fatal: {e}")
