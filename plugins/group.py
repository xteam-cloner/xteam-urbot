from telethon.tl.types import Channel, Chat, User
from . import ultroid_cmd, ultroid_bot 

client = ultroid_bot 
cmd = ultroid_cmd.command 

@client.on(cmd("totalgrup", channel=False, cmd_help={
    "help": "Menghitung total grup dan channel yang diikuti akun.",
    "example": "{cmd}"
}))
async def hitung_total_grup_plugin(event):
    await event.edit("🔄 Mulai menghitung semua dialog...")

    total_grup_kecil = 0
    total_supergroup = 0
    total_channel_broadcast = 0
    total_chat_pribadi = 0 
    
    async for dialog in event.client.iter_dialogs(): 
        entity = dialog.entity
        
        if isinstance(entity, User):
            total_chat_pribadi += 1
        elif isinstance(entity, Channel):
            if entity.megagroup:
                total_supergroup += 1
            elif entity.broadcast:
                total_channel_broadcast += 1
        elif isinstance(entity, Chat): 
            total_grup_kecil += 1
            
    total_grup_channel = total_grup_kecil + total_supergroup + total_channel_broadcast
    
    output = (
        "**📊 Hasil Total Entitas yang Diikuti**\n"
        "--------------------------------------------------\n"
        f"👤 Total Obrolan Pribadi (Users): `{total_chat_pribadi}`\n"
        #f"✅ Total Grup Kecil (Legacy Chat): `{total_grup_kecil}`\n"
        f"🚀 Total Group : `{total_grup_kecil + total_supergroup}`\n"
        f"📣 Total Channel : `{total_channel_broadcast}`\n"
        "--------------------------------------------------\n"
        f"✨ **TOTAL SELURUH GRUP/CHANNEL:** `{total_grup_channel}` entitas"
    )

    await event.edit(output)
  
