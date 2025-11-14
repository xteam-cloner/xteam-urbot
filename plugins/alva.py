"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) dengan gambar kustom dan info detail.
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
    start_time,     # Waktu bot pertama kali dijalankan (bisa float atau datetime)
    ultroid_bot,    # Objek bot/client (untuk dc_id dan send_file)
    eor as ultroid_edit_or_reply, # Alias untuk edit/reply
)
from pyrogram import __version__ as pver       # Versi Pyrogram (Kurigram)
from xteam.version import __version__ as xteam_lib_ver # Versi Library xteam/internal
from xteam.version import ultroid_version      # Versi Userbot

# --- FUNGSI FORMAT PESAN HTML ---

def format_message_text(uptime):
    """
    Memformat teks status alive dengan HTML, menggunakan variabel global.
    """
    python_version = pyver() 
    
    return f"<blockquote><b>✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰</b></blockquote>\n" \
                       f"✵ Owner : <a href='https://t.me/{OWNER_USERNAME}'>{OWNER_NAME}</a>\n" \
                       f"✵ Userbot : {ultroid_version}\n" \
                       f"✵ Dc Id : {ultroid_bot.dc_id}\n" \
                       f"✵ Library : {xteam_lib_ver}\n" \
                       f"✵ Uptime : {uptime}\n" \
                       f"✵ Kurigram :  {pver}\n" \
                       f"✵ Python : {python_version}\n" \
                       f"<blockquote>✵ <a href='https://t.me/xteam_cloner'>xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ</a> ✵</blockquote>\n"

# --- FUNGSI PEMBUAT GAMBAR ALIVE ---

def alive():
    """
    Membuat dan menyimpan gambar sederhana yang menunjukkan bahwa bot/aplikasi 'hidup' (alive).
    """
    ASSETS_DIR = "resources" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "bg2.jpg")
    FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")

    # 1. Buka background (dengan fallback)
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
    except FileNotFoundError:
        background = Image.new('RGB', (1000, 600), color=(30, 30, 30))

    draw = ImageDraw.Draw(background)

    # 2. Tentukan Font (dengan fallback)
    try:
        title_font = ImageFont.truetype(FONT_PATH, size=80)
        info_font = ImageFont.truetype(FONT_PATH, size=40)
    except FileNotFoundError:
        title_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    # 3. Teks dan Posisi
    title_text = "🤖 BOT ALIVE 🟢"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"Last Checked: {current_time} WIB"

    W, H = background.size
    
    def get_text_size(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textsize(text, font=font)

    w_title, h_title = get_text_size(title_text, title_font)
    w_info, _ = get_text_size(info_text, info_font)
    
    x_title = (W - w_title) / 2
    y_title = H / 3
    x_info = (W - w_info) / 2
    y_info = y_title + h_title + 30 

    # 4. Gambar Teks
    draw.text((x_title, y_title), title_text, fill=(255, 255, 255), font=title_font)
    draw.text((x_info, y_info), info_text, fill=(150, 255, 150), font=info_font)

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
    msg = await ultroid_edit_or_reply(event, "**`Processing alive image and status...`**")
    
    try:
        # 2. Buat Gambar
        image_path = alive()
        
        # 3. Hitung Uptime
        now = datetime.now()
        
        # PERBAIKAN: Mengatasi error float vs datetime
        if isinstance(start_time, (int, float)):
            dt_start_time = datetime.fromtimestamp(start_time)
        else:
            dt_start_time = start_time
            
        diff = now - dt_start_time
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        uptime_str = f"{days} hari, {hours} jam, {minutes} menit"
        
        # 4. Format Caption Teks
        caption_text = format_message_text(uptime_str)
        
        # 5. Kirim Gambar dan Teks
        await ultroid_bot.send_file(
            event.chat_id,
            image_path,
            caption=caption_text,
            parse_mode='html',   
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
            
