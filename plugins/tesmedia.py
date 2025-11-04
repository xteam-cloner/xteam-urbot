from telethon import events
# Pastikan impor ultroid_cmd dapat diakses di lingkungan Ultroid Anda
from . import ultroid_cmd 
import httpx, asyncio, os, tempfile, urllib.parse

# PERUBAHAN: Mengganti API sesuai permintaan pengguna.
# Diasumsikan endpoint downloader ada di root dan menerima URL dalam payload JSON.
API = "http://38.92.25.205:63123" 

@ultroid_cmd(pattern="dld ?(.*)")
async def run(message):
    """
    Mengunduh media (video dan/atau audio) dari URL yang diberikan menggunakan API eksternal.
    Gunakan: .dl <url> atau balas pesan yang berisi url.
    """
    
    # Ekstraksi URL dari argumen perintah atau pesan balasan
    url = message.pattern_match.group(1).strip()
    
    if not url:
        if message.reply_to_message and message.reply_to_message.text:
            url = message.reply_to_message.text.strip()
        else:
            # Menggunakan message.reply() untuk kompatibilitas framework Ultroid
            return await message.reply("Silakan berikan URL (`.dl <url>`) atau balas pesan yang berisi URL.")
    
    # Kirim pesan status awal
    # Menggunakan message.reply() untuk kompatibilitas framework Ultroid
    status_msg = await message.reply("⏳ Memproses permintaan ke API...")
    
    if not url:
        return await status_msg.edit("❌ Tidak ada URL ditemukan.")

    # Variabel encoded_url tidak lagi digunakan karena URL dikirim dalam payload JSON

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,id;q;0.8",
        "Connection": "keep-alive",
    }

    async with httpx.AsyncClient(timeout=90, headers=headers) as s:
        try:
            # PERUBAHAN: Mengirim URL di JSON payload dengan key "url".
            r = await s.post(API, json={"url": url}) 
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as e:
            return await message.reply(f"❌ **Kesalahan Server API** (Kode {e.response.status_code}): {e.request.url}")
        except Exception as e:
            return await message.reply(f"❌ **Kesalahan Koneksi**: {e}")

        if data.get("status") != "success":
            return await message.reply(f"❌ **Gagal dari API**: {data.get('msg', data)}")

        # Persiapkan Caption
        title = (data.get("title") or "Download").strip()
        uploader = data.get("uploader") or "-"
        duration = data.get("duration") or "-"
        caption = (
            f"**{title}**\n\n"
            f"**Uploader**: {uploader}\n"
            f"**Durasi**: {duration}\n\n"
            f"**Source URL**: `{url}`"
        )

        video_url = data.get("download_video_url")
        audio_url = data.get("download_audio_url")
        
        download_tasks = []

        async def download_and_send(url_file, is_audio=False):
            ext = ".mp3" if is_audio else ".mp4"
            file_type = "Audio" if is_audio else "Video"
            ftmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            try:
                await status_msg.edit(f"⬇️ Mendownload {file_type}...")
                
                # Streaming download
                # Catatan: URL download_video_url / download_audio_url diunduh menggunakan GET
                async with s.stream("GET", url_file) as resp: 
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes():
                        ftmp.write(chunk)
                ftmp.close()
                
                await status_msg.edit(f"⬆️ Mengunggah {file_type}...")
                
                # Kirim file 
                if is_audio:
                    await message.reply_audio(
                        ftmp.name, 
                        caption=caption, 
                        supports_streaming=True,
                        parse_mode='md'
                    )
                else:
                    await message.reply_video(
                        ftmp.name, 
                        caption=caption, 
                        supports_streaming=True,
                        parse_mode='md'
                    )
                
            except httpx.HTTPStatusError as e:
                await message.reply(f"❌ Gagal mendownload {file_type}. Error {e.response.status_code}")
            except Exception as e:
                await message.reply(f"❌ Error saat mendownload/mengunggah {file_type}: {e}")
            finally:
                # Bersihkan file sementara
                try:
                    os.remove(ftmp.name)
                except Exception as e:
                    print(f"Error removing temp file: {e}")

        # Tambahkan tugas pengunduhan
        if video_url:
            download_tasks.append(download_and_send(video_url, is_audio=False))
        # Hanya unduh audio jika ada dan berbeda dari video
        if audio_url and audio_url != video_url: 
            download_tasks.append(download_and_send(audio_url, is_audio=True))
        
        if not download_tasks:
            await status_msg.edit("❌ API tidak mengembalikan URL media yang valid.")

        # Jalankan semua tugas secara bersamaan
        if download_tasks:
            await asyncio.gather(*download_tasks)
        
        # Hapus pesan status jika semua berhasil
        try:
            await status_msg.delete()
        except:
            pass
