"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) dengan gambar kustom (1280x720) dan detail tercetak di gambar.
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
    Mengumpulkan data status alive dalam format yang siap dicetak ke gambar.
    """
    python_version = pyver() 
    
    return [
        "✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰",
        f"✵ Owner : {OWNER_NAME}",
        f"✵ Userbot : {ultroid_version}",
        f"✵ Dc Id : {ultroid_bot.dc_id}",
        f"✵ Library : {xteam_lib_ver}",
        f"✵ Uptime : {uptime}",
        f"✵ Kurigram :  {pver}",
        f"✵ Python : {python_version}",
        "✵ xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ ✵"
    ]

# --- FUNGSI PEMBUAT GAMBAR ALIVE ---

def alive(alive_data):
    """
    Membuat dan menyimpan gambar sederhana yang menunjukkan bahwa bot/aplikasi 'hidup' (alive),
    dengan detail teks tercetak di dalamnya, menggunakan dimensi 1280x720.
    """
    ASSETS_DIR = "resources" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "bg2.jpg")
    FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")

    # 1. Buka background (dengan fallback 1280x720)
    TARGET_SIZE = (1280, 720) 
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
        # Opsional: Jika bg2.jpg tidak 1280x720, resize agar konsisten
        # background = background.resize(TARGET_SIZE) 
    except FileNotFoundError:
        background = Image.new('RGB', TARGET_SIZE, color=(30, 60, 30)) 

    draw = ImageDraw.Draw(background)
    W, H = background.size 

    # 2. Tentukan Font (disesuaikan untuk 1280x720)
    try:
        title_font = ImageFont.truetype(FONT_PATH, size=90) 
        info_font = ImageFont.truetype(FONT_PATH, size=45) 
        detail_font = ImageFont.truetype(FONT_PATH, size=35)
    except FileNotFoundError:
        title_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()

    # Fungsi pembantu untuk mengukur teks
    def get_text_size(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textsize(text, font=font)


    # --- Bagian A: Judul dan Last Checked (Pusat Atas) ---
    title_text = "BOT ALIVE" 
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"LAST CHECKED: {current_time} WIB"

    w_title, h_title = get_text_size(title_text, title_font)
    w_info, h_info = get_text_size(info_text, info_font)
    
    # Penempatan Judul
    x_title = (W - w_title) / 2
    y_title = H / 4 
    x_info = (W - w_info) / 2
    y_info = y_title + h_title + 15

    draw.text((x_title, y_title), title_text, fill=(255, 255, 255), font=title_font)
    draw.text((x_info, y_info), info_text, fill=(150, 255, 150), font=info_font)

    # --- Bagian B: Cetak Semua Detail Alive ke Dalam Gambar (Margin Kiri) ---
    start_x_detail = 100 
    start_y_detail = H / 2 + 50 
    line_height = get_text_size("A", detail_font)[1] + 15 
    
    for i, line in enumerate(alive_data):
        current_y = start_y_detail + (i * line_height)
        
        # Penyesuaian Warna Teks
        if "xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ" in line or "xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ" in line:
            draw.text((start_x_detail, current_y), line, fill=(255, 255, 100), font=detail_font) 
        else:
            draw.text((start_x_detail, current_y), line, fill=(200, 255, 200), font=detail_font)

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
    Handler untuk perintah .alive
    """
    # 1. Feedback awal
    msg = await ultroid_edit_or_reply(event, "**`Processing alive image...`**")
    
    try:
        # 2. Hitung Uptime (dengan perbaikan float/datetime)
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
        
        # 3. Ambil data alive untuk gambar
        alive_data_list = get_alive_data(uptime_str)
        
        # 4. Buat Gambar
        image_path = alive(alive_data_list)
        
        # 5. Kirim Gambar (Tanpa Caption Teks Detail)
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
    
