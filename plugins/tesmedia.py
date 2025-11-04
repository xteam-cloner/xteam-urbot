from telethon import events
# Pastikan impor ultroid_cmd dapat diakses di lingkungan Ultroid Anda
from . import ultroid_cmd 
import httpx, asyncio, os, tempfile, urllib.parse

from . import (
    ultroid_cmd as xteam_cmd,
    asst,
    eor,
)
import httpx
from urllib.parse import quote_plus

# --- Konfigurasi ---
DOWNLOAD_API = "http://38.92.25.205:63123/api/download?url={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Connection": "keep-alive",
}
# --------------------

@xteam_cmd(pattern="d(?:ld|d) ?(.*)$")
async def downloader(event):
    """
    Menggunakan API kustom untuk mengunduh konten dari URL yang diberikan.
    Sintaks: .dl <url> atau .download <url>
    """
    
    # Ambil URL dari argumen
    url_to_download = event.pattern_match.group(1).strip()

    if not url_to_download:
        await eor(
            event,
            "**❌ Kesalahan:** Mohon berikan URL yang ingin diunduh.\n"
            "**Contoh:** `.dl https://contoh.com/file.mp4`"
        )
        return

    # Kirim pesan tunggu (Loading/Processing)
    msg = await eor(event, "**⏳ Memproses URL...**")

    try:
        # Encode URL agar aman dimasukkan ke dalam query parameter
        encoded_url = quote_plus(url_to_download)
        
        # Buat URL lengkap untuk API
        api_url = DOWNLOAD_API.format(encoded_url)

        # Gunakan httpx untuk melakukan request
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=HEADERS, timeout=60) 
            # Timeout diatur 60 detik (bisa disesuaikan)

        # Cek status kode
        if response.status_code != 200:
            await asst.send_message(
                event.chat_id,
                f"**⚠️ API Mengembalikan Kesalahan:** Status **{response.status_code}**\n"
                f"URL API: `{api_url}`"
            )
            await msg.delete()
            return

        # Cek tipe konten yang dikembalikan (asumsi API mengembalikan file/data mentah)
        # Jika API mengembalikan file/media mentah (binary), coba kirimkan langsung
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type.lower():
            # Jika response adalah JSON (mungkin API error atau memberikan link unduhan)
            data = response.json()
            await asst.send_message(
                event.chat_id,
                "**ℹ️ API Mengembalikan JSON.**\n"
                f"```json\n{data}```\n"
                "Mungkin API tidak mengembalikan file secara langsung."
            )
        else:
            # Asumsi ini adalah file/media yang siap diunggah
            
            # Mendapatkan nama file, jika ada di header (Content-Disposition)
            # Fallback ke nama default
            filename = url_to_download.split('/')[-1] or "downloaded_file"
            
            # Kirim file sebagai bytes
            await asst.send_file(
                event.chat_id,
                file=response.content,
                caption=f"**✅ Berhasil Diunduh!**\n"
                        f"**Sumber:** `{url_to_download}`",
                file_name=filename,
                force_document=True # Kirim sebagai dokumen untuk menghindari kompresi
            )

        # Hapus pesan tunggu
        await msg.delete()

    except httpx.TimeoutException:
        await eor(event, "**🚨 Kesalahan:** Permintaan ke API melebihi batas waktu (Timeout).")
    except httpx.RequestError as e:
        await eor(event, f"**❌ Kesalahan Request:** Gagal terhubung ke API.\nDetail: `{str(e)}`")
    except Exception as e:
        await eor(event, f"**🛑 Kesalahan Tak Terduga:** Terjadi kesalahan saat memproses unduhan.\nDetail: `{str(e)}`")
