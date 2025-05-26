from telethon import TelegramClient, events
from pytgcalls import idle, PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall # Import pengecualian spesifik
import asyncio
import logging # Untuk logging yang lebih baik

# Impor konfigurasi dari xteam.configs.Var
from xteam.configs import Var # Asumsi Var berisi API_ID dan API_HASH

# --- Konfigurasi Logging ---
# Atur level logging ke INFO agar lebih informatif
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Inisialisasi Klien Telegram dan PyTgCalls ---
# Menggunakan variabel dari Var untuk API_ID dan API_HASH
API_ID = Var.API_ID
API_HASH = Var.API_HASH

app = TelegramClient(
    'xteam', # Nama sesi untuk bot
    API_ID,
    API_HASH,
)

call_py = PyTgCalls(app)

# --- Handler untuk Perintah /play ---
@app.on(events.NewMessage(pattern='/play'))
async def play_command(event):
    chat_id = event.chat_id
    logger.info(f"Menerima perintah /play di chat ID: {chat_id}")

    try:
        # Pastikan obrolan suara sudah aktif di grup ini
        await call_py.play(
            chat_id,
            'http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4',
        )
        await event.reply("Memulai pemutaran media! 🎶")
        logger.info(f"Media diputar di {chat_id}")
    except NoActiveGroupCall:
        await event.reply("Tidak ada obrolan suara aktif di grup ini. Mohon mulai obrolan suara terlebih dahulu. 🗣️")
        logger.warning(f"Error: Tidak ada obrolan suara aktif di {chat_id}")
    except Exception as e:
        await event.reply(f"Gagal memutar media: {e} 😟")
        logger.error(f"Error saat memutar media di {chat_id}: {e}", exc_info=True) # exc_info=True untuk detail traceback

# --- Handler untuk Perintah /stop ---
@app.on(events.NewMessage(pattern='/stop'))
async def stop_command(event):
    chat_id = event.chat_id
    logger.info(f"Menerima perintah /stop di chat ID: {chat_id}")

    try:
        await call_py.stop(chat_id)
        await event.reply("Pemutaran media dihentikan dan bot keluar dari obrolan suara. 👋")
        logger.info(f"Media dihentikan di {chat_id}")
    except NoActiveGroupCall:
        await event.reply("Bot tidak sedang berada di obrolan suara aktif di grup ini.")
        logger.warning(f"Error: Bot tidak aktif di obrolan suara di {chat_id}")
    except Exception as e:
        await event.reply(f"Gagal menghentikan media: {e} 😬")
        logger.error(f"Error saat menghentikan media di {chat_id}: {e}", exc_info=True)

# --- Fungsi Utama untuk Menjalankan Bot ---
async def main():
    logger.info("Memulai klien Telegram (bot)...")
    await app.start()
    logger.info("Klien Telegram (bot) dimulai.")

    logger.info("Memulai PyTgCalls...")
    await call_py.start()
    logger.info("PyTgCalls dimulai.")

    logger.info("Bot siap menerima perintah. Tekan Ctrl+C untuk menghentikan.")
    await idle() # Biarkan bot tetap berjalan dan mendengarkan event

    logger.info("Menghentikan PyTgCalls...")
    await call_py.stop_all_group_calls() # Pastikan semua panggilan dihentikan
    await call_py.stop() # Hentikan PyTgCalls
    logger.info("Menghentikan klien Telegram...")
    await app.disconnect()
    logger.info("Selesai.")

# --- Jalankan Fungsi Utama ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot dihentikan secara manual (Ctrl+C).")
    except Exception as e:
        logger.critical(f"Terjadi kesalahan fatal yang tidak tertangani: {e}", exc_info=True)
