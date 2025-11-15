"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) pada gambar background (1280x720) menggunakan font default PIL.
"""
import os
from datetime import datetime
from PIL import ImageDraw, Image, ImageFont
from platform import python_version as pyver

# --- IMPORTS DARI INTI ULTROID ---
from . import ultroid_cmd
from . import (
    OWNER_NAME,
    OWNER_USERNAME,
    start_time,     
    ultroid_bot,    
    eor as ultroid_edit_or_reply, 
)
from pyrogram import __version__ as pver       
from xteam.version import __version__ as xteam_lib_ver 
from xteam.version import ultroid_version      

# --- FUNGSI FORMAT PESAN (PENGUMPUL DATA) ---

def get_alive_data(uptime):
    """
    Mengumpulkan data status alive dalam format yang siap dicetak ke gambar (Teks Inti tanpa simbol).
    """
    python_version = pyver() 
    
    return [
        "XTEAM URBOT IS ALIVE",
        f"Owner : {OWNER_NAME}",
        f"Userbot : {ultroid_version}",
        f"Dc Id : {ultroid_bot.dc_id}",
        f"Library : {xteam_lib_ver}",
        f"Uptime : {uptime}",
        f"Kurigram : {pver}",
        f"Python : {python_version}",
        "XTEAM CLONER"
    ]

# --- FUNGSI PEMBUAT GAMBAR ALIVE ---

def alive(alive_data):
    """
    Membuat dan menyimpan gambar yang berisi teks status bot pada background kustom (1280x720) 
    menggunakan font default PIL.
    """
    ASSETS_DIR = "resources" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "IMG_20251115_011736_203.jpg")
    
    # 1. Buka Background (dengan fallback 1280x720)
    TARGET_SIZE = (1280, 720) 
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
        background = background.resize(TARGET_SIZE) 
    except FileNotFoundError:
        # Fallback jika gambar background tidak ditemukan
        background = Image.new('RGB', TARGET_SIZE, color=(30, 60, 30)) 

    draw = ImageDraw.Draw(background)
    W, H = background.size 

    # 2. Tentukan Font (MENGGUNAKAN DEFAULT PIL)
    detail_font = ImageFont.load_default() 

    # Fungsi pembantu untuk mengukur teks (FIX: Menggunakan draw.textbbox untuk Pillow terbaru)
    def get_text_size(text, font):
        # textbbox mengembalikan (x_min, y_min, x_max, y_max)
        # Posisi awal (0, 0) hanya digunakan untuk perhitungan ukuran
        bbox = draw.textbbox((0, 0), text, font=font)
        # Lebar = x_max - x_min; Tinggi = y_max - y_min
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    # --- Cetak Semua Detail Alive ke Dalam Gambar ---
    start_x_detail = 150 # Margin kiri

    total_text_height = 0
    line_heights = []
    
    # Hitung total tinggi teks
    for line in alive_data:
        w, h = get_text_size(line, detail_font)
        line_heights.append(h)
        total_text_height += h + 10 # Padding 10px

    # Hitung posisi Y awal agar teks berada di tengah vertikal
    start_y_detail = (H - total_text_height) / 2
    
    current_y = start_y_detail
    for i, line in enumerate(alive_data):
        # Warna Teks diatur Putih
        draw.text((start_x_detail, current_y), line, fill=(255, 255, 255), font=detail_font) 

        current_y += line_heights[i] + 10 # Pindah ke baris berikutnya

    # 5. Simpan Gambar
    OUTPUT_DIR = "downloads"
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, "alive.png")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    background.save(OUTPUT_PATH)

    return OUTPUT_PATH

# --- HANDLER ULTROID ---

@ultroid_cmd(pattern="alva$") 
async def alive_handler(event):
    """
    Handler untuk perintah .alva
    """
    msg = await ultroid_edit_or_reply(event, "**`Processing alive image...`**")
    
    try:
        # 2. Hitung Uptime
        now = datetime.now()
        if isinstance(start_time, (int, float)):
            # Perbaikan float/datetime
            dt_start_time = datetime.fromtimestamp(start_time)
        else:
            dt_start_time = start_time
            
        diff = now - dt_start_time
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        uptime_str = f"{days} hari, {hours} jam, {minutes} menit"
        
        # 3. Ambil data alive untuk gambar
        alive_data_list = get_alive_data(uptime_str)
        
        # 4. Buat Gambar
        image_path = alive(alive_data_list)
        
        # 5. Kirim Gambar
        await ultroid_bot.send_file(
            event.chat_id,
            image_path,
            reply_to=event.reply_to_msg_id or event.id,
        )

        # 6. Hapus pesan processing
        await msg.delete()

    except Exception as e:
        await ultroid_edit_or_reply(msg, f"**ERROR saat menjalankan alive:**\n`{str(e)}`")
    
    finally:
        # 7. Hapus file gambar
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
    
