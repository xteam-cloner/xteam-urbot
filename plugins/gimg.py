from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from . import (
    ultroid_cmd as xteam_cmd,
    eor,
    udB,  # Import udB untuk mengakses database Ultroid
)
import os

# Fungsi untuk mendapatkan kunci API
def get_gemini_key():
    """Mengambil GEMINI_API_KEY dari database Ultroid."""
    # Pastikan kunci ini sudah Anda simpan di udB, misalnya:
    # .setkey GEMINI_API_KEY YOUR_API_KEY_DI_SINI
    return udB.get_key("GEMINI_API_KEY")

@xteam_cmd(pattern="gimg(?: |$)(.*)")
async def generate_gemini_image(event):
    """
    Menghasilkan gambar menggunakan Gemini API berdasarkan prompt.
    Penggunaan: .gimg [prompt]
    """
    
    # 1. Ambil Kunci API dan Inisialisasi Klien
    api_key = get_gemini_key()
    
    if not api_key:
        await eor(event, "**❌ Kesalahan Konfigurasi:** Kunci API Gemini tidak ditemukan.\nSilakan atur kunci Anda menggunakan perintah: `.setkey GEMINI_API_KEY <YOUR_API_KEY>`")
        return
        
    client = genai.Client(api_key=api_key)
    
    # 2. Ambil prompt dari argumen perintah
    prompt = event.pattern_match.group(1).strip()
    
    # Prompt default/penyempurnaan
    if not prompt:
        prompt = "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
    else:
        # Menambahkan detail untuk hasil yang lebih baik
        prompt = f"{prompt}, professional photo, highly detailed, photorealistic"
    
    # 3. Kirim pesan tunggu
    message = await eor(event, "**🌀 Sedang membuat gambar untuk prompt:**\n`" + prompt + "`")
    
    try:
        # 4. Panggil Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )

        # 5. Ambil data gambar dan simpan
        # Diasumsikan hanya ada satu kandidat dan satu bagian inline_data
        
        # Cek apakah ada inline_data (gambar)
        image_part = next((part for part in response.candidates[0].content.parts if part.inline_data), None)

        if image_part:
            image_data = image_part.inline_data.data
            
            # Ubah data biner menjadi objek PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Tentukan nama file sementara
            file_name = "generated_gemini_image.png"
            image.save(file_name, "PNG")

            # 6. Kirim gambar ke Telegram
            await event.client.send_file(
                event.chat_id,
                file_name,
                caption=f"**🖼️ Gambar dibuat oleh Gemini**\n**Prompt:** `{prompt}`",
                reply_to=event.reply_to_msg_id or event.id
            )
            
            # 7. Hapus pesan tunggu dan file sementara
            await message.delete()
            os.remove(file_name)

        else:
            # Jika tidak ada gambar (kemungkinan diblokir oleh safety filter)
            text_output = "".join(part.text for part in response.candidates[0].content.parts if part.text)
            await message.edit(f"**❌ Gagal membuat gambar. Output mungkin diblokir.**\n**Output Teks:** `{text_output}`")

    except Exception as e:
        await message.edit(f"**❌ Terjadi kesalahan saat memanggil Gemini API:**\n`{type(e).__name__}: {e}`")
        
