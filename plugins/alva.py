"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) pada gambar background (1280x720) 
             dengan kotak bersinar di sekitar teks, menggunakan font default PIL. Teks status bersih tanpa simbol.
"""
import os
from datetime import datetime
from PIL import ImageDraw, Image, ImageFont, ImageFilter
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
    Mengumpulkan data status alive dalam format yang siap dicetak ke gambar (Teks Inti tanpa simbol/pembingkai).
    """
    python_version = pyver() 
    
    return [
        "✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰",
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
    Membuat dan menyimpan gambar yang berisi teks status bot pada background kustom (1280x720) 
    dengan kotak bersinar di sekitar teks, menggunakan font default PIL.
    """
    ASSETS_DIR = "assets" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "IMG_20251115_011736_203.jpg")

    # 1. Buka Background (dengan fallback 1280x720)
    TARGET_SIZE = (1280, 720) 
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
        background = background.resize(TARGET_SIZE) 
    except FileNotFoundError:
        background = Image.new('RGB', TARGET_SIZE, color=(30, 60, 30)) 

    draw = ImageDraw.Draw(background)
    W, H = background.size 

    # 2. Tentukan Font (MENGGUNAKAN DEFAULT PIL)
    detail_font = ImageFont.load_default() 

    # Fungsi pembantu untuk mengukur teks (Perbaikan untuk Pillow modern)
    def get_text_size(text, font):
        try:
            # Cara modern (textbbox)
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            # Fallback (textsize)
            return draw.textsize(text, font=font) 

    # --- Hitung posisi dan ukuran blok teks ---
    start_x_detail = 150 # Margin kiri (geser ke kanan)

    total_text_height = 0
    line_heights = []
    text_widths = []

    for line in alive_data:
        w, h = get_text_size(line, detail_font)
        line_heights.append(h)
        text_widths.append(w)
        total_text_height += h + 10 

    max_text_width = max(text_widths) if text_widths else 0
    start_y_detail = (H - total_text_height) / 2
    
    # --- Koordinat untuk Kotak Bersinar ---
    padding_x = 30
    padding_y = 20

    box_left = start_x_detail - padding_x
    box_top = start_y_detail - padding_y
    box_right = start_x_detail + max_text_width + padding_x + 10 
    box_bottom = start_y_detail + total_text_height + padding_y

    box_left = max(0, box_left)
    box_top = max(0, box_top)
    box_right = min(W, box_right)
    box_bottom = min(H, box_bottom)
    
    # --- GAMBAR KOTAK BERSINAR ---
    
    glow_canvas = Image.new('RGBA', background.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_canvas)

    glow_color_outer = (100, 200, 255, 100) # Biru Muda Transparan
    main_color = (200, 240, 255, 255)       # Biru Sangat Terang (Inti)
    
    # Lapisan terluar (Glow)
    for i in range(3): 
        glow_draw.rectangle(
            (box_left - i*2, box_top - i*2, box_right + i*2, box_bottom + i*2),
            outline=glow_color_outer,
            width=2
        )
    
    # Lapisan inti
    glow_draw.rectangle(
        (box_left, box_top, box_right, box_bottom),
        outline=main_color,
        width=2
    )

    # Terapkan Blur
    glow_canvas = glow_canvas.filter(ImageFilter.GaussianBlur(radius=5)) 
    background.paste(glow_canvas, (0, 0), glow_canvas)

    # --- Cetak Teks Status Bot ---
    current_y = start_y_detail
    for i, line in enumerate(alive_data):
        draw.text((start_x_detail, current_y), line, fill=(255, 255, 255), font=detail_font) 
        current_y += line_heights[i] + 10 

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
    msg = await ultroid_edit_or_reply(event, "**`Processing alive image...`**")
    
    try:
        # 2. Hitung Uptime
        now = datetime.now()
        if isinstance(start_time, (int, float)):
            dt_start_time = datetime.fromtimestamp(start_time)
        else:
            dt_start_time = start_time
            
        diff = now - dt_start_time
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        uptime_str = f"{days}d, {hours}h, {minutes}m"
        
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
          
