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
import httpx 
from . import ultroid_cmd, eor, ULTROID_IMAGES
from random import choice


# Fungsi untuk mendapatkan gambar inline (opsional, dari kode Anda sebelumnya)
def inline_pic():
    return choice(ULTROID_IMAGES)

@ultroid_cmd(pattern="litbox") # PERUBAHAN DI SINI: pattern hanya "catbox"
async def litterbox_upload_plugin(event):
    """
    Plugin untuk mengunggah file ke Litterbox.catbox.moe.
    Waktu kedaluwarsa selalu 72 jam (3 hari).
    Sintaks: .catbox (cukup balas media)
    """
    if not event.reply_to_msg_id:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.")

    reply_message = await event.get_reply_message()

    if not reply_message.media:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke Litterbox.")

    # Tetapkan waktu kedaluwarsa secara permanen ke '72h'
    expiry_time = "72h" 
    
    # URL dan Data untuk Litterbox
    LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"
    
    message = await eor(event, "Mengunduh media...")
    filePath = None
    
    try:
        # Unduh media
        filePath = await reply_message.download_media()

        await message.edit("Mengunggah ke Litterbox.catbox.moe (Expiry: 72h)...")

        # --- LOGIKA UNGGAH LITTERBOX DENGAN HTTPX ---
        
        # Buka file dalam mode binary untuk diunggah
        with open(filePath, 'rb') as f:
            
            # Data form yang diperlukan oleh API
            data_payload = {
                'reqtype': 'fileupload',
                'time': expiry_time # Nilai kini selalu '72h'
            }
            
            # Bagian file untuk unggahan multipart/form-data
            files_payload = {
                'fileToUpload': f 
            }

            # Gunakan httpx.AsyncClient untuk permintaan POST asinkron
            # Timeout ditingkatkan untuk file besar
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    LITTERBOX_URL, 
                    data=data_payload, 
                    files=files_payload
                )

        # Cek status respons dan ambil URL
        if response.status_code == 200:
            uploaded_url = response.text.strip()
            await message.edit(
                f"<blockquote>📤 Successful Litterbox upload!\n**Expiry:** {expiry_time}\nURL: {uploaded_url}</blockquote>", 
                parse_mode="html"
            )
        else:
            await message.edit(f"Terjadi kesalahan saat mengunggah (Status: {response.status_code}): {response.text}")

    except Exception as e:
        await message.edit(f"Terjadi kesalahan saat mengunggah: <code>{type(e).__name__}: {e}</code>", parse_mode="html")
    finally:
        # Hapus file lokal setelah diunggah
        if filePath and os.path.exists(filePath):
            os.remove(filePath)
