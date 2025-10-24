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
from catbox import CatboxUploader # Pastikan pustaka yang digunakan mendukung Litterbox
from random import choice


# Inisialisasi CatboxUploader
cat_uploader = CatboxUploader()
# upload_file = cat_uploader.upload_file # Tidak diperlukan

# Fungsi untuk mendapatkan gambar inline (opsional, dari kode Anda sebelumnya)
def inline_pic():
    return choice(ULTROID_IMAGES)

@ultroid_cmd(pattern="litterbox(?: |$)(.*)") # Ganti pattern command
async def litterbox_upload_plugin(event):
    """
    Plugin untuk mengunggah file ke Litterbox.catbox.moe (temporer).
    """
    if not event.reply_to_msg_id:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.catbox.moe.")

    reply_message = await event.get_reply_message()

    if not reply_message.media:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.catbox.moe.")

    # Ambil durasi kedaluwarsa dari argumen, jika ada. Default ke 72 jam.
    # Contoh: .litterbox 12h
    expiry_time = event.pattern_match.group(1).strip()
    # Atur default jika tidak ada input atau input tidak valid
    if expiry_time not in ['1h', '12h', '24h', '72h']:
        expiry_time = '72h' # Litterbox default atau 72h

    message = await eor(event, f"Mengunduh media untuk Litterbox (Kedaluwarsa: **{expiry_time}**)...")
    filePath = None
    try:
        filePath = await reply_message.download_media()

        await message.edit("Mengunggah ke Litterbox.catbox.moe...")

        # <<< --- PERUBAHAN UTAMA DI SINI --- >>>
        # Gunakan cat_uploader.upload_to_litterbox(filepath, expire_time)
        uploaded_url = cat_uploader.upload_to_litterbox(filePath, expiry_time=expiry_time)

        await message.edit(f"<blockquote>📤 Unggahan Litterbox Berhasil!\nURL: {uploaded_url}\nKedaluwarsa: {expiry_time}</blockquote>", parse_mode="html")
    except Exception as e:
        await message.edit(f"Terjadi kesalahan saat mengunggah ke Litterbox: {e}")
    finally:
        # Hapus file lokal setelah diunggah
        if filePath and os.path.exists(filePath):
            os.remove(filePath)
            
