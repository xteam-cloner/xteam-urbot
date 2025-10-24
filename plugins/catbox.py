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
    uploaded_url = None
    
    try:
        # Tentukan folder unduhan sementara. Gunakan './' atau '/tmp/' 
        download_dir = "./" 
        
        # --- PERUBAHAN 1: Unduh file. Sekarang kita yakin filePath adalah string. ---
        # Telethon mengembalikan string jalur file ketika 'file' disetel.
        filePath = await reply_message.download_media(file=download_dir)

        if not isinstance(filePath, str) or not os.path.exists(filePath):
            # Ini adalah penanganan kegagalan jika download_media tidak mengembalikan path string
            # Walaupun jarang, ini untuk jaga-jaga.
            raise Exception("Gagal mendapatkan jalur file unduhan yang valid.")

        await message.edit("Mengunggah ke Litterbox.catbox.moe...")

        # --- PERUBAHAN UTAMA 2: Buka file secara eksplisit dan serahkan objek file ---
        # Kita menggunakan 'with open' untuk menjamin file dibuka ('rb' = read binary) 
        # selama proses upload dan ditutup secara otomatis setelahnya.
        with open(filePath, 'rb') as file_handle:
            # Pustaka catbox-uploader dapat menerima file handle (objek file)
            # Anda juga perlu menyediakan nama file di sini untuk unggahan multipart yang benar
            # Biasanya, argumen pertama upload_to_litterbox adalah file (path/handle).
            
            # Kita panggil dengan file_handle DAN nama file (dari filePath)
            # Beberapa library upload mengharapkan objek file, bukan path string.
            uploaded_url = cat_uploader.upload_to_litterbox(file_handle, time=expiry_time, filename=os.path.basename(filePath))


        if uploaded_url:
            await message.edit(f"<blockquote>📤 Unggahan Litterbox Berhasil!\nURL: {uploaded_url}\nKedaluwarsa: {expiry_time}</blockquote>", parse_mode="html")
        else:
            await message.edit("Unggahan gagal: Server tidak mengembalikan URL.")

    except Exception as e:
        await message.edit(f"Terjadi kesalahan saat mengunggah ke Litterbox: `{type(e).__name__}: {e}`")
        
    finally:
        # Hapus file lokal di blok finally untuk pembersihan yang terjamin
        if filePath and os.path.exists(filePath):
            try:
                os.remove(filePath)
            except Exception as clean_e:
                print(f"Peringatan: Gagal menghapus file lokal: {clean_e}")
                pass
