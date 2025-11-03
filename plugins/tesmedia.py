# --- Bagian 1: Import yang Dibutuhkan ---
from telethon import events
from . import ultroid_cmd 
import os
import aiohttp # Wajib untuk request HTTP asinkron

# API Unduhan Anda
DOWNLOAD_API = "http://38.92.25.205:63123/api/download?url="
TEMP_DOWNLOAD_DIR = "downloads/" # Folder sementara

# Buat folder download jika belum ada
if not os.path.isdir(TEMP_DOWNLOAD_DIR):
    os.makedirs(TEMP_DOWNLOAD_DIR)

# --- Bagian 2: Fungsi Unduhan Media (.dld) yang Diperbaiki ---
@ultroid_cmd(pattern="dld (.*)")
async def download_media(event):
    """
    Mengunduh media (video/foto) dari URL yang diberikan menggunakan API eksternal.
    """
    if not event.fwd_from:
        initial_msg = await event.edit("⏳ **Memproses permintaan unduhan...**")
        
        try:
            media_url = event.pattern_match.group(1).strip()
            if not media_url:
                await initial_msg.edit("❌ **ERROR:** Mohon sertakan URL media (video/foto) yang valid setelah `.dld`")
                return
        except IndexError:
            await initial_msg.edit("❌ **ERROR:** Format salah. Gunakan: `.dld https://dictionary.cambridge.org/us/dictionary/english/media`")
            return

        full_api_url = DOWNLOAD_API + media_url
        temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, "downloaded_media")
        final_temp_path = None 

        try:
            await initial_msg.edit("🔗 **Mengirim permintaan ke API...** Menunggu respons file.")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(full_api_url) as resp:
                    if resp.status != 200:
                        await initial_msg.edit(f"❌ **ERROR API:** Gagal mendapatkan file. Status: `{resp.status}`")
                        return
                    
                    # 💡 PERBAIKAN UTAMA: Pengecekan Ukuran Konten (Minimal 5KB)
                    content_length = resp.headers.get("Content-Length")
                    if content_length and int(content_length) < 5120: 
                        error_text = await resp.text()
                        await initial_msg.edit(f"❌ **GAGAL MENGUNDUH (0.0 MB):** API tidak mengembalikan media yang valid.\n**Pesan API (jika ada):** `{error_text.strip()[:100]}...`")
                        return

                    # Penentuan ekstensi file
                    content_type = resp.headers.get("Content-Type", "application/octet-stream")
                    if "video" in content_type:
                        ext = ".mp4"
                    elif "image" in content_type:
                        ext = ".jpg"
                    else:
                        # Fallback yang lebih aman
                        ext = ".mp4" # Asumsi default media adalah MP4, atau .bin jika gagal
                        
                    final_temp_path = temp_file_path + ext
                    
                    # Tulis byte yang diterima ke file sementara
                    with open(final_temp_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
            
            # 2. Mengunggah File ke Telegram
            await initial_msg.edit("📤 **File berhasil diunduh.** Mengunggah ke Telegram...")
            
            file_size = os.path.getsize(final_temp_path)
            
            caption = (
                f"✅ **Berhasil Diunduh!**\n\n"
                f"**Sumber:** `{media_url}`\n"
                f"**Ukuran:** {round(file_size / (1024*1024), 2)} MB"
            )
            
            await event.client.send_file(
                event.chat_id,
                final_temp_path,
                caption=caption,
                force_document=False 
            )
            
            await initial_msg.delete()
            os.remove(final_temp_path)

        except Exception as e:
            if final_temp_path and os.path.exists(final_temp_path):
                os.remove(final_temp_path)
            
            await initial_msg.edit(f"❌ **ERROR:** Terjadi kesalahan dalam proses: `{str(e)}`")

# --- Bagian 3: Fungsi Info Bantuan (.mdlhelp) (TIDAK BERUBAH) ---
@ultroid_cmd(pattern="mdlhelp$")
async def media_help(event):
    if not event.fwd_from:
        help_text = (
            "🎥 **Modul Multifungsi Multimedia** 🖼️\n\n"
            "**Fungsi 1: Unduh Media**\n"
            "  • **Perintah:** `.dld <URL media>`\n"
            "  • **Contoh:** `.dld https://vt.tiktok.com/ZSySkQMsy/`\n"
            "  • **Kegunaan:** Mengunduh video/foto dari URL sosial media (TikTok, YouTube, IG, dll.) melalui API eksternal.\n\n"
            "**Fungsi 2: Bantuan Modul**\n"
            "  • **Perintah:** `.mdlhelp`\n"
            "  • **Kegunaan:** Menampilkan pesan bantuan ini."
        )
        await event.edit(help_text)

# --- Bagian 4: Informasi Modul (Wajib) ---
CMD_HELP = {
    "module": "Modul untuk unduh media dan bantuan.",
    "commands": {
        ".dld [URL]": "Mengunduh video/foto dari URL yang diberikan menggunakan API eksternal.",
        ".mdlhelp": "Menampilkan bantuan untuk modul ini."
    },
    "extra": "Menggunakan aiohttp untuk permintaan API. Pastikan Anda sudah menginstal 'aiohttp'."
}
