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
import requests # Pustaka untuk permintaan HTTP
from . import ultroid_cmd, eor, ULTROID_IMAGES
from random import choice
# CatboxUploader dan impor terkait telah dihapus

# Fungsi untuk mendapatkan gambar inline (opsional)
def inline_pic():
    return choice(ULTROID_IMAGES)

@ultroid_cmd(pattern="zeroxst(?: |$)(.*)")
async def zeroxst_upload_plugin(event):
    """
    Plugin untuk mengunggah file ke 0x0.st.
    Sintaks: .zeroxst
    0x0.st tidak mendukung durasi kedaluwarsa dari argumen.
    """
    if not event.reply_to_msg_id:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke 0x0.st.")

    reply_message = await event.get_reply_message()

    if not reply_message.media:
        return await eor(event, "Balas ke media atau file untuk mengunggahnya ke 0x0.st.")

    message = await eor(event, "Mengunduh media untuk 0x0.st...")
    filePath = None
    uploaded_url = None
    
    try:
        download_dir = "./" 
        
        # Unduh file.
        filePath = await reply_message.download_media(file=download_dir)

        if not isinstance(filePath, str) or not os.path.exists(filePath):
            raise Exception("Gagal mendapatkan jalur file unduhan yang valid.")

        await message.edit("Mengunggah ke 0x0.st...")

        # --- FUNGSI UNGGAHAN DENGAN SOLUSI USER-AGENT (Dijalankan di thread terpisah) ---
        def upload_blocking(path):
            # 💡 SOLUSI: Tentukan User-Agent untuk menghindari error 403
            CUSTOM_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            
            headers = {
                'User-Agent': CUSTOM_USER_AGENT
            }

            with open(path, 'rb') as file_handle:
                # 0x0.st mengharapkan bidang file bernama 'file'
                files = {'file': file_handle} 
                
                # Kirim permintaan POST dengan header User-Agent yang dimodifikasi
                r = requests.post('https://0x0.st', files=files, headers=headers) 
                
                if r.status_code == 200:
                    # 0x0.st mengembalikan URL sebagai teks biasa
                    return r.text.strip() 
                else:
                    # Menangani kegagalan jika status bukan 200
                    raise Exception(f"Unggahan gagal (Status: {r.status_code}): {r.text.strip()}")

        # Jalankan fungsi blocking di threadpool agar tidak memblokir event loop asyncio
        uploaded_url = await asyncio.to_thread(upload_blocking, filePath)

        if uploaded_url and uploaded_url.startswith("http"):
            await message.edit(f"<blockquote>📤 Unggahan 0x0.st Berhasil!\nURL: {uploaded_url}</blockquote>", parse_mode="html")
        else:
            await message.edit(f"Unggahan gagal: Server tidak mengembalikan URL yang valid.\nRespons: `{uploaded_url}`")

    except Exception as e:
        await message.edit(f"Terjadi kesalahan saat mengunggah ke 0x0.st: `{type(e).__name__}: {e}`")
        
    finally:
        # Hapus file lokal di blok finally untuk pembersihan yang terjamin
        if filePath and os.path.exists(filePath):
            try:
                os.remove(filePath)
            except Exception as clean_e:
                # Menghindari kegagalan fatal karena masalah pembersihan
                print(f"Peringatan: Gagal menghapus file lokal: {clean_e}")
                pass
