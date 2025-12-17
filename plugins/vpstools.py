import os
import shutil
import psutil
from datetime import datetime

# Import decorator dan fungsi helper dari Ultroid
from . import ultroid_cmd, get_string

@ultroid_cmd(pattern="clean$")
async def clean_vps(event):
    if not event.out:
        return await event.edit("`Hanya admin yang bisa menjalankan ini!`")

    msg = await event.edit("🧹 **Memulai pembersihan VPS...**")
    
    try:
        # 1. Membersihkan RAM Cache (PageCache, dentries, dan inodes)
        os.system("sync && echo 3 > /proc/sys/vm/drop_caches")
        
        # 2. Membersihkan Cache Pip (Python)
        os.system("pip cache purge")
        
        # 3. Membersihkan APT Cache (Debian/Ubuntu)
        os.system("apt-get autoclean -y && apt-get autoremove -y")
        
        await msg.edit(
            "✅ **Pembersihan Selesai!**\n\n"
            "• **RAM Cache:** Dibersihkan\n"
            "• **Pip Cache:** Dihapus\n"
            "• **APT System:** Autoclean & Autoremove sukses"
        )
    except Exception as e:
        await msg.edit(f"❌ **Gagal membersihkan:**\n`{str(e)}` \n\nPastikan bot berjalan dengan akses root.")

@ultroid_cmd(pattern="Sysinfo$")
async def sys_info(event):
    # Mengambil info RAM
    ram = psutil.virtual_memory()
    # Mengambil info Disk
    disk = shutil.disk_usage("/")
    # Mengambil Uptime Server sederhana
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_hours = int(uptime_seconds // 3600)
    
    info = (
        "🖥 **Status Server VPS**\n\n"
        f"📊 **RAM:** `{ram.percent}%` (Used: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n"
        f"💽 **Disk:** `{disk.used // (1024**3)}GB` / `{disk.total // (1024**3)}GB`\n"
        f"⏳ **Uptime:** `{uptime_hours} Jam`\n"
        f"🕒 **Waktu:** `{datetime.now().strftime('%H:%M:%S')}`"
    )
    await event.edit(info)
  
