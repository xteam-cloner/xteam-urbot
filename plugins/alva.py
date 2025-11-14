"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) pada gambar background (1280x720),
             dengan detail teks tercetak di gambar (tanpa simbol pembingkai, tanpa "BOT ALIVE" / "LAST CHECKED").
"""
import os
from datetime import datetime
from PIL import ImageDraw, Image, ImageFont
from platform import python_version as pyver

# --- IMPORTS DARI INTI ULTROID (tetap sama) ---
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
# Tetap sama, menghasilkan teks tanpa simbol
def get_alive_data(uptime):
    """
    Mengumpulkan data status alive dalam format yang siap dicetak ke gambar (Hanya Teks Inti).
    """
    python_version = pyver() 
    
    return [
        "✵ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✵",
        f"Owner : {OWNER_NAME}",
        f"Userbot : {ultroid_version}",
        f"Dc Id : {ultroid_bot.dc_id}",
        f"Library : {xteam_lib_ver}",
        f"Uptime : {uptime}",
        f"Kurigram : {pver}",
        f"Python : {python_version}",
        "✵ xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ ✵"
    ]

# --- FUNGSI PEMBUAT GAMBAR ALIVE ---

def alive(alive_data):
    """
    Membuat dan menyimpan gambar sederhana yang berisi teks status bot pada background kustom (1280x720).
    """
    ASSETS_DIR = "resources" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "bg2.jpg")
    FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")

    # 1. Buka Background (dengan fallback 1280x720)
    TARGET_SIZE = (1280, 720) 
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
        # Opsional: Resize background jika ukurannya tidak sesuai TARGET_SIZE
        background = background.resize(TARGET_SIZE) 
    except FileNotFoundError:
        # Fallback jika bg2.jpg tidak ditemukan
        background = Image.new('RGB', TARGET_SIZE, color=(30, 60, 30)) # Kembali ke warna hijau gelap default

    draw = ImageDraw.Draw(background)
    W, H = background.size 

    # 2. Tentukan Font
    try:
        detail_font = ImageFont.truetype(FONT_PATH, size=40) 
    except FileNotFoundError:
        detail_font = ImageFont.load_default()

    # Fungsi pembantu untuk mengukur teks
    def get_text_size(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textsize(text, font=font)

    # --- Cetak Semua Detail Alive ke Dalam Gambar ---
    start_x_detail = 100 # Margin kiri

    total_text_height = 0
    line_heights = []
    
    # Hitung total tinggi teks
    for line in alive_data:
        _, h = get_text_size(line, detail_font)
        line_heights.append(h)
        total_text_height += h + 15 # Tambahkan padding antar baris

    # Hitung posisi Y awal agar teks berada di tengah vertikal
    # dan sedikit ke atas/kiri agar tidak terganggu elemen background
    start_y_detail = (H - total_text_height) / 2 # Tengah vertikal
    
    current_y = start_y_detail
    for i, line in enumerate(alive_data):
        # Warna Teks diatur Putih (255, 255, 255)
        draw.text((start_x_detail, current_y), line, fill=(255, 255, 255), font=detail_font) 

        current_y += line_heights[i] + 15 # Pindah ke baris berikutnya + padding

    # 5. Simpan Gambar
    OUTPUT_DIR = "downloads"
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, "alive.png")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    background.save(OUTPUT_PATH)

    return OUTPUT_PATH

# --- HANDLER ULTROID (Tidak ada perubahan) ---

@ultroid_cmd(pattern="alva$") 
async def alive_handler(event):
    """
    Handler untuk perintah .alive
    """
    msg = await ultroid_edit_or_reply(event, "**`Processing alive image...`**")
    
    try:
        now = datetime.now()
        if isinstance(start_time, (int, float)):
            dt_start_time = datetime.fromtimestamp(start_time)
        else:
            dt_start_time = start_time
            
        diff = now - dt_start_time
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        uptime_str = f"{days} hari, {hours} jam, {minutes} menit"
        
        alive_data_list = get_alive_data(uptime_str)
        image_path = alive(alive_data_list)
        
        await ultroid_bot.send_file(
            event.chat_id,
            image_path,
            reply_to=event.reply_to_msg_id or event.id,
        )

        await msg.delete()

    except Exception as e:
        await ultroid_edit_or_reply(msg, f"**ERROR saat menjalankan alive:**\n`{str(e)}`")
    
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
    
