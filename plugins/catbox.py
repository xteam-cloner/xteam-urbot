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
