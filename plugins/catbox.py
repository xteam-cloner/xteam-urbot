import asyncio
import os
from . import ultroid_cmd, eor, ULTROID_IMAGES
from catbox import CatboxUploader
from random import choice


# Inisialisasi CatboxUploader
cat_uploader = CatboxUploader()
# upload_file = cat_uploader.upload_file # This line is problematic if upload_file is not async

# Fungsi untuk mendapatkan gambar inline (opsional, dari kode Anda sebelumnya)
def inline_pic():
    return choice(ULTROID_IMAGES)

@ultroid_cmd(pattern="catbox(?: |$)(.*)")
async def catbox_upload_plugin(event):
    """
    Plugin untuk mengunggah file ke Catbox.moe.
    """
    if not event.reply_to_msg_id:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Catbox.moe.")

    reply_message = await event.get_reply_message()

    if not reply_message.media:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Catbox.moe.")

    message = await eor(event, "Mengunduh media...")
    filePath = None  # Initialize filePath outside the try block
    try:
        filePath = await reply_message.download_media()

        await message.edit("Mengunggah ke Catbox.moe...")

        # <<< --- FIX IS HERE --- >>>
        # Call upload_file directly without await, as it's a synchronous method.
        # If it were an async method, it would be defined with 'async def'.
        uploaded_url = cat_uploader.upload_file(filePath)

        await message.edit(f"<blockquote>📤 Successful upload!\nURL: {uploaded_url}</blockquote>", parse_mode="html")
    except Exception as e:
        await message.edit(f"Terjadi kesalahan saat mengunggah: {e}")
    finally:
        # Hapus file lokal setelah diunggah
        if filePath and os.path.exists(filePath):
            os.remove(filePath)

import asyncio
import os
from . import ultroid_cmd, eor, ULTROID_IMAGES
from catbox import CatboxUploader 
from random import choice
from telethon.tl.types import DocumentAttributeFilename # Import ini jika perlu untuk penamaan file yang lebih baik
# Pastikan Anda sudah menginstal pustaka yang diperlukan: pip install catbox-uploader

# Inisialisasi CatboxUploader
cat_uploader = CatboxUploader() 

# Fungsi untuk mendapatkan gambar inline (opsional)
def inline_pic():
    return choice(ULTROID_IMAGES)

@ultroid_cmd(pattern="litterbox(?: |$)(.*)")
async def litterbox_upload_plugin(event):
    """
    Plugin untuk mengunggah file ke Litterbox.catbox.moe (temporer).
    """
    if not event.reply_to_msg_id:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.catbox.moe.")

    reply_message = await event.get_reply_message()

    if not reply_message.media:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.catbox.moe.")

    # Ambil durasi kedaluwarsa dari argumen. Default ke 72h.
    expiry_time = event.pattern_match.group(1).strip()
    if expiry_time not in ['1h', '12h', '24h', '72h']:
        expiry_time = '72h' 

    message = await eor(event, f"Mengunduh media untuk Litterbox (Kedaluwarsa: **{expiry_time}**)...")
    filePath = None
    
    try:
        # Tentukan folder unduhan sementara
        # Gunakan '.' untuk mendownload di direktori saat ini, atau '/tmp/' jika tersedia
        download_dir = "./" 
        
        # <<< --- PERUBAHAN UTAMA 1: Unduh file dengan jalur yang eksplisit --- >>>
        # reply_message.download_media(file=...) memastikan file benar-benar ditulis ke disk
        # dan mengembalikan string jalur file.
        filePath = await reply_message.download_media(file=download_dir)

        # Pastikan filePath adalah string (jalur file)
        if not isinstance(filePath, str):
            # Jika Telethon mengembalikan objek File, kita coba ambil nama filenya
            # Baris ini mungkin berbeda tergantung implementasi Telethon Anda.
            filePath = reply_message.file.name if hasattr(reply_message.file, 'name') else None
            # Jika masih gagal, buat kesalahan
            if not filePath or not os.path.exists(filePath):
                 raise Exception("Gagal mendapatkan jalur file unduhan yang valid.")

        await message.edit("Mengunggah ke Litterbox.catbox.moe...")

        # <<< --- PERUBAHAN UTAMA 2: Memanggil upload_to_litterbox dengan parameter 'time' --- >>>
        # Perbaikan dari error sebelumnya: 'expiry_time' diganti menjadi 'time'
        uploaded_url = cat_uploader.upload_to_litterbox(filePath, time=expiry_time)

        await message.edit(f"<blockquote>📤 Unggahan Litterbox Berhasil!\nURL: {uploaded_url}\nKedaluwarsa: {expiry_time}</blockquote>", parse_mode="html")
        
    except Exception as e:
        # Jika ada path, hapus saja untuk membersihkan
        if filePath and os.path.exists(filePath):
            os.remove(filePath)
            
        await message.edit(f"Terjadi kesalahan saat mengunggah ke Litterbox: `{type(e).__name__}: {e}`")
        
    finally:
        # <<< --- PERUBAHAN UTAMA 3: Pastikan penghapusan di dalam finally setelah semua operasi I/O selesai --- >>>
        # Hapus file lokal setelah diunggah, jika masih ada dan belum dihapus di blok except
        if filePath and os.path.exists(filePath):
            try:
                os.remove(filePath)
            except Exception as clean_e:
                # Kesalahan saat menghapus mungkin tidak perlu dilaporkan ke pengguna
                print(f"Peringatan: Gagal menghapus file lokal: {clean_e}")
                pass
