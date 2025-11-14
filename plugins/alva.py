"""
Plugin Name: Alive Checker
Description: Menampilkan status aktif bot (Alive) dengan gambar kustom dan info detail tercetak di gambar.
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

# --- FUNGSI FORMAT PESAN (TIDAK DIGUNAKAN LAGI UNTUK CAPTION, TAPI DATA UNTUK GAMBAR) ---
# Saya akan mengubah nama fungsi ini agar lebih jelas perannya sebagai pengumpul data
def get_alive_data(uptime):
    """
    Mengumpulkan data status alive dalam format yang siap dicetak ke gambar.
    """
    python_version = pyver() 
    
    # Mengembalikan list string, setiap item adalah baris teks
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
# Fungsi alive sekarang akan menerima 'alive_data' sebagai argumen
def alive(alive_data):
    """
    Membuat dan menyimpan gambar sederhana yang menunjukkan bahwa bot/aplikasi 'hidup' (alive),
    dengan detail teks tercetak di dalamnya.
    """
    ASSETS_DIR = "resources" 
    BACKGROUND_PATH = os.path.join(ASSETS_DIR, "bg2.jpg")
    FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")

    # 1. Buka background (dengan fallback)
    try:
        background = Image.open(BACKGROUND_PATH).convert("RGB")
    except FileNotFoundError:
        # Jika tidak ada bg2.jpg, buat latar belakang hijau gelap polos agar mirip dengan gambar contoh
        background = Image.new('RGB', (1000, 600), color=(30, 60, 30)) # Hijau gelap

    draw = ImageDraw.Draw(background)

    # 2. Tentukan Font (dengan fallback)
    try:
        title_font = ImageFont.truetype(FONT_PATH, size=80)
        info_font = ImageFont.truetype(FONT_PATH, size=40)
        detail_font = ImageFont.truetype(FONT_PATH, size=30) # Font lebih kecil untuk detail
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

    # --- Bagian A: Judul dan Last Checked (seperti sebelumnya) ---
    title_text = "BOT ALIVE" # Menyesuaikan agar tidak tumpang tindih dengan teks detail di bawah
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"LAST CHECKED: {current_time} WIB"

    W, H = background.size
    
    w_title, h_title = get_text_size(title_text, title_font)
    w_info, h_info = get_text_size(info_text, info_font)
    
    x_title = (W - w_title) / 2
    y_title = H / 4 # Posisikan lebih tinggi untuk memberi ruang
    x_info = (W - w_info) / 2
    y_info = y_title + h_title + 10 # Sedikit di bawah judul

    draw.text((x_title, y_title), title_text, fill=(255, 255, 255), font=title_font)
    draw.text((x_info, y_info), info_text, fill=(150, 255, 150), font=info_font)

    # --- Bagian B: Cetak Semua Detail Alive ke Dalam Gambar ---
    start_x_detail = 50 # Margin kiri
    start_y_detail = y_info + h_info + 60 # Mulai di bawah "Last Checked"
    line_height = get_text_size("A", detail_font)[1] + 10 # Tinggi baris + padding
    
    for i, line in enumerate(alive_data):
        current_y = start_y_detail + (i * line_height)
        # Menyesuaikan warna teks:
        if "xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ" in line or "xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ" in line:
            draw.text((start_x_detail, current_y), line, fill=(255, 255, 100), font=detail_font) # Kuning cerah
        else:
            draw.text((start_x_detail, current_y), line, fill=(200, 255, 200), font=detail_font) # Hijau muda

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
        # 1. Hitung Uptime
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
        
        # 2. Ambil data alive untuk gambar
        alive_data_list = get_alive_data(uptime_str) # Memanggil fungsi pengumpul data
        
        # 3. Buat Gambar (passing data ke fungsi alive())
        image_path = alive(alive_data_list) # Sekarang alive() menerima argumen

        # 4. Kirim Gambar (TANPA CAPTION TEKS LAGI)
        await ultroid_bot.send_file(
            event.chat_id,
            image_path,
            # caption="**Ultroid Userbot is ALIVE!**", # Caption ini bisa dihilangkan atau diubah
            # parse_mode='html', # Tidak perlu parse_mode jika tanpa caption HTML
            reply_to=event.reply_to_msg_id or event.id,
        )

        await msg.delete()

    except Exception as e:
        await ultroid_edit_or_reply(msg, f"**ERROR saat menjalankan alive:**\n`{str(e)}`")
    
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
    
